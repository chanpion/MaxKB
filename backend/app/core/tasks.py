# coding=utf-8
"""Async task queue (arq) + scheduled jobs, replacing Celery.

The legacy stack used Celery + celery-beat + apscheduler for embedding, index
sync, knowledge sync and cleanup. Those periodic jobs are expressed here as
arq `cron_jobs`. Concrete task functions are registered in later stages
(stage 5 embedding/index, stage 6/7 chat & workflow background jobs).
"""
import asyncio
from typing import Callable

from arq import Worker, cron
from arq.connections import RedisSettings
from arq.typing import WorkerSettings

from app.core.config import get_settings

settings = get_settings()

redis_settings = RedisSettings(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password or None,
    database=settings.redis_db,
)

# Registered by downstream stages (embedding, index sync, cleanup, ...).
TASK_FUNCTIONS: list[Callable] = []

# Mirrors legacy celery-beat periodic tasks. Cron specs filled in per job:
#   - embedding sync, knowledge full sync, log cleanup, session cleanup, etc.
CRON_JOBS: list = []


def get_worker_settings() -> WorkerSettings:
    return WorkerSettings(
        functions=TASK_FUNCTIONS,
        cron_jobs=CRON_JOBS,
        redis_settings=redis_settings,
    )


def run_worker() -> None:
    """Entry point for the arq worker process (replaces `celery task`)."""
    worker = Worker(
        functions=TASK_FUNCTIONS,
        cron_jobs=CRON_JOBS,
        redis_settings=redis_settings,
    )
    asyncio.run(worker.run())
