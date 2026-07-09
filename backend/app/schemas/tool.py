"""Tool + tool-folder schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel


class ToolFolderCreate(SQLModel):
    name: str
    desc: str = ""
    parent_id: str | None = None
    workspace_id: str = "default"


class ToolFolderOut(SQLModel):
    id: str
    name: str
    desc: str | None = None
    parent_id: str | None = None
    workspace_id: str = "default"
    tree_id: int | None = None
    level: int | None = None
    lft: int | None = None
    rght: int | None = None
    create_time: datetime | None = None
    update_time: datetime | None = None


class ToolCreate(SQLModel):
    name: str
    desc: str = ""
    code: str = ""
    tool_type: str = "CUSTOM"
    folder_id: str = "default"
    workspace_id: str = "default"
    icon: str = ""
    is_active: bool = True
    input_field_list: list = []
    init_field_list: list = []
    init_params: str | None = None
    label: str | None = None


class ToolUpdate(SQLModel):
    name: str | None = None
    desc: str | None = None
    code: str | None = None
    icon: str | None = None
    is_active: bool | None = None
    folder_id: str | None = None
    input_field_list: list | None = None
    init_field_list: list | None = None
    init_params: str | None = None
    label: str | None = None


class ToolOut(SQLModel):
    id: uuid.UUID
    name: str
    desc: str = ""
    icon: str = ""
    is_active: bool = True
    scope: str = "WORKSPACE"
    tool_type: str = "CUSTOM"
    folder_id: str = "default"
    workspace_id: str = "default"
    user_id: uuid.UUID | None = None
    create_time: datetime | None = None
    update_time: datetime | None = None


class ToolPage(SQLModel):
    # Untyped (Any) list — see schemas/application.py note re: pydantic eval quirk.
    list: Any = []
    total: int = 0


ToolPage.model_rebuild()
