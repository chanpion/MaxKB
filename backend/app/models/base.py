# coding=utf-8
"""Shared SQLModel base and helpers for strict table alignment.

All legacy MaxKB tables declare ``create_time`` / ``update_time`` (injected by
the legacy ``AppModelMixin``). We replicate them through a NON-table base class
so every table inherits the two columns with identical type/nullable/index.

IMPORTANT: tables are aligned to the EXISTING PostgreSQL schema created by the
Django backend. Do NOT add ``create_all()`` anywhere; schema evolves only via
additive Alembic migrations (see alembic/versions/0001_empty.py).
"""
from datetime import datetime
from uuid import UUID

import uuid_utils.compat as uuid
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class AppTableBase(SQLModel):
    create_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True, index=True)
    )
    update_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True, index=True)
    )


def uuid7_default() -> UUID:
    """Default factory for UUID primary keys (matches Django uuid7 default)."""
    return uuid.uuid7()
