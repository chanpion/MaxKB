"""Homepage / Dashboard API — aggregations and rankings."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user
from app.models.application import Application, Chat, ChatRecord
from app.models.knowledge import Document, Knowledge
from app.models.models_provider import Model
from app.models.tool import Tool
from app.models.user import User

router = APIRouter(prefix="/api/homepage", tags=["homepage"])


# ---------------------------------------------------------------------------
# Summary dashboard
# ---------------------------------------------------------------------------


@router.get("")
async def dashboard(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    app_count = await session.scalar(select(func.count()).select_from(Application)) or 0
    kb_count = await session.scalar(select(func.count()).select_from(Knowledge)) or 0
    tool_count = await session.scalar(select(func.count()).select_from(Tool)) or 0
    model_count = await session.scalar(select(func.count()).select_from(Model)) or 0
    chat_count = (
        await session.scalar(
            select(func.count()).select_from(Chat).where(Chat.is_deleted == False)  # noqa: E712
        )
        or 0
    )
    record_count = await session.scalar(select(func.count()).select_from(ChatRecord)) or 0
    doc_count = await session.scalar(select(func.count()).select_from(Document)) or 0

    return {
        "application_count": app_count,
        "knowledge_count": kb_count,
        "tool_count": tool_count,
        "model_count": model_count,
        "chat_count": chat_count,
        "chat_record_count": record_count,
        "document_count": doc_count,
    }


# ---------------------------------------------------------------------------
# Aggregations
# ---------------------------------------------------------------------------


@router.get("/application/aggregation")
async def application_aggregation(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    total = await session.scalar(select(func.count()).select_from(Application)) or 0
    return {"count": total}


@router.get("/knowledge/aggregation")
async def knowledge_aggregation(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    total = await session.scalar(select(func.count()).select_from(Knowledge)) or 0
    return {"count": total}


@router.get("/tool/aggregation")
async def tool_aggregation(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    total = await session.scalar(select(func.count()).select_from(Tool)) or 0
    return {"count": total}


@router.get("/model/aggregation")
async def model_aggregation(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    total = await session.scalar(select(func.count()).select_from(Model)) or 0
    return {"count": total}


@router.get("/chat_record/aggregation")
async def chat_record_aggregation(
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    conditions = []
    if start_time:
        conditions.append(ChatRecord.create_time >= datetime.fromisoformat(start_time))
    if end_time:
        conditions.append(ChatRecord.create_time <= datetime.fromisoformat(end_time))
    total = await session.scalar(select(func.count()).select_from(ChatRecord).where(*conditions)) or 0
    return {"count": total, "list": []}


@router.get("/tokens/aggregation")
async def tokens_aggregation(
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    conditions = []
    if start_time:
        conditions.append(ChatRecord.create_time >= datetime.fromisoformat(start_time))
    if end_time:
        conditions.append(ChatRecord.create_time <= datetime.fromisoformat(end_time))
    total_tokens = (
        await session.scalar(
            select(func.coalesce(func.sum(ChatRecord.message_tokens), 0)).select_from(ChatRecord).where(*conditions)
        )
        or 0
    )
    answer_tokens = (
        await session.scalar(
            select(func.coalesce(func.sum(ChatRecord.answer_tokens), 0)).select_from(ChatRecord).where(*conditions)
        )
        or 0
    )
    return {
        "message_tokens": total_tokens,
        "answer_tokens": answer_tokens,
        "total_tokens": total_tokens + answer_tokens,
    }


@router.get("/monitoring/aggregation")
async def monitoring_aggregation(
    application_id: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list:
    return []


# ---------------------------------------------------------------------------
# Rankings (path-based pagination: /{page}/{page_size})
# ---------------------------------------------------------------------------


def _empty_page(page: int, size: int) -> dict:
    return {"list": [], "total": 0, "page": page, "page_size": size}


@router.get("/application/tokens_ranking/{page}/{page_size}")
async def tokens_ranking(
    page: int,
    page_size: int,
    name: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    return _empty_page(page, page_size)


@router.get("/application/question_ranking/{page}/{page_size}")
async def question_ranking(
    page: int,
    page_size: int,
    name: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    return _empty_page(page, page_size)


@router.get("/application/user_tokens_ranking/{page}/{page_size}")
async def user_tokens_ranking(
    page: int,
    page_size: int,
    name: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    return _empty_page(page, page_size)


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------


@router.get("/tokens_ranking/export")
async def export_tokens_ranking(
    name: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    _: User = Depends(get_current_user),
) -> dict:
    return {"list": [], "total": 0}


@router.get("/question_ranking/export")
async def export_question_ranking(
    name: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    _: User = Depends(get_current_user),
) -> dict:
    return {"list": [], "total": 0}


@router.get("/user_tokens_ranking/export")
async def export_user_tokens_ranking(
    name: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    _: User = Depends(get_current_user),
) -> dict:
    return {"list": [], "total": 0}
