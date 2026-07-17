"""Knowledge-base CRUD API — KB, document, paragraph, hit test, embedding trigger."""

from __future__ import annotations

import uuid as uuid_module

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user
from app.core.tasks import enqueue_ingest
from app.models.knowledge import (
    Document,
    DocumentTag,
    Knowledge,
    KnowledgeFolder,
    Paragraph,
    Problem,
    ProblemParagraphMapping,
    Tag,
    Termbase,
)
from app.models.models_provider import Model
from app.models.user import User
from app.providers.base import resolve_credential
from app.schemas.knowledge import (
    DocumentCreate,
    DocumentOut,
    DocumentPage,
    DocumentUpdate,
    HitTestRequest,
    KnowledgeCreate,
    KnowledgeOut,
    KnowledgePage,
    KnowledgeUpdate,
    ParagraphOut,
    ParagraphPage,
    ProblemOut,
    ProblemPage,
    ProblemParagraphOut,
    TagCreate,
    TagOut,
    TermbaseOut,
    TermbasePage,
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
        select(KnowledgeFolder)
        .where(KnowledgeFolder.workspace_id == workspace_id)
        .order_by(KnowledgeFolder.create_time)
    )
    rows = result.scalars().all()

    # The Next.js tree view needs a *nested* structure (each node carrying a
    # ``children`` array); a flat list would render every folder at the top
    # level. Build the tree purely from ``parent_id`` so we don't depend on the
    # legacy MPTT (lft/rght) columns, which are not maintained on insert.
    folders = [
        {"id": f.id, "name": f.name, "desc": f.desc, "parent_id": f.parent_id}
        for f in rows
    ]
    ids = {f["id"] for f in folders}
    children_map: dict[str | None, list[dict]] = {}
    for f in folders:
        children_map.setdefault(f["parent_id"], []).append(f)
    for f in folders:
        f["children"] = children_map.get(f["id"], [])

    # Roots: parent_id is NULL or points to a folder that does not exist
    # (e.g. the 'default' workspace marker when the default folder is absent).
    roots = [f for f in folders if f["parent_id"] is None or f["parent_id"] not in ids]
    return roots


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


@router.post("/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    folder_id: str = Form("default"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """One-step upload: auto-create knowledge base + document, enqueue for ingestion if embedding model available.

    Called by the standalone upload page (``knowledge/upload``). If a usable embedding model exists
    (first one found in the database), ingestion is enqueued immediately. Otherwise the document
    is created with status WAIT and the user must configure an embedding model separately.
    """
    from app.rag.pipeline import parse_file

    _ = parse_file(file.filename or "document", await file.read())
    _ = await file.seek(0)
    content_bytes = await file.read()

    knowledge = Knowledge(
        name=file.filename or "Uploaded Document",
        desc="",
        type=0,
        folder_id=folder_id,
        workspace_id="default",
        user_id=current_user.id,
    )
    session.add(knowledge)

    # Find any embedding model to allow auto-ingestion
    embedding_result = await session.execute(
        select(Model).where(Model.model_type == "embedding").limit(1)
    )
    embedding_model_row = embedding_result.scalar_one_or_none()
    if embedding_model_row is not None:
        knowledge.embedding_model_id = embedding_model_row.id

    await session.flush()

    document = Document(
        knowledge_id=knowledge.id,
        name=file.filename or "document",
        type=0,
        status="PENDING" if embedding_model_row else "WAIT",
        status_meta={"step": "queued", "filename": file.filename} if embedding_model_row else {},
        user_id=current_user.id,
    )
    session.add(document)
    await session.flush()
    await session.commit()

    if embedding_model_row is not None:
        embedding = {
            "provider": embedding_model_row.provider,
            "model_name": embedding_model_row.model_name,
            "credential": resolve_credential(embedding_model_row.credential),
            "dimensions": (embedding_model_row.meta or {}).get("dimensions"),
        }
        await enqueue_ingest(
            knowledge_id=str(knowledge.id),
            document_id=str(document.id),
            user_id=str(current_user.id) if current_user.id is not None else None,
            filename=file.filename or "document",
            content=content_bytes,
            embedding=embedding,
            with_filter=False,
            limit=4096,
        )

    return {
        "result": True,
        "knowledge_id": str(knowledge.id),
        "document_id": str(document.id),
        "document_count": 1,
    }


@router.post("/workflow")
async def create_workflow_knowledge(
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a workflow-type knowledge base with an initial empty workflow."""
    import uuid as _uuid

    knowledge_id = _uuid.uuid7()
    knowledge = Knowledge(
        id=knowledge_id,
        name=body.get("name", "Workflow Knowledge"),
        desc=body.get("desc", ""),
        type=body.get("type", 1),  # type=1 means workflow
        scope=body.get("scope", "WORKSPACE"),
        folder_id=body.get("folder_id", "default"),
        workspace_id=body.get("workspace_id", "default"),
        embedding_model_id=uuid_module.UUID(body["embedding_model_id"]) if body.get("embedding_model_id") else None,
        user_id=current_user.id,
        meta=body.get("meta", {}),
    )
    session.add(knowledge)

    from app.models.knowledge import KnowledgeWorkflow

    workflow = KnowledgeWorkflow(
        id=_uuid.uuid7(),
        knowledge_id=knowledge_id,
        workspace_id=body.get("workspace_id", "default"),
        work_flow=body.get("work_flow", {}),
    )
    session.add(workflow)
    await session.commit()
    await session.refresh(knowledge)

    return {
        "result": True,
        "knowledge": KnowledgeOut.model_validate(knowledge).model_dump(mode="json"),
    }


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


# ---------------------------------------------------------------------------
# Paragraph CRUD (scoped under document)
# ---------------------------------------------------------------------------
# NOTE: get/update/delete_document for the generic `/document/{document_id}` path are
# registered at the END of this module (see "Generic single-document routes" section)
# so that constant-segment routes like `document/batch_create` are matched first.


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


@router.post("/{knowledge_id}/hit_test", response_model=list[dict])
async def hit_test(
    knowledge_id: str,
    body: HitTestRequest,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """Legacy-compatible hit test.

    Returns a **list** of paragraph hits (each with ``comprehensive_score``),
    matching the legacy ``KnowledgeSerializer.HitTest.hit_test`` shape that the
    frontend sorts with ``arraySort(res.data, 'comprehensive_score', true)``.
    """
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    embedding_model_row = (
        await session.get(Model, knowledge.embedding_model_id) if knowledge.embedding_model_id else None
    )
    if embedding_model_row is None:
        # Fall back to the first available embedding model (mirrors the upload flow).
        fallback_result = await session.execute(
            select(Model).where(Model.model_type == "embedding").limit(1)
        )
        embedding_model_row = fallback_result.scalar_one_or_none()
        if embedding_model_row is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No embedding model configured")
        # Persist the resolved model so subsequent calls work without fallback.
        knowledge.embedding_model_id = embedding_model_row.id
        await session.commit()

    from app.rag.embed import embed_texts, normalize_for_embedding
    from app.rag.retriever import PgVectorRetriever

    dimensions = (embedding_model_row.meta or {}).get("dimensions")
    vectors = await embed_texts(
        embedding_model_row.provider,
        embedding_model_row.model_name,
        embedding_model_row.credential or {},
        [normalize_for_embedding(body.query_text)],
        dimensions=dimensions,
    )
    if not vectors:
        return []

    retriever = PgVectorRetriever()
    rows = await retriever.search(
        query_embedding=vectors[0],
        knowledge_ids=[knowledge_id],
        top_n=body.top_number,
        similarity=body.similarity,
        search_mode=body.search_mode,
        query_text=body.query_text,
    )
    if not rows:
        return []

    paragraph_ids = [r["paragraph_id"] for r in rows]
    p_result = await session.execute(select(Paragraph).where(Paragraph.id.in_(paragraph_ids)))
    paragraphs = {p.id: p for p in p_result.scalars().all()}
    doc_ids = {p.document_id for p in paragraphs.values()}
    d_result = await session.execute(select(Document).where(Document.id.in_(doc_ids)))
    documents = {d.id: d for d in d_result.scalars().all()}

    hits = []
    for r in rows:
        pid = r["paragraph_id"]
        p = paragraphs.get(pid)
        doc = documents.get(p.document_id) if p else None
        similarity = float(r.get("similarity", 0.0))
        hits.append(
            {
                "id": str(pid),
                "paragraph_id": str(pid),
                "document_id": str(p.document_id) if p else "",
                "document_name": doc.name if doc else "",
                "content": r.get("content", ""),
                "title": r.get("title", ""),
                "similarity": similarity,
                "comprehensive_score": similarity,
                "is_active": p.is_active if p else True,
                "hit_num": p.hit_num if p else 0,
                "star_num": 0,
                "trample_num": 0,
            }
        )

    return hits


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
# Termbase CRUD (custom tokenization)
# ---------------------------------------------------------------------------
# IMPORTANT: static routes (batch_delete, batch_export) MUST be declared
# before the dynamic {termbase_id} route to avoid being captured by it.


@router.put("/{knowledge_id}/termbase/batch_delete")
async def batch_delete_termbase(
    knowledge_id: str,
    body: list[str],
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Batch delete termbase entries by id list."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    for tid in body:
        term = await session.get(Termbase, tid)
        if term is not None and str(term.knowledge_id) == knowledge_id:
            await session.delete(term)

    await session.commit()
    return {"result": True}


@router.post("/{knowledge_id}/termbase/batch_export")
async def batch_export_termbase(
    knowledge_id: str,
    body: list[str],
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> str:
    """Batch export termbase entries as newline-separated plain text."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    result = await session.execute(
        select(Termbase.content)
        .where(Termbase.id.in_(body), Termbase.knowledge_id == knowledge_id)
        .order_by(Termbase.create_time.desc())
    )
    contents = result.scalars().all()
    return "\n".join(contents)


@router.post("/{knowledge_id}/termbase", response_model=list[TermbaseOut])
async def create_termbase(
    knowledge_id: str,
    body: list[str],
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[TermbaseOut]:
    """Batch create termbase entries. Body is a list of content strings."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    unique_contents = list(set(body))

    # Check existing to avoid duplicates
    existing_result = await session.execute(
        select(Termbase.content).where(
            Termbase.knowledge_id == knowledge_id,
            Termbase.content.in_(unique_contents),
        )
    )
    existing_contents = set(existing_result.scalars().all())

    created: list[Termbase] = []
    for content in unique_contents:
        if content not in existing_contents:
            term = Termbase(knowledge_id=knowledge_id, content=content)
            session.add(term)
            created.append(term)

    await session.commit()
    for term in created:
        await session.refresh(term)

    return [TermbaseOut.model_validate(t) for t in created]


@router.get("/{knowledge_id}/termbase/{current_page}/{page_size}", response_model=TermbasePage)
async def list_termbase_page(
    knowledge_id: str,
    current_page: int,
    page_size: int,
    content: str = "",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> TermbasePage:
    """Paginated list of termbase entries for a knowledge base."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    base_filter = [Termbase.knowledge_id == knowledge_id]
    if content:
        base_filter.append(Termbase.content.ilike(f"%{content}%"))

    total = await session.scalar(
        select(func.count()).select_from(Termbase).where(*base_filter)
    )
    result = await session.execute(
        select(Termbase)
        .where(*base_filter)
        .order_by(Termbase.create_time.desc())
        .offset((current_page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()
    return TermbasePage(records=[TermbaseOut.model_validate(t) for t in rows], total=total or 0)


@router.put("/{knowledge_id}/termbase/{termbase_id}")
async def update_termbase(
    knowledge_id: str,
    termbase_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Update a single termbase entry's content."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    term = await session.get(Termbase, termbase_id)
    if term is None or str(term.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Termbase not found")

    term.content = body.get("content", term.content)
    await session.commit()
    return {"result": True}


@router.delete("/{knowledge_id}/termbase/{termbase_id}")
async def delete_termbase(
    knowledge_id: str,
    termbase_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Delete a single termbase entry."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    term = await session.get(Termbase, termbase_id)
    if term is None or str(term.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Termbase not found")

    await session.delete(term)
    await session.commit()
    return {"result": True}


# ---------------------------------------------------------------------------
# Problem CRUD
# ---------------------------------------------------------------------------
# IMPORTANT: static routes (batch_delete, batch_association) MUST be declared
# before the dynamic {problem_id} route to avoid being captured by it.


@router.put("/{knowledge_id}/problem/batch_delete")
async def batch_delete_problems(
    knowledge_id: str,
    body: list[str],
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Batch delete problems and their paragraph mappings."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    # Delete problem-paragraph mappings first
    mapping_result = await session.execute(
        select(ProblemParagraphMapping).where(
            ProblemParagraphMapping.knowledge_id == knowledge_id,
            ProblemParagraphMapping.problem_id.in_(body),
        )
    )
    for m in mapping_result.scalars().all():
        await session.delete(m)

    for pid in body:
        problem = await session.get(Problem, pid)
        if problem is not None and str(problem.knowledge_id) == knowledge_id:
            await session.delete(problem)

    await session.commit()
    return {"result": True}


@router.put("/{knowledge_id}/problem/batch_association")
async def batch_associate_problems(
    knowledge_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Batch associate problems with paragraphs."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    problem_id_list: list[str] = body.get("problem_id_list", [])
    paragraph_list: list[dict] = body.get("paragraph_list", [])

    if not problem_id_list or not paragraph_list:
        return {"result": True}

    # Check existing mappings to avoid duplicates
    paragraph_ids = [p.get("paragraph_id") for p in paragraph_list]
    existing_result = await session.execute(
        select(ProblemParagraphMapping).where(
            ProblemParagraphMapping.problem_id.in_(problem_id_list),
            ProblemParagraphMapping.paragraph_id.in_(paragraph_ids),
        )
    )
    existing = set(
        (str(m.problem_id), str(m.paragraph_id)) for m in existing_result.scalars().all()
    )

    for problem_id in problem_id_list:
        problem = await session.get(Problem, problem_id)
        if problem is None:
            continue
        for paragraph in paragraph_list:
            paragraph_id = paragraph.get("paragraph_id", "")
            document_id = paragraph.get("document_id", "")
            if (problem_id, paragraph_id) not in existing:
                session.add(
                    ProblemParagraphMapping(
                        knowledge_id=knowledge_id,
                        document_id=document_id,
                        problem_id=problem_id,
                        paragraph_id=paragraph_id,
                    )
                )

    await session.commit()
    return {"result": True}


@router.post("/{knowledge_id}/problem", response_model=list[ProblemOut])
async def create_problems(
    knowledge_id: str,
    body: list[str],
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[ProblemOut]:
    """Batch create problems. Body is a list of content strings."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    unique_contents = list(set(body))

    existing_result = await session.execute(
        select(Problem.content).where(
            Problem.knowledge_id == knowledge_id,
            Problem.content.in_(unique_contents),
        )
    )
    existing_contents = set(existing_result.scalars().all())

    created: list[Problem] = []
    for content in unique_contents:
        if content not in existing_contents:
            problem = Problem(knowledge_id=knowledge_id, content=content)
            session.add(problem)
            created.append(problem)

    await session.commit()
    for problem in created:
        await session.refresh(problem)

    return [_problem_to_out(p, 0) for p in created]


@router.get("/{knowledge_id}/problem/{current_page}/{page_size}", response_model=ProblemPage)
async def list_problems_page(
    knowledge_id: str,
    current_page: int,
    page_size: int,
    content: str = "",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ProblemPage:
    """Paginated list of problems for a knowledge base."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    base_filter = [Problem.knowledge_id == knowledge_id]
    if content:
        base_filter.append(Problem.content.ilike(f"%{content}%"))

    total = await session.scalar(
        select(func.count()).select_from(Problem).where(*base_filter)
    )
    result = await session.execute(
        select(Problem)
        .where(*base_filter)
        .order_by(Problem.create_time.desc())
        .offset((current_page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()

    # Resolve paragraph_count for each problem
    problem_ids = [p.id for p in rows]
    counts: dict = {}
    if problem_ids:
        count_result = await session.execute(
            text(
                "SELECT problem_id, COUNT(*) AS cnt FROM problem_paragraph_mapping "
                "WHERE problem_id = ANY(:pids) GROUP BY problem_id"
            ),
            {"pids": problem_ids},
        )
        counts = {row[0]: row[1] for row in count_result.fetchall()}

    return ProblemPage(
        records=[_problem_to_out(p, counts.get(p.id, 0)) for p in rows],
        total=total or 0,
    )


@router.get("/{knowledge_id}/problem/{problem_id}/paragraph", response_model=list[ProblemParagraphOut])
async def get_problem_paragraphs(
    knowledge_id: str,
    problem_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[ProblemParagraphOut]:
    """Get associated paragraphs for a problem."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    mapping_result = await session.execute(
        select(ProblemParagraphMapping).where(
            ProblemParagraphMapping.knowledge_id == knowledge_id,
            ProblemParagraphMapping.problem_id == problem_id,
        )
    )
    mappings = mapping_result.scalars().all()
    if not mappings:
        return []

    paragraph_ids = [m.paragraph_id for m in mappings]
    para_result = await session.execute(
        select(Paragraph).where(Paragraph.id.in_(paragraph_ids))
    )
    paragraphs = {p.id: p for p in para_result.scalars().all()}

    return [
        ProblemParagraphOut(
            id=p.id,
            document_id=p.document_id,
            knowledge_id=p.knowledge_id,
            content=p.content,
            title=p.title,
            status=p.status,
            hit_num=p.hit_num,
            is_active=p.is_active,
            position=p.position,
            create_time=p.create_time,
            update_time=p.update_time,
        )
        for m in mappings
        if (p := paragraphs.get(m.paragraph_id))
    ]


@router.put("/{knowledge_id}/problem/{problem_id}")
async def update_problem(
    knowledge_id: str,
    problem_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Update a single problem's content."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    problem = await session.get(Problem, problem_id)
    if problem is None or str(problem.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    if "content" in body:
        problem.content = body["content"]
    await session.commit()
    return {"result": True}


@router.delete("/{knowledge_id}/problem/{problem_id}")
async def delete_problem(
    knowledge_id: str,
    problem_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Delete a single problem and its paragraph mappings."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    problem = await session.get(Problem, problem_id)
    if problem is None or str(problem.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    # Delete mappings first
    mapping_result = await session.execute(
        select(ProblemParagraphMapping).where(
            ProblemParagraphMapping.knowledge_id == knowledge_id,
            ProblemParagraphMapping.problem_id == problem_id,
        )
    )
    for m in mapping_result.scalars().all():
        await session.delete(m)

    await session.delete(problem)
    await session.commit()
    return {"result": True}


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


@router.api_route("/{knowledge_id}/document/batch_create", methods=["POST", "PUT"])
async def batch_create_documents(
    knowledge_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Batch create documents from pre-split paragraphs and make them searchable.

    The frontend has already split each document into paragraphs
    (``[{title, content}]``). We persist a ``Document`` plus one ``Paragraph``
    row per segment (preserving the provided title/content — no re-splitting),
    then embed them so the knowledge base becomes retrievable. Embedding runs
    asynchronously via arq when a worker/redis is available, with a synchronous
    inline fallback so it still works in a single-process dev setup (链路 A).
    """
    from app.core.tasks import enqueue_ingest_paragraphs
    from app.rag.pipeline import embed_paragraphs

    body = await request.json()
    if not isinstance(body, list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Body must be a list")

    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")

    # Resolve the embedding model: prefer the KB's configured model, else the
    # first available embedding model in the database.
    embedding_model_row = None
    if knowledge.embedding_model_id is not None:
        candidate = await session.get(Model, knowledge.embedding_model_id)
        if candidate is not None and candidate.model_type == "embedding":
            embedding_model_row = candidate
    if embedding_model_row is None:
        emb_result = await session.execute(select(Model).where(Model.model_type == "embedding").limit(1))
        embedding_model_row = emb_result.scalar_one_or_none()

    embedding = None
    if embedding_model_row is not None and embedding_model_row.model_type == "embedding":
        embedding = {
            "provider": embedding_model_row.provider,
            "model_name": embedding_model_row.model_name,
            "credential": resolve_credential(embedding_model_row.credential),
            "dimensions": (embedding_model_row.meta or {}).get("dimensions"),
        }

    created: list[str] = []
    pending: list[tuple[str, str | None]] = []  # (document_id, user_id)
    for item in body:
        name = item.get("name", "document")
        paragraphs = item.get("paragraphs", []) or []
        doc = Document(
            knowledge_id=knowledge_id,
            name=name,
            type=knowledge.type,
            status="PENDING" if embedding is not None else "SUCCESS",
            user_id=current_user.id,
            meta={"paragraphs": paragraphs, "paragraph_count": len(paragraphs)},
        )
        session.add(doc)
        await session.flush()

        for idx, para in enumerate(paragraphs):
            session.add(
                Paragraph(
                    knowledge_id=knowledge_id,
                    document_id=doc.id,
                    content=para.get("content", ""),
                    title=(para.get("title") or "")[0:256],
                    position=idx + 1,
                    is_active=True,
                )
            )

        created.append(str(doc.id))
        if embedding is not None:
            pending.append((str(doc.id), str(current_user.id) if current_user.id is not None else None))

    await session.commit()

    # Embed: prefer arq (async); fall back to inline so it works without a worker.
    for document_id, user_id in pending:
        if embedding is None:
            break
        enqueued = False
        try:
            await enqueue_ingest_paragraphs(
                knowledge_id=str(knowledge_id),
                document_id=document_id,
                user_id=user_id,
                embedding=embedding,
            )
            enqueued = True
        except Exception:
            enqueued = False
        if enqueued:
            continue

        # Inline fallback (no arq worker / redis unavailable).
        try:
            result = await embed_paragraphs(
                session,
                knowledge_id=str(knowledge_id),
                document_id=document_id,
                embedding=embedding,
            )
            doc = await session.get(Document, document_id)
            if doc is not None:
                doc.status = "SUCCESS"
                doc.status_meta = {
                    "step": "completed",
                    "paragraph_count": result.paragraph_count,
                    "embedding_count": result.embedding_count,
                    "char_length": result.char_length,
                }
                await session.commit()
        except Exception as exc:
            doc = await session.get(Document, document_id)
            if doc is not None:
                doc.status = "ERROR"
                doc.status_meta = {"step": "error", "error": str(exc)[:500]}
                await session.commit()

    return {"result": True, "document_ids": created, "count": len(created)}


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


@router.post("/{knowledge_id}/document/{document_id}/upload")
async def upload_document_file(
    knowledge_id: str,
    document_id: str,
    file: UploadFile = File(...),
    with_filter: bool = Form(False),
    limit: int = Form(4096),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload a source file and enqueue it for asynchronous ingestion.

    The document must already exist (created via ``POST .../document``). The
    file bytes are sent to the arq worker, which parses/splits/embeds and writes
    paragraph + embedding rows. ``Document.status`` tracks progress:
    ``PENDING`` -> ``INGESTING`` -> ``SUCCESS`` | ``ERROR``.
    """
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")
    if knowledge.embedding_model_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No embedding model configured")

    document = await session.get(Document, document_id)
    if document is None or str(document.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    embedding_model_row = await session.get(Model, knowledge.embedding_model_id)
    if embedding_model_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Embedding model not found")
    if embedding_model_row.model_type != "embedding":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Configured model is not an embedding model"
        )

    embedding = {
        "provider": embedding_model_row.provider,
        "model_name": embedding_model_row.model_name,
        "credential": resolve_credential(embedding_model_row.credential),
        "dimensions": (embedding_model_row.meta or {}).get("dimensions"),
    }

    document.name = file.filename or document.name
    document.status = "PENDING"
    document.status_meta = {"step": "queued", "filename": file.filename}
    await session.commit()

    content = await file.read()
    await enqueue_ingest(
        knowledge_id=str(knowledge_id),
        document_id=str(document_id),
        user_id=str(current_user.id) if current_user.id is not None else None,
        filename=file.filename or "document",
        content=content,
        embedding=embedding,
        with_filter=with_filter,
        limit=limit,
    )

    return {"result": True, "document_id": str(document_id), "status": "PENDING"}


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
    files: list[UploadFile] = File(...),
    patterns: str = Form("[]"),
    limit: int = Form(4096),
    with_filter: bool = Form(True),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """Split preview: upload file(s) and return a paragraph preview array.

    Mirrors the legacy Django ``DocumentView.Split`` response shape so the
    (Vue) admin frontend renders correctly:

    * one item **per uploaded file** (not per paragraph);
    * each item keeps the original file ``name``;
    * ``content`` is the full list of ``{title, content}`` paragraphs
      produced by MaxKB's structure-aware splitter (markdown heading /
      blank-line regex + smart length splitting);
    * ``source_file_id`` is returned for downstream ``batch_create`` parity.

    Accepts an optional ``patterns`` JSON array of custom regexes; when empty
    the splitter falls back to the md / default pattern table (same logic as
    the legacy backend).
    """
    import json

    from uuid import uuid4

    from app.rag.splitter import SplitModel, get_split_model

    # Parse optional custom split patterns (legacy passes a JSON list of regexes).
    custom_patterns: list[str] = []
    try:
        parsed = json.loads(patterns)
        if isinstance(parsed, list):
            custom_patterns = [p for p in parsed if isinstance(p, str) and p.strip()]
    except Exception:
        custom_patterns = []

    preview: list[dict] = []
    for file in files:
        content = await file.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("utf-8", errors="replace")

        if custom_patterns:
            split_model = SplitModel(custom_patterns, with_filter=with_filter, limit=limit)
        else:
            split_model = get_split_model(file.filename or "document", with_filter=with_filter, limit=limit)

        paragraphs = split_model.parse(text)
        preview.append(
            {
                "name": file.filename or "document",
                "content": paragraphs,
                "source_file_id": str(uuid4()),
            }
        )
    return preview


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


# ---------------------------------------------------------------------------
# Generic single-document routes (MUST be registered LAST so constant-segment
# routes like `document/batch_create`, `document/batch_delete`, `document/migrate/{id}`,
# `document/web` are matched first and not shadowed by the `{document_id}` param).
# ---------------------------------------------------------------------------


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
# Helpers
# ---------------------------------------------------------------------------


def _problem_to_out(problem, paragraph_count: int = 0) -> ProblemOut:
    """Convert a Problem ORM instance to ProblemOut with paragraph_count."""
    return ProblemOut(
        id=problem.id,
        knowledge_id=problem.knowledge_id,
        content=problem.content,
        hit_num=getattr(problem, "hit_num", 0),
        paragraph_count=paragraph_count,
        create_time=problem.create_time,
        update_time=problem.update_time,
    )
