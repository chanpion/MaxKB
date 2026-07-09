"""Knowledge-base schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel


class KnowledgeCreate(SQLModel):
    name: str
    desc: str = ""
    type: int = 0
    scope: str = "WORKSPACE"
    embedding_model_id: uuid.UUID | None = None
    folder_id: str = "default"
    workspace_id: str = "default"
    meta: dict = {}


class KnowledgeUpdate(SQLModel):
    name: str | None = None
    desc: str | None = None
    embedding_model_id: uuid.UUID | None = None
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
    # Untyped (Any) list (see ApplicationPage note re: pydantic nested-model
    # eval quirk). Field is named ``list`` so the annotation must not be ``list``.
    list: Any = []
    total: int = 0


KnowledgePage.model_rebuild()
