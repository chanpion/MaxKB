"""Application (agent) API — CRUD, publish, chat streaming endpoint."""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, time, timedelta
from typing import Any

import uuid_utils.compat as uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.folder_tree import build_folder_tree
from app.core.db import get_session
from app.core.security import get_current_user
from app.models.application import (
    Application,
    ApplicationAccessToken,
    ApplicationApiKey,
    ApplicationFolder,
    ApplicationKnowledgeMapping,
    ApplicationVersion,
    Chat,
)
from app.models.models_provider import Model
from app.models.user import User
from app.providers.base import resolve_credential
from app.schemas.application import (
    AccessTokenOut,
    AccessTokenUpdate,
    ApiKeyCreate,
    ApiKeyOut,
    ApplicationCreate,
    ApplicationOut,
    ApplicationPage,
    ApplicationStatsOut,
    ApplicationUpdate,
    ApplicationVersionOut,
    ChatRequest,
)

router = APIRouter(prefix="/api/application", tags=["application"])


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ApplicationOut])
async def list_applications(
    workspace_id: str | None = None,
    name: str | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[ApplicationOut]:
    conditions = []
    if workspace_id:
        conditions.append(Application.workspace_id == workspace_id)
    if name:
        conditions.append(Application.name.ilike(f"%{name}%"))
    result = await session.execute(select(Application).where(*conditions).order_by(Application.create_time.desc()))
    return [ApplicationOut.model_validate(a) for a in result.scalars().all()]


# ---------------------------------------------------------------------------
# Application Folders (MUST come before /{application_id})
# ---------------------------------------------------------------------------


@router.get("/folder", response_model=list[dict])
async def list_application_folders(
    workspace_id: str = "default",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """Folder tree for the application page sidebar.

    Returns a single tree rooted at a synthetic ``根目录`` node (id == workspace
    id) with the real folders nested underneath, matching the Django backend.
    """
    result = await session.execute(
        select(ApplicationFolder).where(ApplicationFolder.workspace_id == workspace_id).order_by(ApplicationFolder.lft)
    )
    return build_folder_tree(result.scalars().all(), workspace_id)


@router.post("/folder", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_application_folder(
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    folder = ApplicationFolder(
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


@router.post("/{application_id}/open", response_model=dict)
async def open_application(
    application_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Open an application — create a fresh debug chat session for it.

    Mirrors Django ``application/<id>/open`` which returns a temporary
    ``chat_user_id`` for the debug/embedded chat panel. We create a ``Chat``
    row (the backend's session object) so the frontend can immediately start a
    conversation against the application.
    """
    application = await session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    chat = Chat(
        application_id=application.id,
        abstract="新对话",
        chat_user_type="ANONYMOUS_USER",
    )
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return {
        "id": str(chat.id),
        "application_id": str(application.id),
        "chat_user_id": str(chat.id),
        "chat_user_type": "ANONYMOUS_USER",
        "debug": True,
    }


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(
    body: ApplicationCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ApplicationOut:
    data = body.model_dump()
    knowledge_ids: list = data.pop("knowledge_id_list", []) or []

    application = Application(
        **data,
        user_id=current_user.id,
        workspace_id="default",
    )
    session.add(application)
    await session.flush()

    # Link knowledge bases (SIMPLE type)
    for kid in knowledge_ids:
        session.add(ApplicationKnowledgeMapping(application_id=application.id, knowledge_id=kid))

    await session.commit()
    await session.refresh(application)
    return ApplicationOut.model_validate(application)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@router.put("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: str,
    body: ApplicationUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ApplicationOut:
    application = await session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    update_data = body.model_dump(exclude_unset=True)
    knowledge_ids: list | None = update_data.pop("knowledge_id_list", None)

    for field, value in update_data.items():
        setattr(application, field, value)

    # Re-sync knowledge base mappings if provided
    if knowledge_ids is not None:
        existing = await session.execute(
            select(ApplicationKnowledgeMapping).where(ApplicationKnowledgeMapping.application_id == application.id)
        )
        for m in existing.scalars().all():
            await session.delete(m)
        for kid in knowledge_ids:
            session.add(ApplicationKnowledgeMapping(application_id=application.id, knowledge_id=kid))

    await session.commit()
    await session.refresh(application)
    return ApplicationOut.model_validate(application)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_application(
    application_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    application = await session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    await session.delete(application)
    await session.commit()


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------


@router.put("/{application_id}/publish", response_model=ApplicationOut)
async def publish_application(
    application_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ApplicationOut:
    application = await session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    now = datetime.now()
    application.is_publish = True
    application.publish_time = now

    # Create a version snapshot
    version_name = now.strftime("%Y-%m-%d %H:%M:%S")
    version = ApplicationVersion(
        application_id=application.id,
        workspace_id=application.workspace_id,
        application_name=application.name,
        name=version_name,
        publish_user_id=current_user.id,
        publish_user_name=current_user.username,
        user_id=current_user.id,
        desc=application.desc,
        prologue=application.prologue,
        dialogue_number=application.dialogue_number,
        model_id=application.model_id,
        knowledge_setting=application.knowledge_setting,
        model_setting=application.model_setting,
        model_params_setting=application.model_params_setting,
        problem_optimization=application.problem_optimization,
        icon=application.icon,
        work_flow=application.work_flow,
        type=application.type,
        problem_optimization_prompt=application.problem_optimization_prompt,
        tts_model_id=application.tts_model_id,
        stt_model_id=application.stt_model_id,
        tts_model_enable=application.tts_model_enable,
        stt_model_enable=application.stt_model_enable,
        tts_type=application.tts_type,
        tts_autoplay=application.tts_autoplay,
        stt_autosend=application.stt_autosend,
        clean_time=application.clean_time,
        file_upload_enable=application.file_upload_enable,
        file_upload_setting=application.file_upload_setting,
        mcp_enable=application.mcp_enable,
        mcp_tool_ids=application.mcp_tool_ids,
        mcp_servers=application.mcp_servers,
        tool_enable=application.tool_enable,
        tool_ids=application.tool_ids,
        application_enable=application.application_enable,
        application_ids=application.application_ids,
        skill_tool_ids=application.skill_tool_ids,
        long_term_enable=application.long_term_enable,
        long_term_model_id=application.long_term_model_id,
        long_term_model_params_setting=application.long_term_model_params_setting,
        long_term_trigger_type=application.long_term_trigger_type,
        long_term_trigger_setting=application.long_term_trigger_setting,
    )
    session.add(version)

    # Ensure access token exists
    token_result = await session.execute(
        select(ApplicationAccessToken).where(ApplicationAccessToken.application_id == application.id)
    )
    if token_result.scalar_one_or_none() is None:
        import hashlib

        token_str = hashlib.md5(str(application.id).encode()).hexdigest()[8:24]
        session.add(
            ApplicationAccessToken(
                application_id=application.id,
                access_token=token_str,
            )
        )

    await session.commit()
    await session.refresh(application)
    return ApplicationOut.model_validate(application)


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------


@router.get("/{application_id}/application_key", response_model=list[ApiKeyOut])
async def list_api_keys(
    application_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[ApiKeyOut]:
    result = await session.execute(select(ApplicationApiKey).where(ApplicationApiKey.application_id == application_id))
    return [ApiKeyOut.model_validate(k) for k in result.scalars().all()]


@router.post("/{application_id}/application_key", response_model=ApiKeyOut, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    application_id: str,
    body: ApiKeyCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ApiKeyOut:
    secret = "sk-" + secrets.token_hex(24)
    key = ApplicationApiKey(
        application_id=application_id,
        secret_key=secret,
        workspace_id="default",
        is_active=body.is_active,
        allow_cross_domain=body.allow_cross_domain,
        cross_domain_list=body.cross_domain_list,
        is_permanent=body.is_permanent,
    )
    session.add(key)
    await session.commit()
    await session.refresh(key)
    return ApiKeyOut.model_validate(key)


@router.delete("/{application_id}/application_key/{key_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_api_key(
    application_id: str,
    key_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    key = await session.get(ApplicationApiKey, key_id)
    if key is None or str(key.application_id) != application_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    await session.delete(key)
    await session.commit()


# ---------------------------------------------------------------------------
# Access Token
# ---------------------------------------------------------------------------


@router.get("/{application_id}/access_token", response_model=AccessTokenOut)
async def get_access_token(
    application_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> AccessTokenOut:
    result = await session.execute(
        select(ApplicationAccessToken).where(ApplicationAccessToken.application_id == application_id)
    )
    token = result.scalar_one_or_none()
    if token is None:
        # 对齐旧版 Django：发布应用时若不存在则自动创建访问令牌
        token = ApplicationAccessToken(
            application_id=application_id,
            access_token=hashlib.md5(str(uuid.uuid7()).encode()).hexdigest()[8:24],
            is_active=True,
        )
        session.add(token)
        await session.commit()
        await session.refresh(token)
    return AccessTokenOut.model_validate(token)


@router.put("/{application_id}/access_token", response_model=AccessTokenOut)
async def update_access_token(
    application_id: str,
    body: AccessTokenUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> AccessTokenOut:
    result = await session.execute(
        select(ApplicationAccessToken).where(ApplicationAccessToken.application_id == application_id)
    )
    token = result.scalar_one_or_none()
    if token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access token not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(token, field, value)

    await session.commit()
    await session.refresh(token)
    return AccessTokenOut.model_validate(token)


# ---------------------------------------------------------------------------
# Statistics — 对齐旧版 application_stats / application_token_usage / top_questions
# ---------------------------------------------------------------------------


def _resolve_time_range(start_time: str | None, end_time: str | None) -> tuple[datetime, datetime]:
    """将 %Y-%m-%d 字符串转换为当日 00:00:00 ~ 23:59:59.999999 的 datetime。"""
    if start_time:
        start = datetime.combine(datetime.strptime(start_time, "%Y-%m-%d").date(), time.min)
    else:
        start = datetime(2000, 1, 1, 0, 0, 0)
    if end_time:
        end = datetime.combine(datetime.strptime(end_time, "%Y-%m-%d").date(), time.max)
    else:
        end = datetime(2999, 12, 31, 23, 59, 59, 999999)
    return start, end


@router.get("/{application_id}/application_stats")
async def application_stats_trend(
    application_id: str,
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """按天聚合对话统计，对齐旧版 chat_record_count_trend.sql + customer_count_trend.sql。"""
    start, end = _resolve_time_range(start_time, end_time)
    chat_sql = text(
        """
        SELECT
            SUM(CASE WHEN r.vote_status = '0' THEN 1 ELSE 0 END) AS star_num,
            SUM(CASE WHEN r.vote_status = '1' THEN 1 ELSE 0 END) AS trample_num,
            SUM(r.message_tokens + r.answer_tokens) AS tokens_num,
            COUNT(r.id) AS chat_record_count,
            COUNT(DISTINCT c.chat_user_id) AS customer_num,
            r.create_time::DATE AS day
        FROM application_chat_record r
        LEFT JOIN application_chat c ON c.id = r.chat_id
        WHERE c.application_id = :app_id
          AND r.create_time >= :start
          AND r.create_time <= :end
        GROUP BY r.create_time::DATE
        """
    )
    customer_sql = text(
        """
        SELECT
            COUNT(s.id) AS customer_added_count,
            s.create_time::DATE AS day
        FROM application_chat_user_stats s
        WHERE s.application_id = :app_id
          AND s.create_time >= :start
          AND s.create_time <= :end
        GROUP BY s.create_time::DATE
        """
    )
    params = {"app_id": application_id, "start": start, "end": end}
    chat_rows = (await session.execute(chat_sql, params)).mappings().all()
    customer_rows = (await session.execute(customer_sql, params)).mappings().all()
    customer_by_day = {row["day"].strftime("%Y-%m-%d") if row["day"] else "": row for row in customer_rows}

    days = {row["day"].strftime("%Y-%m-%d") if row["day"] else "" for row in chat_rows}
    days |= set(customer_by_day.keys())
    # 补全起止区间每一天（对齐旧版 get_days_between_dates 合并逻辑）
    cur = start.date()
    while cur <= end.date():
        days.add(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)

    result = []
    for day in sorted(days):
        chat = next((r for r in chat_rows if (r["day"].strftime("%Y-%m-%d") if r["day"] else "") == day), None)
        cust = customer_by_day.get(day, {})
        result.append(
            {
                "day": day,
                "star_num": int(chat["star_num"] or 0) if chat else 0,
                "trample_num": int(chat["trample_num"] or 0) if chat else 0,
                "tokens_num": int(chat["tokens_num"] or 0) if chat else 0,
                "chat_record_count": int(chat["chat_record_count"] or 0) if chat else 0,
                "customer_num": int(chat["customer_num"] or 0) if chat else 0,
                "customer_added_count": int(cust.get("customer_added_count") or 0),
            }
        )
    return result


@router.get("/{application_id}/application_token_usage")
async def application_token_usage(
    application_id: str,
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """按用户聚合 Token 消耗排行，对齐旧版 get_token_usage.sql。"""
    start, end = _resolve_time_range(start_time, end_time)
    sql = text(
        """
        SELECT
            SUM(r.message_tokens + r.answer_tokens) AS token_usage,
            MAX(COALESCE(c.asker->>'username', '游客')) AS username
        FROM application_chat_record r
        LEFT JOIN application_chat c ON c.id = r.chat_id
        WHERE c.application_id = :app_id
          AND r.create_time >= :start
          AND r.create_time <= :end
        GROUP BY c.chat_user_id
        ORDER BY token_usage DESC
        """
    )
    rows = (await session.execute(sql, {"app_id": application_id, "start": start, "end": end})).mappings().all()
    return [{"token_usage": int(r["token_usage"] or 0), "username": r["username"]} for r in rows]


@router.get("/{application_id}/top_questions")
async def application_top_questions(
    application_id: str,
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """按用户聚合提问次数排行，对齐旧版 top_questions.sql。"""
    start, end = _resolve_time_range(start_time, end_time)
    sql = text(
        """
        SELECT
            COUNT(r.id) AS chat_record_count,
            MAX(COALESCE(c.asker->>'username', '游客')) AS username
        FROM application_chat_record r
        LEFT JOIN application_chat c ON c.id = r.chat_id
        WHERE c.application_id = :app_id
          AND r.create_time >= :start
          AND r.create_time <= :end
        GROUP BY c.chat_user_id
        ORDER BY chat_record_count DESC, username ASC
        """
    )
    rows = (await session.execute(sql, {"app_id": application_id, "start": start, "end": end})).mappings().all()
    return [{"chat_record_count": int(r["chat_record_count"] or 0), "username": r["username"]} for r in rows]


# ---------------------------------------------------------------------------
# Application Versions
# ---------------------------------------------------------------------------


@router.get("/{application_id}/application_version", response_model=list[ApplicationVersionOut])
async def list_application_versions(
    application_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[ApplicationVersionOut]:
    result = await session.execute(
        select(ApplicationVersion)
        .where(ApplicationVersion.application_id == application_id)
        .order_by(ApplicationVersion.create_time.desc())
    )
    return [ApplicationVersionOut.model_validate(v) for v in result.scalars().all()]


@router.get("/{application_id}/application_version/{version_id}", response_model=ApplicationVersionOut)
async def get_application_version(
    application_id: str,
    version_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ApplicationVersionOut:
    version = await session.get(ApplicationVersion, version_id)
    if version is None or str(version.application_id) != application_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return ApplicationVersionOut.model_validate(version)


# ---------------------------------------------------------------------------
# Application Stats
# ---------------------------------------------------------------------------


@router.get("/{application_id}/stats", response_model=ApplicationStatsOut)
async def application_stats(
    application_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ApplicationStatsOut:
    application = await session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    chat_count = (
        await session.scalar(
            select(func.count())
            .select_from(Chat)
            .where(
                Chat.application_id == application_id,
                Chat.is_deleted == False,  # noqa: E712
            )
        )
        or 0
    )

    chat_user_count = (
        await session.scalar(
            select(func.count())
            .select_from(Chat)
            .where(
                Chat.application_id == application_id,
                Chat.is_deleted == False,  # noqa: E712
            )
        )
        or 0
    )

    star_total = (
        await session.scalar(
            select(func.sum(Chat.star_num)).where(
                Chat.application_id == application_id,
                Chat.is_deleted == False,  # noqa: E712
            )
        )
        or 0
    )

    trample_total = (
        await session.scalar(
            select(func.sum(Chat.trample_num)).where(
                Chat.application_id == application_id,
                Chat.is_deleted == False,  # noqa: E712
            )
        )
        or 0
    )

    return ApplicationStatsOut(
        dialogue_number=application.dialogue_number,
        chat_count=chat_count,
        chat_user_count=chat_user_count,
        star_num=star_total,
        trample_num=trample_total,
    )


async def _resolve_embedding_config(session: AsyncSession, application: Application) -> dict[str, Any] | None:
    """Resolve the embedding model for an application.

    Legacy Django's ``Application`` has no ``embedding_model_id`` column — the
    embedding model is owned by each linked ``Knowledge`` base. Derive it from
    the first linked knowledge base (matching legacy ``search_knowledge``
    behaviour) and return a provider-ready dict (credential resolved to a dict),
    or ``None`` when no embedding model can be resolved.
    """
    from app.models.knowledge import Knowledge

    mapping = await session.execute(
        select(ApplicationKnowledgeMapping.knowledge_id)
        .where(ApplicationKnowledgeMapping.application_id == application.id)
        .limit(1)
    )
    kid = mapping.scalar_one_or_none()
    if kid is None:
        return None
    knowledge = await session.get(Knowledge, kid)
    if knowledge is None or knowledge.embedding_model_id is None:
        return None
    row = await session.get(Model, knowledge.embedding_model_id)
    if row is None:
        return None
    return {
        "provider": row.provider,
        "model_name": row.model_name,
        "credential": resolve_credential(row.credential),
        "dimensions": (row.meta or {}).get("dimensions"),
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

    if application.type == "WORK_FLOW":
        return await _chat_workflow(application, body, session)

    model_row = await session.get(Model, application.model_id) if application.model_id else None
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

    embedding = body.embedding or await _resolve_embedding_config(session, application)

    from app.agents.chat_agent import ChatAgent

    agent = ChatAgent(
        model_provider=model_row.provider,
        model_name=model_row.model_name,
        credential=resolve_credential(model_row.credential),
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
        except Exception as exc:
            yield "data: " + json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")


async def _chat_workflow(
    application: Application,
    body: ChatRequest,
    session: AsyncSession,
) -> StreamingResponse:
    """Route a ``WORK_FLOW``-type application through :class:`WorkflowEngine`.

    The application's ``work_flow`` graph is executed node-by-node. The active
    LLM / embedding credentials are resolved from the application's configured
    models and injected as ``model_config`` / ``embedding_config`` so that
    ``ai-chat`` / ``search-knowledge`` nodes can call providers without per-node
    credentials. Progress is streamed back as SSE (node_start / node_end /
    chunk / interrupted / done).
    """
    from app.workflows.engine import WorkflowEngine, sse_event

    flow = application.work_flow or {}
    if not flow.get("nodes"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application has no workflow defined")

    model_row = await session.get(Model, application.model_id) if application.model_id else None

    model_config: dict[str, Any] | None = None
    if model_row is not None:
        model_config = {
            "provider": model_row.provider,
            "model_name": model_row.model_name,
            "credential": resolve_credential(model_row.credential),
            "model_params_setting": model_row.meta or {},
        }

    embedding_config = await _resolve_embedding_config(session, application)

    # ``question`` is read by the start node; everything else becomes a global
    # variable referenceable as ``global.<key>`` inside the flow.
    params: dict[str, Any] = {"question": body.message}
    engine = WorkflowEngine(
        flow,
        params,
        model_config=model_config,
        embedding_config=embedding_config,
    )

    async def event_source():
        try:
            async for frame in engine.stream():
                yield frame
        except Exception as exc:  # propagate as an SSE error frame
            yield sse_event({"type": "error", "message": str(exc)})

    return StreamingResponse(event_source(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Legacy path-based pagination — must be last to avoid shadowing sub-routes
# ---------------------------------------------------------------------------


@router.get("/{page}/{page_size}", response_model=ApplicationPage)
async def list_applications_paginated(
    page: int,
    page_size: int,
    name: str = "",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ApplicationPage:
    """Legacy path-based pagination: ``/{page}/{page_size}``."""
    conditions = []
    if name:
        conditions.append(Application.name.ilike(f"%{name}%"))
    total = await session.scalar(select(func.count()).select_from(Application).where(*conditions))
    result = await session.execute(
        select(Application)
        .where(*conditions)
        .order_by(Application.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()
    return ApplicationPage(
        records=[ApplicationOut.model_validate(a) for a in rows],
        total=total or 0,
        current=page,
        size=page_size,
    )
