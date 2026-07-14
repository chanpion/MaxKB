"""Ingestion pipeline: parse -> split -> embed -> store.

Replicates the legacy ``knowledge`` flow (serializer ``Create.save`` /
``embedding_by_document``) against the EXISTING ``document`` / ``paragraph`` /
``embedding`` tables so the new FastAPI service can share data with Django.

  * Document + Paragraph rows are written via the SQLModel async session.
  * Embedding rows use raw asyncpg SQL (pgvector ``::vector`` cast + the
    ``to_tsvector`` search column) — identical to ``PgVectorRetriever`` usage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID as _UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import engine
from app.models.base import uuid7
from app.models.knowledge import Document, Paragraph
from app.rag.embed import (
    chunk_text,
    embed_texts,
    normalize_for_embedding,
    sub_array,
)
from app.rag.parsers import ParsedDocument, parse_file
from app.rag.splitter import split_text

# SourceType.PARAGRAPH in the legacy Django enum (single-char codes: 0 problem, 1 paragraph, 2 title).
_SOURCE_TYPE_PARAGRAPH = "1"

_SQL_INSERT_EMBEDDING = text(
    """
    INSERT INTO embedding
        (id, source_id, source_type, is_active, knowledge_id, document_id, paragraph_id, embedding, search_vector, meta)
    VALUES
        (:id, :source_id, :source_type, :is_active, :knowledge_id, :document_id, :paragraph_id,
         CAST(:embedding AS vector), to_tsvector('simple', :search_text), CAST(:meta AS jsonb))
    """
)


@dataclass
class IngestionResult:
    document_id: str
    paragraph_count: int
    embedding_count: int
    char_length: int


async def ingest_document(
    session: AsyncSession,
    *,
    knowledge_id: str,
    document_id: str,
    user_id: str | None,
    filename: str,
    content: bytes,
    embedding: dict[str, Any],
    with_filter: bool = False,
    limit: int = 4096,
    source_file_id: str | None = None,
    meta: dict[str, Any] | None = None,
    doc_type: int = 0,
) -> IngestionResult:
    """Parse ``content``, split, embed and persist it under one ``document``.

    ``embedding`` must carry ``provider``, ``model_name``, ``credential`` and
    optionally ``dimensions`` (defaults to 1536 to match the ``embedding`` column).
    """
    parsed: list[ParsedDocument] = parse_file(filename, content)

    paragraphs_data: list[dict[str, str]] = []
    for pd in parsed:
        paragraphs_data.extend(
            split_text(pd.content, filename=pd.name or filename, with_filter=with_filter, limit=limit)
        )

    # ---- Document row -------------------------------------------------------
    doc_meta = dict(meta or {})
    if source_file_id is not None:
        doc_meta["source_file_id"] = source_file_id
    doc_meta["allow_download"] = True

    char_length = sum(len(p.get("content", "")) for p in paragraphs_data)
    # Upsert: the upload endpoint may have pre-created the Document row, so we
    # update it in place instead of INSERT-ing a duplicate primary key.
    document = await session.get(Document, _UUID(document_id))
    if document is None:
        document = Document(
            id=_UUID(document_id),
            knowledge_id=knowledge_id,
            name=filename[0:128],
            char_length=char_length,
            user_id=user_id,
            type=doc_type,
            meta=doc_meta,
        )
        session.add(document)
    else:
        document.name = filename[0:128]
        document.char_length = char_length
        document.user_id = document.user_id or user_id
        document.type = doc_type
        document.meta = doc_meta

    # ---- Paragraph rows -----------------------------------------------------
    paragraph_objs: list[Paragraph] = []
    for idx, p in enumerate(paragraphs_data):
        para = Paragraph(
            knowledge_id=knowledge_id,
            document_id=document_id,
            content=p.get("content", ""),
            title=(p.get("title") or "")[0:256],
            position=idx + 1,
            is_active=True,
        )
        paragraph_objs.append(para)
        session.add(para)

    await session.flush()

    result = await _embed_paragraphs(
        session,
        knowledge_id=knowledge_id,
        document_id=document_id,
        paragraph_objs=paragraph_objs,
        embedding=embedding,
    )
    return result


async def _embed_paragraphs(
    session: AsyncSession,
    *,
    knowledge_id: str | _UUID,
    document_id: str | _UUID,
    paragraph_objs: list[Paragraph],
    embedding: dict[str, Any],
) -> IngestionResult:
    """Embed a set of already-persisted ``Paragraph`` rows and write ``embedding`` rows.

    Shared by :func:`ingest_document` (paragraphs freshly created from raw
    content) and :func:`embed_paragraphs` (paragraphs created upstream, e.g. by
    the ``batch_create`` API from pre-split frontend data). The paragraph rows
    are assumed to already exist in the database; this only computes chunk
    embeddings and inserts them, then returns counts for status bookkeeping.
    """
    embedding_count = 0
    provider = embedding["provider"]
    model_name = embedding["model_name"]
    credential = embedding.get("credential", {})
    dimensions = embedding.get("dimensions")

    # Gather (paragraph, chunk_texts) pairs.
    chunk_plan: list[tuple[Paragraph, list[str]]] = []
    for para in paragraph_objs:
        texts = chunk_text(para.content, chunk_size=256)
        para.chunks = texts  # mirror legacy Paragraph.chunks
        chunk_plan.append((para, texts))

    # Flatten into one text list, keep mapping back to paragraph.
    flat_texts: list[str] = []
    owner: list[Paragraph] = []
    for para, texts in chunk_plan:
        for t in texts:
            flat_texts.append(t)
            owner.append(para)

    if flat_texts:
        normalized = [normalize_for_embedding(t) for t in flat_texts]
        vectors = await embed_texts(provider, model_name, credential, normalized, dimensions=dimensions)

        async with engine.connect() as conn:
            for batch in sub_array(list(range(len(flat_texts))), item_num=10):
                for i in batch:
                    para = owner[i]
                    emb_id = str(uuid7())
                    await conn.execute(
                        _SQL_INSERT_EMBEDDING,
                        {
                            "id": emb_id,
                            "source_id": str(para.id),
                            "source_type": _SOURCE_TYPE_PARAGRAPH,
                            "is_active": True,
                            "knowledge_id": str(knowledge_id),
                            "document_id": str(document_id),
                            "paragraph_id": str(para.id),
                            "embedding": "[" + ",".join(str(float(x)) for x in vectors[i]) + "]",
                            "search_text": flat_texts[i],
                            "meta": "{}",
                        },
                    )
                    embedding_count += 1
            await conn.commit()

    # Persist the (now chunked) paragraph rows and the document.
    char_length = sum(len(para.content) for para in paragraph_objs)
    await session.commit()
    return IngestionResult(
        document_id=str(document_id),
        paragraph_count=len(paragraph_objs),
        embedding_count=embedding_count,
        char_length=char_length,
    )


async def embed_paragraphs(
    session: AsyncSession,
    *,
    knowledge_id: str | _UUID,
    document_id: str | _UUID,
    embedding: dict[str, Any],
) -> IngestionResult:
    """Embed already-persisted ``Paragraph`` rows of a document.

    Unlike :func:`ingest_document`, this does NOT parse or split content — the
    ``Paragraph`` rows are assumed to already exist (e.g. created by the
    ``batch_create`` API from pre-split frontend data). It only computes
    embeddings and writes ``embedding`` rows, then returns counts.
    """
    from sqlalchemy import select

    rows = await session.execute(
        select(Paragraph).where(Paragraph.document_id == _UUID(document_id)).order_by(Paragraph.position)
    )
    paragraph_objs = list(rows.scalars().all())
    if not paragraph_objs:
        return IngestionResult(
            document_id=str(document_id),
            paragraph_count=0,
            embedding_count=0,
            char_length=0,
        )
    return await _embed_paragraphs(
        session,
        knowledge_id=knowledge_id,
        document_id=document_id,
        paragraph_objs=paragraph_objs,
        embedding=embedding,
    )
