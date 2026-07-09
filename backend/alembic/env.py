# coding=utf-8
"""Alembic environment for the MaxKB FastAPI backend.

IMPORTANT (migration safety):
- The initial migration (0001_empty) is intentionally EMPTY and only stamps the
  version state. Existing tables are NOT created/dropped by this project.
- `compare_type=False` disables column type-change autogeneration, complementing
  the CI migration guard (scripts/check_migrations.py) which blocks drop_/type
  change operations.
"""
from logging.config import fileConfig

import asyncio
from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from sqlmodel import SQLModel

# Import all models so their tables register on SQLModel.metadata (target_metadata).
import app.models  # noqa: F401

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=False,
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    from app.core.db import engine

    async with engine.connect() as connection:
        await connection.run_sync(_do_run_migrations)


def run_migrations_online() -> None:
    asyncio.run(_run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
