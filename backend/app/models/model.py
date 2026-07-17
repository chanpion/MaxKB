"""Model table (db_table='model').

NOTE: both `models_provider` and `local_model` define a `Model` pointing to the
same `model` table. Defined ONCE here. Stores provider model credentials.
"""

from typing import Any
from uuid import UUID

import uuid_utils.compat as uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import AppTableBase


class Model(AppTableBase, table=True):
    __tablename__ = "model"

    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    name: str = Field(default="", max_length=128, index=True)
    status: str = Field(default="SUCCESS", max_length=20, index=True)
    model_type: str = Field(default="", max_length=128, index=True)
    model_name: str = Field(default="", max_length=128, index=True)
    user_id: UUID | None = Field(default=None)
    provider: str = Field(default="", max_length=128, index=True)
    credential: str = Field(default="", max_length=102400)
    meta: dict = Field(default={}, sa_column=Column(JSONB))
    model_params_form: Any = Field(default={}, sa_column=Column(JSONB))
    workspace_id: str = Field(default="default", max_length=64, index=True)
