"""Async task queue (arq) + scheduled jobs, replacing Celery.

The legacy stack used Celery + celery-beat + apscheduler for embedding, index
sync, knowledge sync and cleanup. Those are expressed here as arq task
functions and arq ``cron`` jobs backed by the same Redis:

  * ``ingest_document_task``  — parses/splits/embeds a document (wraps
    :func:`app.rag.pipeline.ingest_document`); enqueue via :func:`enqueue_ingest`.
  * ``cleanup_logs_task`` / ``cleanup_chat_records_task`` — daily maintenance,
    mirroring the legacy celery-beat ``PeriodicTask`` rows.
  * ``run_trigger``           — fires a scheduled/event ``event_trigger`` (also
    registered dynamically per active trigger at worker start).

arq resolves job functions by their ``module.func`` dotted name, so every
callable here is registered in ``TASK_FUNCTIONS`` and enqueue calls pass the
fully-qualified string (``"app.core.tasks.ingest_document_task"`` etc.).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID as _UUID

import redis.asyncio as aioredis
from arq import ArqRedis, Worker, cron
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.db import SessionLocal, engine

settings = get_settings()

redis_settings = RedisSettings(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password or None,
    database=settings.redis_db,
)


# --------------------------------------------------------------------------- #
# Task functions (resolved by arq via their qualified name).
# --------------------------------------------------------------------------- #
async def ingest_document_task(
    ctx: dict[str, Any],
    *,
    knowledge_id: str,
    document_id: str,
    user_id: str | None,
    filename: str,
    content: bytes,
    embedding: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """arq task: ingest one document asynchronously.

    Mirrors the legacy ``embedding_by_document`` Celery task. A fresh async
    session is opened here (workers run outside a request context). The
    document ``status`` is driven through ``PENDING`` -> ``INGESTING`` ->
    ``SUCCESS`` | ``ERROR`` so the frontend can poll progress.
    """
    from app.models.knowledge import Document
    from app.rag.pipeline import ingest_document

    async with SessionLocal() as session:
        doc = await session.get(Document, _UUID(document_id))
        if doc is not None:
            doc.status = "INGESTING"
            doc.status_meta = {"step": "ingesting", "filename": filename[0:128]}
            await session.commit()

        try:
            result = await ingest_document(
                session,
                knowledge_id=knowledge_id,
                document_id=document_id,
                user_id=user_id,
                filename=filename,
                content=content,
                embedding=embedding,
                **kwargs,
            )
        except Exception as exc:
            doc = await session.get(Document, _UUID(document_id))
            if doc is not None:
                doc.status = "ERROR"
                doc.status_meta = {"step": "error", "error": str(exc)[:500]}
                await session.commit()
            raise

        doc = await session.get(Document, _UUID(document_id))
        if doc is not None:
            doc.status = "SUCCESS"
            doc.status_meta = {
                "step": "completed",
                "paragraph_count": result.paragraph_count,
                "embedding_count": result.embedding_count,
                "char_length": result.char_length,
            }
            await session.commit()

        return {
            "document_id": result.document_id,
            "paragraph_count": result.paragraph_count,
            "embedding_count": result.embedding_count,
            "char_length": result.char_length,
        }


async def ingest_paragraphs_task(
    ctx: dict[str, Any],
    *,
    knowledge_id: str,
    document_id: str,
    user_id: str | None,
    embedding: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """arq task: embed already-persisted Paragraph rows of one document.

    Used by the ``batch_create`` API, where the frontend has already split the
    document into paragraphs and the web process wrote the ``Document`` +
    ``Paragraph`` rows. This worker only computes embeddings and writes
    ``embedding`` rows, driving the document ``status`` PENDING -> INGESTING ->
    SUCCESS | ERROR so the frontend can poll progress.
    """
    from app.models.knowledge import Document
    from app.rag.pipeline import embed_paragraphs

    async with SessionLocal() as session:
        doc = await session.get(Document, _UUID(document_id))
        if doc is not None:
            doc.status = "INGESTING"
            doc.status_meta = {"step": "ingesting"}
            await session.commit()

        try:
            result = await embed_paragraphs(
                session,
                knowledge_id=knowledge_id,
                document_id=document_id,
                embedding=embedding,
            )
        except Exception as exc:
            doc = await session.get(Document, _UUID(document_id))
            if doc is not None:
                doc.status = "ERROR"
                doc.status_meta = {"step": "error", "error": str(exc)[:500]}
                await session.commit()
            raise

        doc = await session.get(Document, _UUID(document_id))
        if doc is not None:
            doc.status = "SUCCESS"
            doc.status_meta = {
                "step": "completed",
                "paragraph_count": result.paragraph_count,
                "embedding_count": result.embedding_count,
                "char_length": result.char_length,
            }
            await session.commit()

        return {
            "document_id": result.document_id,
            "paragraph_count": result.paragraph_count,
            "embedding_count": result.embedding_count,
            "char_length": result.char_length,
        }


async def cleanup_logs_task(ctx: dict[str, Any]) -> int:
    """Daily: drop log rows older than 30 days (best-effort)."""
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("DELETE FROM log WHERE create_time < now() - interval '30 days'"))
            await conn.commit()
            return int(res.rowcount or 0)
    except Exception:  # pragma: no cover - maintenance, non-fatal
        return 0


async def cleanup_chat_records_task(ctx: dict[str, Any]) -> int:
    """Daily: purge soft-deleted chat sessions older than 7 days (best-effort)."""
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            res = await conn.execute(
                text("DELETE FROM application_chat WHERE is_deleted = TRUE AND create_time < now() - interval '7 days'")
            )
            await conn.commit()
            return int(res.rowcount or 0)
    except Exception:  # pragma: no cover - maintenance, non-fatal
        return 0


# Trigger execution entrypoint (defined in app.trigger.tasks to keep the
# ``app.trigger.tasks:run_trigger`` dotted path stable for cron specs).
from app.trigger.tasks import run_trigger  # noqa: E402

# Registered functions arq can resolve by qualified name.
TASK_FUNCTIONS: list[Callable] = [
    ingest_document_task,
    ingest_paragraphs_task,
    cleanup_logs_task,
    cleanup_chat_records_task,
    run_trigger,
]

# Mirrors legacy celery-beat periodic tasks.
CRON_JOBS: list = [
    cron(cleanup_logs_task, hour=3, minute=0, name="cleanup_logs"),
    cron(cleanup_chat_records_task, hour=4, minute=0, name="cleanup_chat_records"),
]


def register_active_triggers() -> int:
    """Append an arq cron job for every active ``event_trigger`` (scheduled type).

    Called at worker start so scheduled triggers survive restarts (``job_id`` is
    stable per trigger id). The query is best-effort: if the DB is unreachable
    the worker still starts with the static maintenance crons.
    """
    from app.trigger.manager import manager
    from app.trigger.scheduled import build_arq_cron

    try:
        triggers = asyncio.run(manager.list_active_triggers())
    except Exception:  # pragma: no cover - DB may be down at boot
        return 0

    registered = 0
    for t in triggers:
        spec = build_arq_cron(t.get("trigger_setting") or {})
        if not spec:
            continue
        CRON_JOBS.append(cron("app.trigger.tasks:run_trigger", **spec, job_id=str(t["id"])))
        registered += 1
    return registered


# --------------------------------------------------------------------------- #
# Enqueue helpers (called from the web process).
# --------------------------------------------------------------------------- #
async def enqueue_ingest(
    *,
    knowledge_id: str,
    document_id: str,
    user_id: str | None,
    filename: str,
    content: bytes,
    embedding: dict[str, Any],
    **kwargs: Any,
) -> None:
    """Enqueue a document for asynchronous ingestion.

    Connects to the same Redis arq uses as its broker and enqueues
    :func:`ingest_document_task` (fully-qualified name so the worker resolves it).
    """
    pool = aioredis.ConnectionPool.from_url(settings.redis_url)
    redis = ArqRedis(pool_or_conn=pool)
    try:
        await redis.enqueue_job(
            "app.core.tasks.ingest_document_task",
            knowledge_id=knowledge_id,
            document_id=document_id,
            user_id=user_id,
            filename=filename,
            content=content,
            embedding=embedding,
            **kwargs,
        )
    finally:
        await redis.aclose()


async def enqueue_ingest_paragraphs(
    *,
    knowledge_id: str,
    document_id: str,
    user_id: str | None,
    embedding: dict[str, Any],
    **kwargs: Any,
) -> None:
    """Enqueue embedding of already-persisted paragraphs for one document.

    Mirrors :func:`enqueue_ingest` but targets ``ingest_paragraphs_task`` (no
    raw file content — the ``Paragraph`` rows already exist in the DB).
    """
    pool = aioredis.ConnectionPool.from_url(settings.redis_url)
    redis = ArqRedis(pool_or_conn=pool)
    try:
        await redis.enqueue_job(
            "app.core.tasks.ingest_paragraphs_task",
            knowledge_id=knowledge_id,
            document_id=document_id,
            user_id=user_id,
            embedding=embedding,
            **kwargs,
        )
    finally:
        await redis.aclose()


@dataclass
class WorkerSettings:
    """arq 0.28 dropped the importable ``WorkerSettings`` class (it is now a
    TypedDict). This lightweight holder is what :func:`get_worker_settings`
    returns; :func:`run_worker` reads ``functions`` / ``cron_jobs`` /
    ``redis_settings`` off it to build the arq ``Worker``.
    """

    functions: list[Callable]
    cron_jobs: list
    redis_settings: RedisSettings


def get_worker_settings() -> WorkerSettings:
    return WorkerSettings(
        functions=TASK_FUNCTIONS,
        cron_jobs=CRON_JOBS,
        redis_settings=redis_settings,
    )


def run_worker() -> None:
    """Entry point for the arq worker process (replaces `celery task`)."""
    # The worker executes triggers in its own process, so it must register the
    # real handlers (the web process registers its own copy separately).
    from app.trigger.handlers import register_trigger_handlers

    register_trigger_handlers()
    register_active_triggers()
    settings_obj = get_worker_settings()
    worker = Worker(
        functions=settings_obj.functions,
        cron_jobs=settings_obj.cron_jobs,
        redis_settings=settings_obj.redis_settings,
    )
    asyncio.run(worker.run())
