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
from sqlmodel import Field, SQLModel


class AppTableBase(SQLModel):
    # NOTE: Do NOT use `sa_column=Column(...)` here. A `Column` instance created
    # in this base class body would be SHARED by every `table=True` subclass,
    # causing "Column object 'create_time' already assigned to Table 'X'".
    # Plain `Field` makes SQLModel build a fresh `Column` per subclass instead.
    create_time: datetime | None = Field(default=None, index=True)
    update_time: datetime | None = Field(default=None, index=True)


def uuid7() -> UUID:
    """UUID7 primary-key factory (matches Django uuid7 default)."""
    return uuid.uuid7()


# Backwards-compatible alias.
uuid7_default = uuid7
