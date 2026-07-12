"""Chat API — anonymous auth, messaging, conversations."""

from __future__ import annotations

import json
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import create_access_token
from app.models.application import (
    Application,
    ApplicationAccessToken,
    ApplicationKnowledgeMapping,
    Chat,
    ChatRecord,
)
from app.models.models_provider import Model
from app.models.system import ChatUser
from app.schemas.chat import (
    AnonymousAuthRequest,
    ApplicationProfileOut,
    ChatMessageRequest,
    ChatOut,
    ChatPage,
    ChatRecordOut,
    ChatRecordPage,
    EditAbstractRequest,
    TokenResponse,
    VoteRequest,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Anonymous authentication
# ---------------------------------------------------------------------------


@router.post("/auth/anonymous", response_model=TokenResponse)
async def anonymous_auth(
    body: AnonymousAuthRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    # Look up the application access token
    result = await session.execute(
        select(ApplicationAccessToken).where(
            ApplicationAccessToken.access_token == body.access_token,
            ApplicationAccessToken.is_active == True,  # noqa: E712
        )
    )
    access_token_row = result.scalar_one_or_none()
    if access_token_row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid access token",
        )

    # Create or find anonymous chat user
    anon_username = f"anon_{secrets.token_hex(8)}"
    chat_user = ChatUser(
        username=anon_username,
        nick_name="游客",
        source="ANONYMOUS",
        is_active=True,
    )
    session.add(chat_user)
    await session.flush()

    # Create JWT token with chat user context
    token_data = {
        "sub": str(chat_user.id),
        "application_id": str(access_token_row.application_id),
        "chat_user_type": "ANONYMOUS_USER",
        "source": "ANONYMOUS",
    }
    token = create_access_token(token_data)

    await session.commit()
    return TokenResponse(access_token=token)


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


@router.get("/profile")
async def auth_profile(
    token: str = Query(..., alias="access_token"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return application authentication profile for the chat widget."""
    result = await session.execute(
        select(ApplicationAccessToken).where(
            ApplicationAccessToken.access_token == token,
            ApplicationAccessToken.is_active == True,  # noqa: E712
        )
    )
    access_token_row = result.scalar_one_or_none()
    if access_token_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

    application = await session.get(Application, access_token_row.application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    return {
        "id": str(application.id),
        "name": application.name,
        "icon": application.icon,
        "authentication": access_token_row.authentication,
        "authentication_value": access_token_row.authentication_value,
        "show_source": access_token_row.show_source,
    }


@router.get("/application/profile", response_model=ApplicationProfileOut)
async def application_profile(
    token: str = Query(..., alias="access_token"),
    session: AsyncSession = Depends(get_session),
) -> ApplicationProfileOut:
    result = await session.execute(
        select(ApplicationAccessToken).where(
            ApplicationAccessToken.access_token == token,
            ApplicationAccessToken.is_active == True,  # noqa: E712
        )
    )
    access_token_row = result.scalar_one_or_none()
    if access_token_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

    application = await session.get(Application, access_token_row.application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    return ApplicationProfileOut(
        id=application.id,
        name=application.name,
        desc=application.desc,
        icon=application.icon,
        prologue=application.prologue,
        type=application.type,
        is_publish=application.is_publish,
        work_flow=application.work_flow,
        tts_model_enable=application.tts_model_enable,
        tts_type=application.tts_type,
        tts_autoplay=application.tts_autoplay,
        stt_model_enable=application.stt_model_enable,
        stt_autosend=application.stt_autosend,
        file_upload_enable=application.file_upload_enable,
        file_upload_setting=application.file_upload_setting,
        show_source=access_token_row.show_source,
        authentication=access_token_row.authentication,
        authentication_value=access_token_row.authentication_value,
    )


# ---------------------------------------------------------------------------
# Chat sessions
# ---------------------------------------------------------------------------


@router.get("/open", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
async def open_chat(
    token: str = Query(..., alias="access_token"),
    session: AsyncSession = Depends(get_session),
) -> ChatOut:
    result = await session.execute(
        select(ApplicationAccessToken).where(
            ApplicationAccessToken.access_token == token,
            ApplicationAccessToken.is_active == True,  # noqa: E712
        )
    )
    access_token_row = result.scalar_one_or_none()
    if access_token_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid access token")

    chat = Chat(
        application_id=access_token_row.application_id,
        abstract="新对话",
        chat_user_type="ANONYMOUS_USER",
    )
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return ChatOut.model_validate(chat)


# ---------------------------------------------------------------------------
# Chat messages (streaming)
# ---------------------------------------------------------------------------


def _embedding_dict(model: Model | None) -> dict | None:
    if model is None:
        return None
    return {
        "provider": model.provider,
        "model_name": model.model_name,
        "credential": model.credential,
        "dimensions": (model.meta or {}).get("dimensions"),
    }


@router.post("/chat_message/{chat_id}")
async def chat_message(
    chat_id: str,
    body: ChatMessageRequest,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    chat = await session.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    application = await session.get(Application, chat.application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if body.stream and application.type == "SIMPLE":
        return await _chat_simple_stream(application, body, chat, session)

    # Non-streaming or workflow: return JSON
    # For now, default to simple streaming
    return await _chat_simple_stream(application, body, chat, session)


async def _chat_simple_stream(
    application: Application,
    body: ChatMessageRequest,
    chat: Chat,
    session: AsyncSession,
) -> StreamingResponse:
    model_row = await session.get(Model, application.model_id) if application.model_id else None
    if model_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No chat model configured")

    embedding_model_row = (
        await session.get(Model, application.knowledge_setting.get("embedding_model_id"))
        if application.knowledge_setting and application.knowledge_setting.get("embedding_model_id")
        else None
    )

    knowledge_ids = []
    mapping = await session.execute(
        select(ApplicationKnowledgeMapping.knowledge_id).where(
            ApplicationKnowledgeMapping.application_id == application.id
        )
    )
    knowledge_ids = [str(k) for k in mapping.scalars().all()]

    from app.agents.chat_agent import ChatAgent

    agent = ChatAgent(
        model_provider=model_row.provider,
        model_name=model_row.model_name,
        credential=model_row.credential,
        knowledge_ids=knowledge_ids,
        embedding=_embedding_dict(embedding_model_row),
        top_n=(application.knowledge_setting or {}).get("top_n", 5),
        similarity=(application.knowledge_setting or {}).get("similarity", 0.5),
        search_mode=(application.knowledge_setting or {}).get("search_mode", "embedding"),
    )

    async def event_source():
        full_answer = ""
        try:
            async for frame in agent.stream(body.message, session_id=str(chat.id)):
                full_answer += frame
                yield frame
        except Exception as exc:
            yield "data: " + json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n\n"
        finally:
            # Persist chat record
            record = ChatRecord(
                chat_id=chat.id,
                problem_text=body.message,
                answer_text=full_answer.replace("data: ", "").replace("\n\n", ""),
                message_tokens=len(body.message),
                answer_tokens=len(full_answer),
                index=chat.chat_record_count + 1,
                vote_status="-1",
            )
            session.add(record)
            chat.chat_record_count = chat.chat_record_count + 1
            # Update abstract from first message
            if chat.abstract == "新对话":
                chat.abstract = body.message[:50]
            await session.commit()

    return StreamingResponse(event_source(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Historical conversations
# ---------------------------------------------------------------------------


@router.get("/historical_conversation", response_model=ChatPage)
async def list_conversations(
    token: str = Query(..., alias="access_token"),
    page: int = 1,
    size: int = 10,
    session: AsyncSession = Depends(get_session),
) -> ChatPage:
    result = await session.execute(
        select(ApplicationAccessToken).where(
            ApplicationAccessToken.access_token == token,
            ApplicationAccessToken.is_active == True,  # noqa: E712
        )
    )
    access_token_row = result.scalar_one_or_none()
    if access_token_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid access token")

    conditions = [
        Chat.application_id == access_token_row.application_id,
        Chat.is_deleted == False,  # noqa: E712
    ]

    total = await session.scalar(select(func.count()).select_from(Chat).where(*conditions))
    result = await session.execute(
        select(Chat).where(*conditions).order_by(Chat.create_time.desc()).offset((page - 1) * size).limit(size)
    )
    rows = result.scalars().all()
    return ChatPage(list=[ChatOut.model_validate(r) for r in rows], total=total or 0)


@router.get("/historical_conversation_record/{chat_id}", response_model=ChatRecordPage)
async def list_chat_records(
    chat_id: str,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_session),
) -> ChatRecordPage:
    chat = await session.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    total = await session.scalar(select(func.count()).select_from(ChatRecord).where(ChatRecord.chat_id == chat_id))
    result = await session.execute(
        select(ChatRecord)
        .where(ChatRecord.chat_id == chat_id)
        .order_by(ChatRecord.create_time.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = result.scalars().all()
    return ChatRecordPage(
        list=[ChatRecordOut.model_validate(r) for r in rows],
        total=total or 0,
    )


# ---------------------------------------------------------------------------
# Delete conversation
# ---------------------------------------------------------------------------


@router.delete("/historical_conversation/{chat_id}")
async def delete_conversation(
    chat_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    chat = await session.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    chat.is_deleted = True
    await session.commit()
    return {"result": True}


# ---------------------------------------------------------------------------
# Vote
# ---------------------------------------------------------------------------


@router.put("/vote/chat/{chat_id}/chat_record/{record_id}")
async def vote_chat_record(
    chat_id: str,
    record_id: str,
    body: VoteRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    record = await session.get(ChatRecord, record_id)
    if record is None or str(record.chat_id) != chat_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat record not found")

    record.vote_status = body.vote_status
    if body.vote_reason is not None:
        record.vote_reason = body.vote_reason
    if body.vote_other_content:
        record.vote_other_content = body.vote_other_content

    await session.commit()
    return {"result": True}


# ---------------------------------------------------------------------------
# Edit abstract
# ---------------------------------------------------------------------------


@router.put("/historical_conversation/{chat_id}")
async def edit_abstract(
    chat_id: str,
    body: EditAbstractRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    chat = await session.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    chat.abstract = body.abstract
    await session.commit()
    return {"result": True}


# ---------------------------------------------------------------------------
# OpenAI-compatible completions (for published apps)
# ---------------------------------------------------------------------------


@router.post("/{application_id}/chat/completions")
async def chat_completions(
    application_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    application = await session.get(Application, application_id)
    if application is None or not application.is_publish:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    messages = body.get("messages", [])
    user_message = messages[-1].get("content", "") if messages else ""

    model_row = await session.get(Model, application.model_id) if application.model_id else None
    if model_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No chat model configured")

    knowledge_ids = []
    mapping = await session.execute(
        select(ApplicationKnowledgeMapping.knowledge_id).where(
            ApplicationKnowledgeMapping.application_id == application.id
        )
    )
    knowledge_ids = [str(k) for k in mapping.scalars().all()]

    from app.agents.chat_agent import ChatAgent

    agent = ChatAgent(
        model_provider=model_row.provider,
        model_name=model_row.model_name,
        credential=model_row.credential,
        knowledge_ids=knowledge_ids,
        embedding=None,
        top_n=(application.knowledge_setting or {}).get("top_n", 5),
        similarity=(application.knowledge_setting or {}).get("similarity", 0.5),
        search_mode=(application.knowledge_setting or {}).get("search_mode", "embedding"),
    )

    async def event_source():
        try:
            async for frame in agent.stream(user_message):
                yield frame
        except Exception as exc:
            yield json.dumps({"error": str(exc)}) + "\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# TTS / STT (placeholder — requires model provider integration)
# ---------------------------------------------------------------------------


@router.post("/text_to_speech")
async def text_to_speech(body: dict) -> dict:
    return {"result": True, "message": "TTS endpoint ready"}


@router.post("/speech_to_text")
async def speech_to_text(body: dict) -> dict:
    return {"result": True, "message": "STT endpoint ready"}


# ---------------------------------------------------------------------------
# Captcha
# ---------------------------------------------------------------------------


@router.get("/captcha")
async def captcha(username: str = "", access_token: str = "") -> dict:
    import base64
    import secrets

    key = secrets.token_hex(16)
    return {"key": key, "image": base64.b64encode(b"captcha-placeholder").decode()}
