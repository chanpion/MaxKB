# coding=utf-8
"""tools app tables. FK columns are stored as plain id columns (the legacy
Django models used db_constraint=False, so there is NO DB-level foreign key)."""
from datetime import datetime
from uuid import UUID

import uuid_utils.compat as uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Field, String

from app.models.base import AppTableBase


class ToolFolder(AppTableBase, table=True):
    __tablename__ = "tool_folder"
    id: str = Field(default_factory=lambda: str(uuid.uuid7()), max_length=64, primary_key=True)
    name: str = Field(default="", max_length=64, index=True)
    desc: str | None = Field(default=None, max_length=200)
    user_id: UUID | None = Field(default=None)
    workspace_id: str = Field(default="default", max_length=64, index=True)
    parent_id: str | None = Field(default=None, max_length=64)
    # MPTT columns retained for schema compatibility (queried via parent_id + CTE).
    tree_id: int = Field(default=0)
    level: int = Field(default=0)
    lft: int = Field(default=0)
    rght: int = Field(default=0)


class Tool(AppTableBase, table=True):
    __tablename__ = "tool"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    user_id: UUID | None = Field(default=None)
    name: str = Field(default="", max_length=64, index=True)
    desc: str = Field(default="", max_length=128)
    code: str = Field(default="", max_length=102400)
    input_field_list: list = Field(default=[], sa_column=Column(JSONB))
    init_field_list: list = Field(default=[], sa_column=Column(JSONB))
    icon: str = Field(default="", max_length=256)
    is_active: bool = Field(default=True, index=True)
    scope: str = Field(default="WORKSPACE", max_length=20, index=True)
    tool_type: str = Field(default="CUSTOM", max_length=20, index=True)
    template_id: str | None = Field(default=None, max_length=128, index=True)
    folder_id: str = Field(default="default", max_length=64)
    workspace_id: str = Field(default="default", max_length=64, index=True)
    init_params: str | None = Field(default=None, max_length=102400)
    label: str | None = Field(default=None, max_length=128, index=True)
    version: str | None = Field(default=None, max_length=64)


class ToolRecord(AppTableBase, table=True):
    __tablename__ = "tool_record"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    tool_id: UUID | None = Field(default=None)
    workspace_id: str = Field(default="default", max_length=64, index=True)
    source_type: str = Field(default="APPLICATION", max_length=256)
    source_id: UUID
    meta: dict = Field(default={}, sa_column=Column(JSONB))
    state: str = Field(default="1", max_length=20)
    run_time: float = Field(default=0.0)


class ToolWorkflow(AppTableBase, table=True):
    __tablename__ = "tool_workflow"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    tool_id: UUID
    workspace_id: str = Field(default="default", max_length=64, index=True)
    work_flow: dict = Field(default={}, sa_column=Column(JSONB))
    is_publish: bool = Field(default=False, index=True)
    publish_time: datetime | None = Field(default=None)


class ToolWorkflowVersion(AppTableBase, table=True):
    __tablename__ = "tool_workflow_version"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    tool_id: UUID
    workspace_id: str = Field(default="default", max_length=64, index=True)
    name: str = Field(default="", max_length=128)
    work_flow: dict = Field(default={}, sa_column=Column(JSONB))
    publish_user_id: UUID | None = Field(default=None)
    publish_user_name: str = Field(default="", max_length=128)
