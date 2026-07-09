"""Application (agent) API + chat streaming endpoint.

The Agno ``ChatAgent`` is imported lazily inside the chat endpoint so the rest
of the app imports cleanly even before ``agno`` is installed in the venv.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user
from app.models.application import Application, ApplicationKnowledgeMapping
from app.models.models_provider import Model
from app.models.user import User
from app.schemas.application import ApplicationOut, ApplicationPage, ChatRequest

router = APIRouter(prefix="/api/application", tags=["application"])


@router.get("", response_model=ApplicationPage)
async def list_applications(
    page: int = 1,
    size: int = 10,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ApplicationPage:
    total = await session.scalar(select(func.count()).select_from(Application))
    result = await session.execute(
        select(Application).order_by(Application.create_time.desc()).offset((page - 1) * size).limit(size)
    )
    rows = result.scalars().all()
    return ApplicationPage(list=[ApplicationOut.model_validate(a) for a in rows], total=total or 0)


@router.get("/{application_id}", response_model=ApplicationOut)
async def get_application(
    application_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ApplicationOut:
    application = await session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return ApplicationOut.model_validate(application)


def _embedding_dict(model: Model | None) -> dict | None:
    if model is None:
        return None
    return {
        "provider": model.provider,
        "model_name": model.model_name,
        "credential": model.credential,
        "dimensions": (model.meta or {}).get("dimensions"),
    }


@router.post("/{application_id}/chat")
async def chat(
    application_id: str,
    body: ChatRequest,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    application = await session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    model_row = await session.get(Model, application.model_id) if application.model_id else None
    embedding_model_row = (
        await session.get(Model, application.embedding_model_id) if application.embedding_model_id else None
    )
    if model_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application has no chat model configured")

    knowledge_ids = body.knowledge_ids
    if not knowledge_ids:
        mapping = await session.execute(
            select(ApplicationKnowledgeMapping.knowledge_id).where(
                ApplicationKnowledgeMapping.application_id == application_id
            )
        )
        knowledge_ids = [str(k) for k in mapping.scalars().all()]

    embedding = body.embedding or _embedding_dict(embedding_model_row)

    # Lazy import so agno is only required when actually chatting.
    from app.agents.chat_agent import ChatAgent

    agent = ChatAgent(
        model_provider=model_row.provider,
        model_name=model_row.model_name,
        credential=model_row.credential,
        knowledge_ids=knowledge_ids,
        embedding=embedding,
        top_n=body.top_n,
        similarity=body.similarity,
        search_mode=body.search_mode,
    )

    async def event_source():
        try:
            async for frame in agent.stream(body.message, session_id=body.session_id):
                yield frame
        except Exception as exc:  # surface errors as an SSE event
            yield "data: " + json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")
