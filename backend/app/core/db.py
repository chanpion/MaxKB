"""Async database engine and session factory.

SAFETY: this module MUST NOT call ``create_all`` / ``metadata.create_all``.
Tables already exist in the shared PostgreSQL instance (created by the legacy
Django backend). Schema evolution is handled exclusively by Alembic, starting
from the empty baseline (0001_empty). New tables are only introduced via
additive Alembic migrations.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    # Pool mapping (Django dj_db_conn_pool -> SQLAlchemy asyncpg):
    #   POOL_SIZE=20        -> pool_size
    #   MAX_OVERFLOW=80     -> max_overflow
    #   RECYCLE=1800        -> pool_recycle
    #   PRE_PING=True       -> pool_pre_ping
    #   TIMEOUT=30          -> pool_timeout
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=settings.db_pool_pre_ping,
    pool_timeout=settings.db_pool_timeout,
    connect_args={"server_settings": {"application_name": "maxkb_backend"}},
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async SQLAlchemy session."""
    async with SessionLocal() as session:
        yield session
