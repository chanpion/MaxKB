"""Trigger manager: loads ``event_trigger`` / ``event_trigger_task`` rows and
dispatches their linked tasks (workflow or tool).

The manager is intentionally decoupled from the actual task execution: consumers
(e.g. the API layer in Stage 9) register a handler per ``source_type``. This
keeps the migration free of hard dependencies on the application / tools models
while preserving the legacy table compatibility (same ``db_table`` names).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import text

from app.core.db import engine
from app.models.base import uuid7

# source_type -> async handler(payload) -> result
Handler = Callable[[dict[str, Any]], Awaitable[Any]]

_SQL_ACTIVE_TRIGGERS = """
SELECT t.id, t.workspace_id, t.name, t.trigger_type, t.trigger_setting, t.is_active
FROM event_trigger t
WHERE t.is_active = TRUE
  AND ($1::text IS NULL OR t.workspace_id = $1)
"""

_SQL_TRIGGER_TASKS = """
SELECT source_type, source_id, parameter, meta
FROM event_trigger_task
WHERE trigger_id = $1 AND is_active = TRUE
"""


class TriggerManager:
    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register_handler(self, source_type: str, handler: Handler) -> None:
        self._handlers[source_type] = handler

    async def list_active_triggers(self, workspace_id: str | None = None) -> list[dict[str, Any]]:
        async with engine.connect() as conn:
            rows = (await conn.execute(text(_SQL_ACTIVE_TRIGGERS), (workspace_id,))).mappings().all()
        return [dict(r) for r in rows]

    async def get_tasks(self, trigger_id: str) -> list[dict[str, Any]]:
        async with engine.connect() as conn:
            rows = (await conn.execute(text(_SQL_TRIGGER_TASKS), (str(trigger_id),))).mappings().all()
        return [dict(r) for r in rows]

    async def execute_trigger(self, trigger_id: str, payload: dict[str, Any] | None = None) -> list[Any]:
        """Execute every linked task of a trigger, dispatching by source_type."""
        payload = payload or {}
        tasks = await self.get_tasks(trigger_id)
        results: list[Any] = []
        for task in tasks:
            handler = self._handlers.get(task.get("source_type"))
            if handler is None:
                results.append({"error": f"no handler for {task.get('source_type')}"})
                continue
            task_payload = {
                "trigger_id": str(trigger_id),
                "trigger_task_id": str(task.get("id")),
                "source_type": task.get("source_type"),
                "source_id": str(task.get("source_id")),
                "parameter": task.get("parameter") or [],
                "meta": task.get("meta") or {},
                **payload,
            }
            results.append(await handler(task_payload))
        return results


# Process-wide manager.
manager = TriggerManager()


def register_handler(source_type: str, handler: Handler) -> None:
    manager.register_handler(source_type, handler)


async def execute_trigger(trigger_id: str, payload: dict[str, Any] | None = None) -> list[Any]:
    return await manager.execute_trigger(trigger_id, payload)


def new_trigger_id() -> str:
    return str(uuid7())
