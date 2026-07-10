# coding=utf-8
"""application app tables (agents, chats, long-term memory, access tokens).

FK columns are plain ids (legacy db_constraint=False -> no DB FKs). MPTT folder
columns retained for compatibility. JSON/JSONB fields rely on SQLModel's
implicit JSONB mapping for PostgreSQL.
"""
from datetime import datetime
from uuid import UUID

import uuid_utils.compat as uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlmodel import Field

from app.models.base import AppTableBase


class ApplicationFolder(AppTableBase, table=True):
    __tablename__ = "application_folder"
    id: str = Field(default_factory=lambda: str(uuid.uuid7()), max_length=64, primary_key=True)
    name: str = Field(default="", max_length=64, index=True)
    desc: str | None = Field(default=None, max_length=200)
    user_id: UUID | None = Field(default=None)
    workspace_id: str = Field(default="default", max_length=64, index=True)
    parent_id: str | None = Field(default=None, max_length=64)
    tree_id: int = Field(default=0)
    level: int = Field(default=0)
    lft: int = Field(default=0)
    rght: int = Field(default=0)


class Application(AppTableBase, table=True):
    __tablename__ = "application"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    workspace_id: str = Field(default="default", max_length=64, index=True)
    folder_id: str = Field(default="default", max_length=64)
    is_publish: bool = Field(default=False)
    name: str = Field(default="", max_length=128, index=True)
    desc: str = Field(default="", max_length=512)
    prologue: str = Field(default="", max_length=40960)
    dialogue_number: int = Field(default=0)
    user_id: UUID | None = Field(default=None)
    model_id: UUID | None = Field(default=None)
    knowledge_setting: dict = Field(default={})
    model_setting: dict = Field(default={})
    model_params_setting: dict = Field(default={})
    tts_model_params_setting: dict = Field(default={})
    stt_model_params_setting: dict = Field(default={})
    problem_optimization: bool = Field(default=False)
    icon: str = Field(default="./favicon.ico", max_length=256)
    work_flow: dict = Field(default={})
    type: str = Field(default="SIMPLE", max_length=256)
    problem_optimization_prompt: str | None = Field(default=None, max_length=102400)
    tts_model_id: UUID | None = Field(default=None)
    stt_model_id: UUID | None = Field(default=None)
    tts_model_enable: bool = Field(default=False)
    stt_model_enable: bool = Field(default=False)
    tts_type: str = Field(default="BROWSER", max_length=20)
    tts_autoplay: bool = Field(default=False)
    stt_autosend: bool = Field(default=False)
    clean_time: int = Field(default=180)
    publish_time: datetime | None = Field(default=None)
    file_upload_enable: bool = Field(default=False)
    file_upload_setting: dict = Field(default={})
    mcp_enable: bool = Field(default=False)
    mcp_tool_ids: list = Field(default=[])
    mcp_servers: dict = Field(default={})
    mcp_source: str = Field(default="referencing", max_length=20)
    tool_enable: bool = Field(default=False)
    tool_ids: list = Field(default=[])
    application_enable: bool = Field(default=False)
    application_ids: list = Field(default=[])
    skill_tool_ids: list = Field(default=[])
    mcp_output_enable: bool = Field(default=True)
    file_clean_time: int = Field(default=180)
    long_term_enable: bool = Field(default=False)
    long_term_model_id: UUID | None = Field(default=None)
    long_term_model_params_setting: dict = Field(default={})
    long_term_trigger_type: str = Field(default="ROUND")
    long_term_trigger_setting: dict = Field(default={})


class ApplicationKnowledgeMapping(AppTableBase, table=True):
    __tablename__ = "application_knowledge_mapping"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    application_id: UUID
    knowledge_id: UUID


class ApplicationVersion(AppTableBase, table=True):
    __tablename__ = "application_version"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    application_id: UUID
    name: str = Field(default="", max_length=128)
    desc: str = Field(default="", max_length=512)
    prologue: str = Field(default="", max_length=40960)
    dialogue_number: int = Field(default=0)
    user_id: UUID | None = Field(default=None)
    model_id: UUID | None = Field(default=None)
    knowledge_setting: dict = Field(default={})
    model_setting: dict = Field(default={})
    model_params_setting: dict = Field(default={})
    tts_model_params_setting: dict = Field(default={})
    stt_model_params_setting: dict = Field(default={})
    problem_optimization: bool = Field(default=False)
    icon: str = Field(default="./favicon.ico", max_length=256)
    work_flow: dict = Field(default={})
    type: str = Field(default="SIMPLE", max_length=256)
    problem_optimization_prompt: str | None = Field(default=None, max_length=102400)
    tts_model_id: UUID | None = Field(default=None)
    stt_model_id: UUID | None = Field(default=None)
    tts_model_enable: bool = Field(default=False)
    stt_model_enable: bool = Field(default=False)
    tts_type: str = Field(default="BROWSER", max_length=20)
    tts_autoplay: bool = Field(default=False)
    stt_autosend: bool = Field(default=False)
    clean_time: int = Field(default=180)
    file_upload_enable: bool = Field(default=False)
    file_upload_setting: dict = Field(default={})
    mcp_enable: bool = Field(default=False)
    mcp_tool_ids: list = Field(default=[])
    mcp_servers: dict = Field(default={})
    mcp_source: str = Field(default="referencing", max_length=20)
    tool_enable: bool = Field(default=False)
    tool_ids: list = Field(default=[])
    application_enable: bool = Field(default=False)
    application_ids: list = Field(default=[])
    skill_tool_ids: list = Field(default=[])
    mcp_output_enable: bool = Field(default=True)
    long_term_enable: bool = Field(default=False)
    long_term_model_id: UUID | None = Field(default=None)
    long_term_model_params_setting: dict = Field(default={})
    long_term_trigger_type: str = Field(default="ROUND")
    long_term_trigger_setting: dict = Field(default={})


class Chat(AppTableBase, table=True):
    __tablename__ = "application_chat"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    application_id: UUID
    abstract: str = Field(default="", max_length=1024)
    chat_user_id: str | None = Field(default=None)
    chat_user_type: str = Field(default="ANONYMOUS_USER", max_length=64)
    is_deleted: bool = Field(default=False)
    asker: dict = Field(default={"username": "游客"})
    meta: dict = Field(default={})
    star_num: int = Field(default=0)
    trample_num: int = Field(default=0)
    chat_record_count: int = Field(default=0)
    mark_sum: int = Field(default=0)
    source: dict = Field(default={})
    ip_address: str = Field(default="", max_length=128)


class ChatRecord(AppTableBase, table=True):
    __tablename__ = "application_chat_record"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    chat_id: UUID
    vote_status: str = Field(default="-1", max_length=10)
    vote_reason: str | None = Field(default=None, max_length=50)
    vote_other_content: str = Field(default="", max_length=1024)
    problem_text: str = Field(default="", max_length=10240)
    answer_text: str = Field(default="", max_length=40960)
    answer_text_list: list = Field(default=[], sa_column=Column(ARRAY(JSONB)))
    message_tokens: int = Field(default=0)
    answer_tokens: int = Field(default=0)
    const: int = Field(default=0)
    details: dict = Field(default={})
    improve_paragraph_id_list: list = Field(default=[], sa_column=Column(ARRAY(PG_UUID)))
    run_time: float = Field(default=0.0)
    index: int
    source: dict = Field(default={})
    ip_address: str = Field(default="", max_length=128)


class ChatShareLink(AppTableBase, table=True):
    __tablename__ = "application_chat_share_link"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    chat_id: UUID
    application_id: UUID
    share_type: str = Field(default="PUBLIC", max_length=20)
    user_id: UUID | None = Field(default=None)
    chat_record_ids: list = Field(default=[], sa_column=Column(ARRAY(PG_UUID)))


class ApplicationChatUserStats(AppTableBase, table=True):
    __tablename__ = "application_chat_user_stats"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    chat_user_id: UUID
    chat_user_type: str = Field(default="ANONYMOUS_USER", max_length=64)
    application_id: UUID
    access_num: int = Field(default=0)
    intraday_access_num: int = Field(default=0)


class ApplicationLongTermMemory(AppTableBase, table=True):
    __tablename__ = "application_long_term_memory"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    application_id: UUID
    chat_user_id: str = Field(default="", max_length=128, index=True)
    memory: str = Field(default="")


class ApplicationAccessToken(AppTableBase, table=True):
    __tablename__ = "application_access_token"
    application_id: UUID = Field(primary_key=True)
    access_token: str = Field(default="", max_length=128, unique=True)
    is_active: bool = Field(default=True)
    access_num: int = Field(default=100)
    white_active: bool = Field(default=False)
    white_list: list = Field(default=[], sa_column=Column(ARRAY(PG_UUID)))
    show_source: bool = Field(default=False)
    show_exec: bool = Field(default=False)
    authentication: bool = Field(default=False)
    authentication_value: dict = Field(default={})
    language: str | None = Field(default=None, max_length=10)


class ApplicationApiKey(AppTableBase, table=True):
    __tablename__ = "application_api_key"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    secret_key: str = Field(default="", max_length=1024, unique=True)
    workspace_id: str = Field(default="default", max_length=64, index=True)
    application_id: UUID
    is_active: bool = Field(default=True)
    allow_cross_domain: bool = Field(default=False)
    cross_domain_list: list = Field(default=[], sa_column=Column(ARRAY(PG_UUID)))
    expire_time: datetime = Field(default_factory=datetime.now)
    is_permanent: bool = Field(default=True)
