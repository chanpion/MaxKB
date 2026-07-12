"""Chat schemas — anonymous auth, messages, conversations."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel

# --- Auth ---


class AnonymousAuthRequest(SQLModel):
    access_token: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"


# --- Chat message ---


class ChatMessageRequest(SQLModel):
    message: str
    stream: bool = True
    re_chat: bool = False
    form_data: dict[str, Any] | None = None
    image_list: list[dict[str, Any]] = []
    document_list: list[dict[str, Any]] = []
    audio_list: list[dict[str, Any]] = []


# --- Chat session ---


class ChatOut(SQLModel):
    id: uuid.UUID
    application_id: uuid.UUID
    abstract: str = ""
    chat_user_id: str | None = None
    chat_user_type: str = "ANONYMOUS_USER"
    is_deleted: bool = False
    star_num: int = 0
    trample_num: int = 0
    chat_record_count: int = 0
    create_time: datetime | None = None
    update_time: datetime | None = None


class ChatPage(SQLModel):
    list: Any = []
    total: int = 0


ChatPage.model_rebuild()


# --- Chat record ---


class ChatRecordOut(SQLModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    vote_status: str = "-1"
    vote_reason: str | None = None
    vote_other_content: str = ""
    problem_text: str = ""
    answer_text: str = ""
    answer_text_list: list[dict[str, Any]] = []
    message_tokens: int = 0
    answer_tokens: int = 0
    details: dict[str, Any] | None = None
    run_time: float = 0.0
    index: int = 0
    create_time: datetime | None = None


class ChatRecordPage(SQLModel):
    list: Any = []
    total: int = 0


ChatRecordPage.model_rebuild()


# --- Vote ---


class VoteRequest(SQLModel):
    vote_status: str = "-1"  # -1 | 0 | 1
    vote_reason: str | None = None
    vote_other_content: str = ""


# --- Edit abstract ---


class EditAbstractRequest(SQLModel):
    abstract: str


# --- Application profile (public chat-facing) ---


class ApplicationProfileOut(SQLModel):
    id: uuid.UUID
    name: str
    desc: str = ""
    icon: str = "./favicon.ico"
    prologue: str = ""
    type: str = "SIMPLE"
    is_publish: bool = False
    work_flow: dict[str, Any] | None = None
    tts_model_enable: bool = False
    tts_type: str = "BROWSER"
    tts_autoplay: bool = False
    stt_model_enable: bool = False
    stt_autosend: bool = False
    file_upload_enable: bool = False
    file_upload_setting: dict[str, Any] | None = None
    show_source: bool = False
    authentication: bool = False
    authentication_value: dict[str, Any] | None = None
