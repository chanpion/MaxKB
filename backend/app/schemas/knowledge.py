"""Knowledge-base schemas — KB, document, paragraph, hit test."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel

# --- Knowledge ---


class KnowledgeCreate(SQLModel):
    name: str
    desc: str = ""
    type: int = 0
    scope: str = "WORKSPACE"
    embedding_model_id: str | None = None
    folder_id: str = "default"
    workspace_id: str = "default"
    meta: dict = {}


class KnowledgeUpdate(SQLModel):
    name: str | None = None
    desc: str | None = None
    embedding_model_id: str | None = None
    meta: dict | None = None


class KnowledgeOut(SQLModel):
    id: uuid.UUID
    name: str
    desc: str = ""
    type: int = 0
    scope: str = "WORKSPACE"
    workspace_id: str = "default"
    user_id: uuid.UUID | None = None
    embedding_model_id: uuid.UUID | None = None
    file_size_limit: int = 100
    file_count_limit: int = 50
    create_time: datetime | None = None
    update_time: datetime | None = None


class KnowledgePage(SQLModel):
    records: Any = []
    total: int = 0


KnowledgePage.model_rebuild()


# --- Document ---


class DocumentCreate(SQLModel):
    name: str
    type: int = 0
    hit_handling_method: str = "optimization"
    directly_return_similarity: float = 0.9
    meta: dict[str, Any] = {}


class DocumentUpdate(SQLModel):
    name: str | None = None
    is_active: bool | None = None
    hit_handling_method: str | None = None
    directly_return_similarity: float | None = None
    meta: dict[str, Any] | None = None


class DocumentOut(SQLModel):
    id: uuid.UUID
    knowledge_id: uuid.UUID
    name: str
    char_length: int = 0
    status: str = ""
    is_active: bool = True
    type: int = 0
    hit_handling_method: str = "optimization"
    directly_return_similarity: float = 0.9
    meta: dict[str, Any] | None = None
    status_meta: dict[str, Any] | None = None
    create_time: datetime | None = None
    update_time: datetime | None = None


class DocumentPage(SQLModel):
    records: Any = []
    total: int = 0


DocumentPage.model_rebuild()


# --- Paragraph ---


class ParagraphOut(SQLModel):
    id: uuid.UUID
    document_id: uuid.UUID
    knowledge_id: uuid.UUID
    content: str = ""
    title: str = ""
    status: str = ""
    hit_num: int = 0
    is_active: bool = True
    position: int = 0
    chunks: list[str] = []
    create_time: datetime | None = None
    update_time: datetime | None = None


class ParagraphPage(SQLModel):
    records: Any = []
    total: int = 0


ParagraphPage.model_rebuild()


# --- Hit test ---


class HitTestRequest(SQLModel):
    # Field names match the legacy Django serializer + frontend payload.
    query_text: str
    top_number: int = 5
    similarity: float = 0.5
    search_mode: str = "embedding"  # embedding | keywords | blend


# --- Tags ---


class TagCreate(SQLModel):
    key: str
    value: str


class TagOut(SQLModel):
    id: uuid.UUID
    knowledge_id: uuid.UUID
    key: str
    value: str
    create_time: datetime | None = None
