"""arq task entrypoints for the trigger subsystem.

These are the functions referenced by ``app.trigger.scheduled`` cron specs and
by the API when manually firing a trigger. Keeping them in a dedicated
``tasks`` module matches the ``app.trigger.tasks:<name>`` dotted paths that arq
resolves at worker start.
"""

from __future__ import annotations

from typing import Any

from app.trigger.manager import manager


async def run_trigger(ctx: dict[str, Any], trigger_id: str) -> Any:
    """arq task entrypoint: execute a trigger (and all its linked tasks) by id.

    ``ctx`` is the arq worker context (unused here; accepted for signature
    compatibility with arq cron/enqueue job functions).
    """
    return await manager.execute_trigger(trigger_id)
