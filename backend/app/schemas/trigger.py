"""Trigger (scheduled task) schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import SQLModel


class TriggerCreate(SQLModel):
    name: str
    desc: str = ""
    trigger_type: str = "SCHEDULED"
    trigger_setting: dict = {}
    meta: dict = {}
    is_active: bool = True
    workspace_id: str = "default"


class TriggerUpdate(SQLModel):
    name: str | None = None
    desc: str | None = None
    trigger_type: str | None = None
    trigger_setting: dict | None = None
    meta: dict | None = None
    is_active: bool | None = None


class TriggerOut(SQLModel):
    id: uuid.UUID
    workspace_id: str = "default"
    name: str
    desc: str = ""
    trigger_type: str = "SCHEDULED"
    trigger_setting: dict = {}
    meta: dict = {}
    is_active: bool = True
    user_id: uuid.UUID | None = None
    create_time: datetime | None = None
    update_time: datetime | None = None


class TriggerTaskOut(SQLModel):
    id: uuid.UUID
    trigger_id: uuid.UUID | None = None
    source_type: str = "APPLICATION"
    source_id: uuid.UUID | None = None
    is_active: bool = True
    parameter: list = []
    meta: dict = {}
