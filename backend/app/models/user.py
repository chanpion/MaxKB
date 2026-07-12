"""User table (db_table='user').

NOTE: both the `users` app and `local_model` app define a `User` model pointing
to the same `user` table in the legacy DB. We define it ONCE here.
"""

from uuid import UUID

import uuid_utils.compat as uuid
from sqlmodel import Field

from app.models.base import AppTableBase


class User(AppTableBase, table=True):
    __tablename__ = "user"

    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    email: str | None = Field(default=None, unique=True, index=True, max_length=254)
    phone: str = Field(default="", max_length=20, index=True)
    nick_name: str = Field(default="", max_length=150, unique=True, index=True)
    username: str = Field(default="", max_length=150, unique=True, index=True)
    password: str = Field(default="", max_length=150)
    role: str = Field(default="", max_length=150)
    source: str = Field(default="LOCAL", max_length=10, index=True)
    is_active: bool = Field(default=True, index=True)
    language: str | None = Field(default=None, max_length=10)
