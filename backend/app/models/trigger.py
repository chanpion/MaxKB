"""trigger app tables."""

from uuid import UUID

import uuid_utils.compat as uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import AppTableBase


class Trigger(AppTableBase, table=True):
    __tablename__ = "event_trigger"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    workspace_id: str = Field(default="default", max_length=64, index=True)
    name: str = Field(default="", max_length=128, index=True)
    desc: str = Field(default="", max_length=512)
    trigger_type: str = Field(default="SCHEDULED", max_length=256)
    trigger_setting: dict = Field(default={}, sa_column=Column(JSONB))
    meta: dict = Field(default={}, sa_column=Column(JSONB))
    is_active: bool = Field(default=True, index=True)
    user_id: UUID | None = Field(default=None)


class TriggerTask(AppTableBase, table=True):
    __tablename__ = "event_trigger_task"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    trigger_id: UUID
    source_type: str = Field(default="APPLICATION", max_length=256)
    source_id: UUID
    is_active: bool = Field(default=True, index=True)
    parameter: list = Field(default=[], sa_column=Column(JSONB))
    meta: dict = Field(default={}, sa_column=Column(JSONB))


class TaskRecord(AppTableBase, table=True):
    __tablename__ = "event_trigger_task_record"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    trigger_id: UUID
    trigger_task_id: UUID
    source_type: str = Field(default="APPLICATION", max_length=256)
    source_id: UUID
    task_record_id: UUID
    meta: dict = Field(default={}, sa_column=Column(JSONB))
    state: str = Field(default="1", max_length=20)
    run_time: float = Field(default=0.0)
