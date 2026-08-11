"""Knowledge-base schemas — KB, document, paragraph, hit test."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import model_validator
from sqlmodel import SQLModel

# Backend internal document status -> frontend 4-char stage code.
# The UI treats the last char as the EMBEDDING stage (see utils/status.ts).
_INTERNAL_DOC_STATUS_CODE = {
    "WAIT": "0",
    "PENDING": "0",
    "INGESTING": "1",
    "SUCCESS": "2",
    "ERROR": "3",
}

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
    document_count: int = 0
    char_length: int = 0
    user_name: str = ""
    embedding_model_name: str = ""
    permission: str = ""
    create_time: datetime | None = None
    update_time: datetime | None = None


class KnowledgePage(SQLModel):
    records: Any = []
    total: int = 0
    current: int = 1
    size: int = 10


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
    paragraph_count: int = 0
    nick_name: str = ""
    tag_count: int = 0
    tags: list[Any] = []

    @model_validator(mode="after")
    def _enrich(self) -> "DocumentOut":
        # Paragraphs are persisted as independent Paragraph rows, never inside
        # document.meta. Drop any legacy `paragraphs` payload to keep list/detail
        # responses lean (it previously bloated the document list with full text).
        if isinstance(self.meta, dict) and "paragraphs" in self.meta:
            self.meta = {k: v for k, v in self.meta.items() if k != "paragraphs"}

        # The frontend `Status`/`StatusTable` components parse `status` as a
        # 4-char stage code (EMBEDDING, GENERATE_PROBLEM, SYNC, TOKENIZE),
        # reversed, where '0'=PENDING '1'=STARTED '2'=SUCCESS '3'=FAILURE
        # 'n'=ignored — exactly the legacy Django "nnn2" format. The backend
        # stores a human-readable status ("WAIT"/"INGESTING"/"SUCCESS"/"ERROR"),
        # so map it to the char code the UI expects.
        code = _INTERNAL_DOC_STATUS_CODE.get(self.status or "WAIT", "0")
        self.status = "nnn" + code

        meta = self.status_meta or {}
        if "aggs" not in meta:
            meta = {
                **meta,
                "aggs": [{"count": self.paragraph_count, "status": code}],
                "state_time": meta.get("state_time") or {},
            }
            self.status_meta = meta
        return self


class DocumentPage(SQLModel):
    records: Any = []
    total: int = 0
    current: int = 1
    size: int = 10


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
    current: int = 1
    size: int = 10


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


# --- Termbase ---


class TermbaseOut(SQLModel):
    id: uuid.UUID
    knowledge_id: uuid.UUID
    content: str = ""
    create_time: datetime | None = None
    update_time: datetime | None = None


class TermbasePage(SQLModel):
    records: Any = []
    total: int = 0


TermbasePage.model_rebuild()


# --- Problem ---


class ProblemOut(SQLModel):
    id: uuid.UUID
    knowledge_id: uuid.UUID
    content: str = ""
    hit_num: int = 0
    paragraph_count: int = 0
    create_time: datetime | None = None
    update_time: datetime | None = None


class ProblemPage(SQLModel):
    records: Any = []
    total: int = 0


ProblemPage.model_rebuild()


class ProblemParagraphOut(SQLModel):
    id: uuid.UUID
    document_id: uuid.UUID
    knowledge_id: uuid.UUID
    content: str = ""
    title: str = ""
    status: str = ""
    hit_num: int = 0
    is_active: bool = True
    position: int = 0
    create_time: datetime | None = None
    update_time: datetime | None = None
