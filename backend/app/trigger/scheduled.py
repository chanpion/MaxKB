# coding=utf-8
"""Scheduled-trigger support via arq cron.

The legacy service used Celery beat ``PeriodicTask`` rows. The migration scans
those registrations and reproduces them as arq cron jobs (Redis-backed). This
module builds the arq ``cron`` spec from a trigger's ``trigger_setting``
(``cron`` / ``interval`` / ``timezone``) — arq itself is imported lazily so the
module is importable before ``uv sync``.
"""
from __future__ import annotations

from typing import Any, Dict

# Maps MaxKB trigger_setting keys -> arq cron kwargs.
_ARQ_CRON_KEYS = ("cron", "interval", "minute", "hour", "day", "month", "day_of_week", "timezone")


def build_arq_cron(trigger_setting: Dict[str, Any]) -> Dict[str, Any]:
    """Extract arq ``cron(...)`` kwargs from a trigger_setting dict."""
    spec: Dict[str, Any] = {}
    for key in _ARQ_CRON_KEYS:
        if key in trigger_setting and trigger_setting[key] is not None:
            spec[key] = trigger_setting[key]
    return spec


def register_scheduled_trigger(trigger: Any) -> None:
    """Register a scheduled trigger as an arq cron job.

    arq workers pick this up from the shared Redis. Requires ``arq`` installed
    and the worker started (see ``app.core.tasks`` / main lifespan).
    """
    from arq import cron

    spec = build_arq_cron(trigger.trigger_setting or {})
    # The cron job enqueues ``run_trigger`` which calls the TriggerManager.
    cron(
        "app.trigger.tasks:run_trigger",
        **spec,
        job_id=str(trigger.id),
    )


async def run_trigger(ctx: Dict[str, Any], trigger_id: str) -> Any:
    """arq task entrypoint: execute a trigger by id."""
    from app.trigger.manager import manager

    return await manager.execute_trigger(trigger_id)
