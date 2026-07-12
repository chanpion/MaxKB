"""Auth schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import SQLModel


class LoginRequest(SQLModel):
    model_config = {"extra": "allow"}  # Accept captcha, encryptedData etc.
    username: str
    password: str = ""  # Optional — may be sent inside encryptedData


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

    @classmethod
    def create(cls, token_str: str) -> Token:
        return cls(access_token=token_str)


class LoginResponse(Token):
    """Backward-compatible login response — frontend reads ``data.token``."""

    token: str = ""  # noqa: A003

    @classmethod
    def create(cls, token_str: str) -> LoginResponse:  # noqa: A003
        return cls(access_token=token_str, token=token_str)


class UserOut(SQLModel):
    id: uuid.UUID
    username: str
    nick_name: str
    email: str | None = None
    role: list[str] = []
    permissions: list[str] = []
    is_active: bool = True
    source: str = ""
    language: str | None = None
    create_time: datetime | None = None


class UserCreate(SQLModel):
    username: str
    nick_name: str = ""
    email: str | None = None
    password: str
    role: str = "USER"
    phone: str = ""
    is_active: bool = True


class UserUpdate(SQLModel):
    username: str | None = None
    nick_name: str | None = None
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None
    phone: str | None = None
    language: str | None = None


class PasswordResetRequest(SQLModel):
    old_password: str
    new_password: str


class LanguageRequest(SQLModel):
    language: str


class ProfileUpdate(SQLModel):
    nick_name: str | None = None
    email: str | None = None
    phone: str | None = None
    language: str | None = None
