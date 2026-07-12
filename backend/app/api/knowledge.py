"""Knowledge-base CRUD API — KB, document, paragraph, hit test, embedding trigger."""

from __future__ import annotations

import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user
from app.models.knowledge import Document, DocumentTag, Knowledge, KnowledgeFolder, Paragraph, Tag
from app.models.models_provider import Model
from app.models.user import User
from app.schemas.knowledge import (
    DocumentCreate,
    DocumentOut,
    DocumentPage,
    DocumentUpdate,
    HitTestRequest,
    HitTestResponse,
    HitTestResult,
    KnowledgeCreate,
    KnowledgeOut,
    KnowledgePage,
    KnowledgeUpdate,
    ParagraphOut,
    ParagraphPage,
    TagCreate,
    TagOut,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


# ---------------------------------------------------------------------------
# Knowledge base CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=KnowledgePage)
async def list_knowledge(
    page: int = 1,
    size: int = 10,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> KnowledgePage:
    total = await session.scalar(select(func.count()).select_from(Knowledge))
    result = await session.execute(
        select(Knowledge).order_by(Knowledge.create_time.desc()).offset((page - 1) * size).limit(size)
    )
    rows = result.scalars().all()
    return KnowledgePage(records=[KnowledgeOut.model_validate(k) for k in rows], total=total or 0)


@router.post("", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
async def create_knowledge(
    body: KnowledgeCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> KnowledgeOut:
    return await _create_knowledge(body, session, current_user)


async def _create_knowledge(
    body: KnowledgeCreate,
    session: AsyncSession,
    current_user: User,
) -> KnowledgeOut:
    knowledge = Knowledge(
        name=body.name,
        desc=body.desc,
        type=body.type,
        scope=body.scope,
        embedding_model_id=uuid_module.UUID(body.embedding_model_id) if body.embedding_model_id else None,
        folder_id=body.folder_id,
        workspace_id=body.workspace_id,
        user_id=current_user.id,
        meta=body.meta,
    )
    session.add(knowledge)
    await session.commit()
    await session.refresh(knowledge)
    return KnowledgeOut.model_validate(knowledge)


# ---------------------------------------------------------------------------
# Knowledge folders (MUST come before /{knowledge_id} to avoid route conflict)
# ---------------------------------------------------------------------------


@router.get("/folder", response_model=list[dict])
async def list_knowledge_folders(
    workspace_id: str = "default",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[dict]:
    result = await session.execute(
        select(KnowledgeFolder).where(KnowledgeFolder.workspace_id == workspace_id).order_by(KnowledgeFolder.lft)
    )
    rows = result.scalars().all()
    return [{"id": f.id, "name": f.name, "desc": f.desc, "parent_id": f.parent_id} for f in rows]


@router.post("/folder", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_knowledge_folder(
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    folder = KnowledgeFolder(
        name=body.get("name", ""),
        desc=body.get("desc"),
        parent_id=body.get("parent_id"),
        workspace_id=body.get("workspace_id", "default"),
        user_id=current_user.id,
    )
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return {"id": folder.id, "name": folder.name, "desc": folder.desc, "parent_id": folder.parent_id}


# ---------------------------------------------------------------------------
# Knowledge base sub-routes (MUST come before /{knowledge_id} catch-all)
# ---------------------------------------------------------------------------


@router.post("/base")
async def create_knowledge_base(
    body: KnowledgeCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> KnowledgeOut:
    """Legacy alias for creating a knowledge base."""
    return await _create_knowledge(body, session, current_user)


@router.get("/{knowledge_id}", response_model=KnowledgeOut)
async def get_knowledge(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> KnowledgeOut:
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")
    return KnowledgeOut.model_validate(knowledge)


@router.put("/{knowledge_id}", response_model=KnowledgeOut)
async def update_knowledge(
    knowledge_id: str,
    body: KnowledgeUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> KnowledgeOut:
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "embedding_model_id" and value is not None:
            value = uuid_module.UUID(value)
        setattr(knowledge, field, value)
    await session.commit()
    await session.refresh(knowledge)
    return KnowledgeOut.model_validate(knowledge)


@router.delete("/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")
    await session.delete(knowledge)
    await session.commit()


# ---------------------------------------------------------------------------
# Document CRUD (scoped under knowledge base)
# ---------------------------------------------------------------------------


@router.get("/{knowledge_id}/document", response_model=DocumentPage)
async def list_documents(
    knowledge_id: str,
    page: int = 1,
    size: int = 10,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> DocumentPage:
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    total = await session.scalar(
        select(func.count()).select_from(Document).where(Document.knowledge_id == knowledge_id)
    )
    result = await session.execute(
        select(Document)
        .where(Document.knowledge_id == knowledge_id)
        .order_by(Document.create_time.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = result.scalars().all()
    return DocumentPage(records=[DocumentOut.model_validate(d) for d in rows], total=total or 0)


@router.post("/{knowledge_id}/document", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(
    knowledge_id: str,
    body: DocumentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    document = Document(
        knowledge_id=knowledge_id,
        name=body.name,
        type=body.type,
        hit_handling_method=body.hit_handling_method,
        directly_return_similarity=body.directly_return_similarity,
        meta=body.meta,
        user_id=current_user.id,
        status="WAIT",
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return DocumentOut.model_validate(document)


@router.get("/{knowledge_id}/document/{document_id}", response_model=DocumentOut)
async def get_document(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> DocumentOut:
    document = await session.get(Document, document_id)
    if document is None or str(document.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentOut.model_validate(document)


@router.put("/{knowledge_id}/document/{document_id}", response_model=DocumentOut)
async def update_document(
    knowledge_id: str,
    document_id: str,
    body: DocumentUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> DocumentOut:
    document = await session.get(Document, document_id)
    if document is None or str(document.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(document, field, value)

    await session.commit()
    await session.refresh(document)
    return DocumentOut.model_validate(document)


@router.delete("/{knowledge_id}/document/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    document = await session.get(Document, document_id)
    if document is None or str(document.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await session.delete(document)
    await session.commit()


# ---------------------------------------------------------------------------
# Paragraph CRUD (scoped under document)
# ---------------------------------------------------------------------------


@router.get("/{knowledge_id}/document/{document_id}/paragraph", response_model=ParagraphPage)
async def list_paragraphs(
    knowledge_id: str,
    document_id: str,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ParagraphPage:
    document = await session.get(Document, document_id)
    if document is None or str(document.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    total = await session.scalar(
        select(func.count()).select_from(Paragraph).where(Paragraph.document_id == document_id)
    )
    result = await session.execute(
        select(Paragraph)
        .where(Paragraph.document_id == document_id)
        .order_by(Paragraph.position.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = result.scalars().all()
    return ParagraphPage(records=[ParagraphOut.model_validate(p) for p in rows], total=total or 0)


@router.get(
    "/{knowledge_id}/document/{document_id}/paragraph/{paragraph_id}",
    response_model=ParagraphOut,
)
async def get_paragraph(
    knowledge_id: str,
    document_id: str,
    paragraph_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ParagraphOut:
    paragraph = await session.get(Paragraph, paragraph_id)
    if paragraph is None or str(paragraph.document_id) != document_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")
    return ParagraphOut.model_validate(paragraph)


# ---------------------------------------------------------------------------
# Hit test
# ---------------------------------------------------------------------------


@router.post("/{knowledge_id}/hit_test", response_model=HitTestResponse)
async def hit_test(
    knowledge_id: str,
    body: HitTestRequest,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> HitTestResponse:
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    embedding_model_row = (
        await session.get(Model, knowledge.embedding_model_id) if knowledge.embedding_model_id else None
    )
    if embedding_model_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No embedding model configured")

    from app.rag.embed import embed_texts, normalize_for_embedding
    from app.rag.retriever import PgVectorRetriever

    dimensions = (embedding_model_row.meta or {}).get("dimensions")
    vectors = await embed_texts(
        embedding_model_row.provider,
        embedding_model_row.model_name,
        embedding_model_row.credential or {},
        [normalize_for_embedding(body.query)],
        dimensions=dimensions,
    )
    if not vectors:
        return HitTestResponse(results=[], total=0)

    retriever = PgVectorRetriever()
    rows = await retriever.search(
        query_embedding=vectors[0],
        knowledge_ids=[knowledge_id],
        top_n=body.top_n,
        similarity=body.similarity,
        search_mode=body.search_mode,
        query_text=body.query,
    )

    hits = []
    for r in rows:
        doc = await session.get(Document, r.get("document_id"))
        hits.append(
            HitTestResult(
                paragraph_id=r.get("paragraph_id"),
                document_id=r.get("document_id"),
                document_name=doc.name if doc else "",
                content=r.get("content", ""),
                title=r.get("title", ""),
                similarity=r.get("similarity", 0.0),
                hit_num=r.get("hit_num", 0),
            )
        )

    return HitTestResponse(results=hits, total=len(hits))


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@router.get("/{knowledge_id}/tag", response_model=list[TagOut])
async def list_tags(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[TagOut]:
    result = await session.execute(select(Tag).where(Tag.knowledge_id == knowledge_id).order_by(Tag.key, Tag.value))
    return [TagOut.model_validate(t) for t in result.scalars().all()]


@router.post("/{knowledge_id}/tag", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(
    knowledge_id: str,
    body: TagCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> TagOut:
    tag = Tag(knowledge_id=knowledge_id, key=body.key, value=body.value)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return TagOut.model_validate(tag)


@router.delete("/{knowledge_id}/tag/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    knowledge_id: str,
    tag_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    tag = await session.get(Tag, tag_id)
    if tag is None or str(tag.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    await session.delete(tag)
    await session.commit()


# ---------------------------------------------------------------------------
# Trigger embedding
# ---------------------------------------------------------------------------


@router.post("/{knowledge_id}/embedding")
async def trigger_embedding(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    result = await session.execute(
        select(Document).where(
            Document.knowledge_id == knowledge_id,
            Document.is_active == True,  # noqa: E712
            Document.status.in_(["WAIT", "ERROR"]),
        )
    )
    documents = result.scalars().all()

    for doc in documents:
        doc.status = "PENDING"
        doc.status_meta = {"step": "queued"}

    await session.commit()

    return {"result": True, "document_count": len(documents), "document_ids": [str(d.id) for d in documents]}


# ---------------------------------------------------------------------------
# Batch operations
# ---------------------------------------------------------------------------


@router.put("/{knowledge_id}/document/batch_delete")
async def batch_delete_documents(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Soft-delete documents by id_list."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    id_list = body.get("id_list", [])
    for did in id_list:
        doc = await session.get(Document, did)
        if doc is not None and str(doc.knowledge_id) == knowledge_id:
            doc.is_active = False

    await session.commit()
    return {"result": True, "count": len(id_list)}


@router.put("/batch_delete")
async def batch_delete_knowledge(
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Delete knowledge bases by id_list."""
    id_list = body.get("id_list", [])
    for kid in id_list:
        kb = await session.get(Knowledge, kid)
        if kb is not None:
            await session.delete(kb)

    await session.commit()
    return {"result": True, "count": len(id_list)}


@router.put("/batch_move")
async def batch_move_knowledge(
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Move knowledge bases to a target folder."""
    id_list = body.get("id_list", [])
    folder_id = body.get("folder_id", "")

    for kid in id_list:
        kb = await session.get(Knowledge, kid)
        if kb is not None:
            kb.folder_id = folder_id

    await session.commit()
    return {"result": True, "count": len(id_list)}


@router.put("/{knowledge_id}/document/batch_refresh")
async def batch_refresh_documents(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: batch refresh documents."""
    return {"result": True}


@router.put("/{knowledge_id}/document/batch_hit_handling")
async def batch_hit_handling(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: batch set hit handling for documents."""
    return {"result": True}


@router.put("/{knowledge_id}/document/batch_cancel_task")
async def batch_cancel_task(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: batch cancel document tasks."""
    return {"result": True}


@router.post("/{knowledge_id}/document/batch_create")
async def batch_create_documents(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: batch create documents."""
    return {"result": True}


@router.post("/{knowledge_id}/document/batch_export")
async def batch_export_documents(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: batch export documents."""
    return {"result": True}


@router.post("/{knowledge_id}/document/batch_add_tag")
async def batch_add_tag(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Add a tag to multiple documents."""
    id_list: list = body.get("id_list", [])
    tag_id: str = body.get("tag_id", "")

    tag = await session.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    for did in id_list:
        existing = await session.execute(
            select(DocumentTag).where(DocumentTag.document_id == did, DocumentTag.tag_id == tag_id)
        )
        if existing.scalar_one_or_none() is None:
            session.add(DocumentTag(document_id=did, tag_id=tag_id))

    await session.commit()
    return {"result": True, "count": len(id_list)}


@router.get("/{knowledge_id}/document/batch_export")
async def get_batch_export_documents(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: get batch export status."""
    return {"result": True}


@router.get("/{knowledge_id}/document/batch_export_zip")
async def get_batch_export_zip(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: download batch export zip."""
    return {"result": True}


# ---------------------------------------------------------------------------
# Document operations (individual)
# ---------------------------------------------------------------------------


@router.put("/{knowledge_id}/document/{document_id}/refresh")
async def refresh_document(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Set document status to PENDING for re-embedding."""
    document = await session.get(Document, document_id)
    if document is None or str(document.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document.status = "PENDING"
    document.status_meta = {"step": "queued"}
    await session.commit()
    return {"result": True}


@router.put("/{knowledge_id}/document/{document_id}/sync")
async def sync_document(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: sync document."""
    return {"result": True}


@router.put("/{knowledge_id}/document/{document_id}/tokenize")
async def tokenize_document(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: tokenize document."""
    return {"result": True}


@router.put("/{knowledge_id}/document/{document_id}/cancel_task")
async def cancel_document_task(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Set document status back to WAIT."""
    document = await session.get(Document, document_id)
    if document is None or str(document.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document.status = "WAIT"
    document.status_meta = {}
    await session.commit()
    return {"result": True}


@router.get("/{knowledge_id}/document/{document_id}/export")
async def export_document(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: export document."""
    return {"result": True}


@router.get("/{knowledge_id}/document/{document_id}/export_zip")
async def export_document_zip(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: download document export zip."""
    return {"result": True}


@router.get("/{knowledge_id}/document/{document_id}/download_source_file")
async def download_source_file(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: download document source file."""
    return {"result": True}


@router.put("/{knowledge_id}/document/{document_id}/replace_source_file")
async def replace_source_file(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: replace document source file."""
    return {"result": True}


@router.post("/{knowledge_id}/document/{document_id}/sync")
async def post_sync_document(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: sync document (POST variant)."""
    return {"result": True}


@router.put("/{knowledge_id}/document/migrate/{target_knowledge_id}")
async def migrate_documents(
    knowledge_id: str,
    target_knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: migrate documents to another knowledge base."""
    return {"result": True}


# ---------------------------------------------------------------------------
# Document import (special document types)
# ---------------------------------------------------------------------------


@router.post("/{knowledge_id}/document/qa")
async def create_qa_document(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a QA-type document."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    document = Document(
        knowledge_id=knowledge_id,
        name=body.get("name", "QA Document"),
        type=body.get("type", 3),
        hit_handling_method=body.get("hit_handling_method", "optimization"),
        directly_return_similarity=body.get("directly_return_similarity", 0.9),
        meta=body.get("meta", {}),
        user_id=current_user.id,
        status="WAIT",
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return {"result": True, "document": DocumentOut.model_validate(document).model_dump(mode="json")}


@router.post("/{knowledge_id}/document/table")
async def create_table_document(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a table-type document."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    document = Document(
        knowledge_id=knowledge_id,
        name=body.get("name", "Table Document"),
        type=body.get("type", 4),
        hit_handling_method=body.get("hit_handling_method", "optimization"),
        directly_return_similarity=body.get("directly_return_similarity", 0.9),
        meta=body.get("meta", {}),
        user_id=current_user.id,
        status="WAIT",
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return {"result": True, "document": DocumentOut.model_validate(document).model_dump(mode="json")}


@router.put("/{knowledge_id}/document/web")
async def create_web_document(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a web-type document."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    document = Document(
        knowledge_id=knowledge_id,
        name=body.get("name", "Web Document"),
        type=body.get("type", 2),
        hit_handling_method=body.get("hit_handling_method", "optimization"),
        directly_return_similarity=body.get("directly_return_similarity", 0.9),
        meta=body.get("meta", {}),
        user_id=current_user.id,
        status="WAIT",
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return {"result": True, "document": DocumentOut.model_validate(document).model_dump(mode="json")}


@router.get("/{knowledge_id}/document/split_pattern")
async def get_split_pattern(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: get document split patterns."""
    return {"result": True, "patterns": []}


@router.post("/{knowledge_id}/document/split")
async def split_document(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: split a document."""
    return {"result": True}


# ---------------------------------------------------------------------------
# Knowledge operations (models, publish, export, etc.)
# ---------------------------------------------------------------------------


@router.get("/{knowledge_id}/model")
async def list_knowledge_models(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """List all LLM models from the database."""
    result = await session.execute(select(Model))
    models = result.scalars().all()
    return {
        "result": True,
        "models": [
            {
                "id": str(m.id),
                "provider": m.provider,
                "model_name": m.model_name,
                "model_type": m.model_type,
            }
            for m in models
        ],
    }


@router.get("/{knowledge_id}/embedding_model")
async def list_embedding_models(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """List embedding models from the database."""
    result = await session.execute(select(Model))
    models = result.scalars().all()
    return {
        "result": True,
        "models": [
            {
                "id": str(m.id),
                "provider": m.provider,
                "model_name": m.model_name,
                "model_type": m.model_type,
                "meta": m.meta,
            }
            for m in models
        ],
    }


# Legacy alias for frontend typo "emdedding_model" → "embedding_model"
@router.get("/{knowledge_id}/emdedding_model", include_in_schema=False)
async def list_embedding_models_alias(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    return await list_embedding_models(knowledge_id, session, _)


@router.post("/{knowledge_id}/generate_related")
async def generate_related(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: generate related questions."""
    return {"result": True}


@router.put("/{knowledge_id}/publish")
async def publish_knowledge(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Update the publish flag for a knowledge base."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    is_publish = body.get("is_publish", False)
    # Store publish flag in meta for now
    knowledge.meta = {**(knowledge.meta or {}), "is_publish": is_publish}
    await session.commit()
    return {"result": True, "is_publish": is_publish}


@router.get("/{knowledge_id}/sync")
async def sync_knowledge(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: sync knowledge base."""
    return {"result": True}


@router.get("/{knowledge_id}/export")
async def export_knowledge(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: export knowledge base."""
    return {"result": True}


@router.get("/{knowledge_id}/export_zip")
async def export_knowledge_zip(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: download knowledge base export zip."""
    return {"result": True}


@router.get("/{knowledge_id}/export_knowledge")
async def export_knowledge_data(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: export knowledge base data."""
    return {"result": True}


@router.post("/import_knowledge")
async def import_knowledge(
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: import knowledge base."""
    return {"result": True}


@router.get("/{knowledge_id}/mcp_tools")
async def get_mcp_tools(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: get MCP tools for a knowledge base."""
    return {"result": True, "tools": []}


# ---------------------------------------------------------------------------
# Knowledge versions
# ---------------------------------------------------------------------------


@router.get("/{knowledge_id}/knowledge_version")
async def list_knowledge_versions(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: list knowledge base versions."""
    return {"result": True, "versions": []}


@router.get("/{knowledge_id}/knowledge_version/{version_id}")
async def get_knowledge_version(
    knowledge_id: str,
    version_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: get a specific knowledge base version."""
    return {"result": True, "version": {}}


# ---------------------------------------------------------------------------
# Tags (extended)
# ---------------------------------------------------------------------------


@router.get("/{knowledge_id}/tags")
async def list_tags_alias(
    knowledge_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[TagOut]:
    """Alias for tag list."""
    result = await session.execute(select(Tag).where(Tag.knowledge_id == knowledge_id).order_by(Tag.key, Tag.value))
    return [TagOut.model_validate(t) for t in result.scalars().all()]


@router.put("/{knowledge_id}/tag/{tag_id}", response_model=TagOut)
async def update_tag(
    knowledge_id: str,
    tag_id: str,
    body: TagCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> TagOut:
    """Update a tag."""
    tag = await session.get(Tag, tag_id)
    if tag is None or str(tag.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    tag.key = body.key
    tag.value = body.value
    await session.commit()
    await session.refresh(tag)
    return TagOut.model_validate(tag)


@router.delete("/{knowledge_id}/tag/{tag_id}/{del_type}")
async def delete_tag_with_type(
    knowledge_id: str,
    tag_id: str,
    del_type: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Delete a tag with optional cascade type."""
    tag = await session.get(Tag, tag_id)
    if tag is None or str(tag.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    # Remove tag-document mappings first
    await session.execute(select(DocumentTag).where(DocumentTag.tag_id == tag_id))
    mappings = (await session.execute(select(DocumentTag).where(DocumentTag.tag_id == tag_id))).scalars().all()
    for m in mappings:
        await session.delete(m)

    await session.delete(tag)
    await session.commit()
    return {"result": True}


@router.delete("/{knowledge_id}/tags/batch_delete")
async def batch_delete_tags(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Batch delete tags."""
    id_list = body.get("id_list", [])
    for tid in id_list:
        tag = await session.get(Tag, tid)
        if tag is not None and str(tag.knowledge_id) == knowledge_id:
            # Remove tag-document mappings
            mappings = (await session.execute(select(DocumentTag).where(DocumentTag.tag_id == tid))).scalars().all()
            for m in mappings:
                await session.delete(m)
            await session.delete(tag)

    await session.commit()
    return {"result": True, "count": len(id_list)}


@router.get("/{knowledge_id}/document/{document_id}/tags")
async def get_document_tags(
    knowledge_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[TagOut]:
    """Get tags for a document."""
    result = await session.execute(
        select(Tag)
        .join(DocumentTag, Tag.id == DocumentTag.tag_id)
        .where(DocumentTag.document_id == document_id, Tag.knowledge_id == knowledge_id)
    )
    return [TagOut.model_validate(t) for t in result.scalars().all()]


@router.post("/{knowledge_id}/document/{document_id}/tags")
async def add_tag_to_document(
    knowledge_id: str,
    document_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Add a tag to a document."""
    tag_id = body.get("tag_id", "")

    document = await session.get(Document, document_id)
    if document is None or str(document.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    tag = await session.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    existing = await session.execute(
        select(DocumentTag).where(DocumentTag.document_id == document_id, DocumentTag.tag_id == tag_id)
    )
    if existing.scalar_one_or_none() is None:
        session.add(DocumentTag(document_id=document_id, tag_id=tag_id))
        await session.commit()

    return {"result": True}


@router.delete("/{knowledge_id}/document/{document_id}/tags/batch_delete")
async def batch_remove_tags_from_documents(
    knowledge_id: str,
    document_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Remove tags from documents."""
    id_list = body.get("id_list", [])
    for tid in id_list:
        mappings = (
            (
                await session.execute(
                    select(DocumentTag).where(DocumentTag.document_id == document_id, DocumentTag.tag_id == tid)
                )
            )
            .scalars()
            .all()
        )
        for m in mappings:
            await session.delete(m)

    await session.commit()
    return {"result": True, "count": len(id_list)}


@router.delete("/{knowledge_id}/tag/{tag_id}/docs_delete")
async def remove_tag_from_all_docs(
    knowledge_id: str,
    tag_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Remove a tag from all documents in this knowledge base."""
    tag = await session.get(Tag, tag_id)
    if tag is None or str(tag.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    mappings = (await session.execute(select(DocumentTag).where(DocumentTag.tag_id == tag_id))).scalars().all()
    for m in mappings:
        await session.delete(m)

    await session.commit()
    return {"result": True}


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


@router.get("/document/template/export")
async def export_document_template(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: export document template."""
    return {"result": True}


@router.get("/document/table_template/export")
async def export_table_template(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Stub: export table template."""
    return {"result": True}


# ---------------------------------------------------------------------------
# Path pagination (MUST be at the end to avoid shadowing sub-routes)
# ---------------------------------------------------------------------------


@router.get("/{page}/{page_size}")
async def list_knowledge_paginated(
    page: int,
    page_size: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> KnowledgePage:
    """Paginated knowledge base list via path parameters."""
    total = await session.scalar(select(func.count()).select_from(Knowledge))
    result = await session.execute(
        select(Knowledge).order_by(Knowledge.create_time.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    rows = result.scalars().all()
    return KnowledgePage(records=[KnowledgeOut.model_validate(k) for k in rows], total=total or 0)


@router.get("/{knowledge_id}/document/{page}/{page_size}")
async def list_documents_paginated(
    knowledge_id: str,
    page: int,
    page_size: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> DocumentPage:
    """Paginated document list via path parameters."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    total = await session.scalar(
        select(func.count()).select_from(Document).where(Document.knowledge_id == knowledge_id)
    )
    result = await session.execute(
        select(Document)
        .where(Document.knowledge_id == knowledge_id)
        .order_by(Document.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()
    return DocumentPage(records=[DocumentOut.model_validate(d) for d in rows], total=total or 0)


@router.get("/{knowledge_id}/tag/{current_page}/{page_size}")
async def list_tags_paginated(
    knowledge_id: str,
    current_page: int,
    page_size: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Paginated tag list via path parameters."""
    total = await session.scalar(select(func.count()).select_from(Tag).where(Tag.knowledge_id == knowledge_id))
    result = await session.execute(
        select(Tag)
        .where(Tag.knowledge_id == knowledge_id)
        .order_by(Tag.key, Tag.value)
        .offset((current_page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()
    return {
        "list": [TagOut.model_validate(t).model_dump(mode="json") for t in rows],
        "total": total or 0,
    }


@router.get("/{knowledge_id}/knowledge_version/{page}/{page_size}")
async def list_knowledge_versions_paginated(
    knowledge_id: str,
    page: int,
    page_size: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Paginated knowledge base version list via path parameters."""
    return {"result": True, "list": [], "total": 0}
