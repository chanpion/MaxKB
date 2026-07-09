"""Shared API schemas: paging and standard envelopes."""

from __future__ import annotations

from sqlmodel import SQLModel


class Page(SQLModel):
    page: int = 1
    size: int = 10


class PageData(SQLModel):
    """Generic page envelope (overridden per resource for typed ``list``)."""

    total: int = 0


class Result(SQLModel):
    """Standard success envelope."""

    code: int = 200
    message: str = "success"
