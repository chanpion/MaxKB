"""Application (agent) + chat schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel

# --- Knowledge / Model settings (shared by create & update) ---


class NoReferencesSetting(SQLModel):
    status: str = "ai_questioning"  # ai_questioning | designated_answer
    value: str = ""


class KnowledgeSetting(SQLModel):
    top_n: float = 10.0
    similarity: float = 0.6
    max_paragraph_char_number: int = 5000
    search_mode: str = "embedding"  # embedding | keywords | blend
    no_references_setting: NoReferencesSetting = NoReferencesSetting()


class ModelSetting(SQLModel):
    prompt: str = ""
    system: str = ""
    no_references_prompt: str = ""
    reasoning_content_enable: bool = False
    reasoning_content_start: str = "<think>"
    reasoning_content_end: str = "</think>"


# --- Create ---


class ApplicationCreate(SQLModel):
    name: str
    desc: str = ""
    folder_id: str = "default"
    type: str = "SIMPLE"  # SIMPLE | WORK_FLOW
    # SIMPLE-type fields
    model_id: uuid.UUID | None = None
    dialogue_number: int = 5
    prologue: str = ""
    knowledge_id_list: list[uuid.UUID] = []
    knowledge_setting: KnowledgeSetting | None = None
    model_setting: ModelSetting | None = None
    model_params_setting: dict[str, Any] = {}
    problem_optimization: bool = False
    problem_optimization_prompt: str = ""
    tts_model_enable: bool = False
    tts_model_id: uuid.UUID | None = None
    tts_type: str = "BROWSER"
    tts_autoplay: bool = False
    stt_model_enable: bool = False
    stt_model_id: uuid.UUID | None = None
    stt_autosend: bool = False
    tts_model_params_setting: dict[str, Any] = {}
    stt_model_params_setting: dict[str, Any] = {}
    icon: str = "./favicon.ico"
    # WORK_FLOW-type fields
    work_flow: dict[str, Any] | None = None


# --- Update ---


class ApplicationUpdate(SQLModel):
    name: str | None = None
    desc: str | None = None
    folder_id: str | None = None
    type: str | None = None
    model_id: uuid.UUID | None = None
    dialogue_number: int | None = None
    prologue: str | None = None
    knowledge_id_list: list[uuid.UUID] | None = None
    knowledge_setting: KnowledgeSetting | None = None
    model_setting: ModelSetting | None = None
    model_params_setting: dict[str, Any] | None = None
    problem_optimization: bool | None = None
    problem_optimization_prompt: str | None = None
    icon: str | None = None
    work_flow: dict[str, Any] | None = None
    tts_model_enable: bool | None = None
    tts_model_id: uuid.UUID | None = None
    tts_type: str | None = None
    tts_autoplay: bool | None = None
    stt_model_enable: bool | None = None
    stt_model_id: uuid.UUID | None = None
    stt_autosend: bool | None = None
    tts_model_params_setting: dict[str, Any] | None = None
    stt_model_params_setting: dict[str, Any] | None = None
    mcp_enable: bool | None = None
    mcp_tool_ids: list | None = None
    mcp_servers: dict[str, Any] | None = None
    tool_enable: bool | None = None
    tool_ids: list | None = None
    application_enable: bool | None = None
    application_ids: list | None = None
    skill_tool_ids: list | None = None
    file_upload_enable: bool | None = None
    file_upload_setting: dict[str, Any] | None = None
    clean_time: int | None = None
    long_term_enable: bool | None = None
    long_term_model_id: uuid.UUID | None = None
    long_term_trigger_type: str | None = None
    long_term_trigger_setting: dict[str, Any] | None = None
    long_term_model_params_setting: dict[str, Any] | None = None


# --- Detail / Response ---


class ApplicationOut(SQLModel):
    id: uuid.UUID
    name: str
    desc: str = ""
    type: str = "SIMPLE"
    workspace_id: str = "default"
    folder_id: str = "default"
    user_id: uuid.UUID | None = None
    model_id: uuid.UUID | None = None
    is_publish: bool = False
    publish_time: datetime | None = None
    icon: str = "./favicon.ico"
    prologue: str = ""
    dialogue_number: int = 0
    knowledge_setting: dict[str, Any] | None = None
    model_setting: dict[str, Any] | None = None
    model_params_setting: dict[str, Any] | None = None
    work_flow: dict[str, Any] | None = None
    problem_optimization: bool = False
    problem_optimization_prompt: str | None = None
    tts_model_enable: bool = False
    tts_model_id: uuid.UUID | None = None
    tts_type: str = "BROWSER"
    tts_autoplay: bool = False
    stt_model_enable: bool = False
    stt_model_id: uuid.UUID | None = None
    stt_autosend: bool = False
    mcp_enable: bool = False
    tool_enable: bool = False
    file_upload_enable: bool = False
    long_term_enable: bool = False
    clean_time: int = 180
    create_time: datetime | None = None
    update_time: datetime | None = None


class ApplicationPage(SQLModel):
    list: Any = []
    total: int = 0


ApplicationPage.model_rebuild()


# --- API Key ---


class ApiKeyCreate(SQLModel):
    is_active: bool = True
    allow_cross_domain: bool = False
    cross_domain_list: list[str] = []
    is_permanent: bool = True


class ApiKeyOut(SQLModel):
    id: uuid.UUID
    secret_key: str
    application_id: uuid.UUID
    is_active: bool = True
    allow_cross_domain: bool = False
    cross_domain_list: list[str] = []
    is_permanent: bool = True
    create_time: datetime | None = None


# --- Access Token ---


class AccessTokenUpdate(SQLModel):
    is_active: bool | None = None
    access_num: int | None = None
    white_active: bool | None = None
    white_list: list | None = None
    show_source: bool | None = None
    show_exec: bool | None = None
    authentication: bool | None = None
    authentication_value: dict[str, Any] | None = None
    language: str | None = None


class AccessTokenOut(SQLModel):
    application_id: uuid.UUID
    access_token: str
    is_active: bool = True
    access_num: int = 100
    white_active: bool = False
    white_list: list = []
    show_source: bool = False
    show_exec: bool = False
    authentication: bool = False
    authentication_value: dict[str, Any] | None = None
    language: str | None = None


# --- Application Version ---


class ApplicationVersionOut(SQLModel):
    id: uuid.UUID
    application_id: uuid.UUID
    name: str = ""
    desc: str = ""
    publish_user_id: uuid.UUID | None = None
    publish_user_name: str = ""
    work_flow: dict[str, Any] | None = None
    create_time: datetime | None = None


# --- Application Stats ---


class ApplicationStatsOut(SQLModel):
    dialogue_number: int = 0
    chat_count: int = 0
    chat_user_count: int = 0
    star_num: int = 0
    trample_num: int = 0


# --- Chat ---


class ChatRequest(SQLModel):
    message: str
    knowledge_ids: list[uuid.UUID] = []
    embedding: dict | None = None
    session_id: str | None = None
    top_n: int = 5
    similarity: float = 0.5
    search_mode: str = "embedding"
