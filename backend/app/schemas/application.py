"""Application (agent) + chat schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel


class ApplicationOut(SQLModel):
    id: uuid.UUID
    name: str
    desc: str = ""
    type: str = "SIMPLE"
    workspace_id: str = "default"
    user_id: uuid.UUID | None = None
    model_id: uuid.UUID | None = None
    is_publish: bool = False
    create_time: datetime | None = None
    update_time: datetime | None = None


class ApplicationPage(SQLModel):
    # Untyped (Any) list to avoid a pydantic v2 eval quirk with nested SQLModel
    # (UUID field) types under ``from __future__ import annotations``; FastAPI
    # still serializes each item correctly. Field is named ``list`` so the
    # annotation must not also be ``list`` (name clash).
    list: Any = []
    total: int = 0


ApplicationPage.model_rebuild()


class ChatRequest(SQLModel):
    message: str
    knowledge_ids: list[uuid.UUID] = []
    embedding: dict | None = None
    session_id: str | None = None
    top_n: int = 5
    similarity: float = 0.5
    search_mode: str = "embedding"
