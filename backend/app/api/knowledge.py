"""Knowledge-base CRUD API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user
from app.models.knowledge import Knowledge
from app.models.user import User
from app.schemas.knowledge import KnowledgeCreate, KnowledgeOut, KnowledgePage, KnowledgeUpdate

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


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
    return KnowledgePage(list=[KnowledgeOut.model_validate(k) for k in rows], total=total or 0)


@router.post("", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
async def create_knowledge(
    body: KnowledgeCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> KnowledgeOut:
    knowledge = Knowledge(
        name=body.name,
        desc=body.desc,
        type=body.type,
        scope=body.scope,
        embedding_model_id=body.embedding_model_id,
        folder_id=body.folder_id,
        workspace_id=body.workspace_id,
        user_id=current_user.id,
        meta=body.meta,
    )
    session.add(knowledge)
    await session.commit()
    await session.refresh(knowledge)
    return KnowledgeOut.model_validate(knowledge)


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
