"""Auth schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import SQLModel


class LoginRequest(SQLModel):
    username: str
    password: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(SQLModel):
    id: uuid.UUID
    username: str
    nick_name: str
    email: str | None = None
    role: str = ""
    is_active: bool = True
    source: str = ""
    language: str | None = None
    create_time: datetime | None = None
