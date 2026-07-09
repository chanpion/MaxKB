"""Trigger handlers: dispatch ``event_trigger_task`` rows to real execution.

Previously :class:`~app.trigger.manager.TriggerManager` had no registered
handlers, so any trigger only returned ``{"error": "no handler for ..."}``.
This module wires the two legacy ``source_type`` values:

  * ``APPLICATION`` — load the linked application's ``work_flow`` and run it
    through :class:`~app.workflows.engine.WorkflowEngine`.
  * ``TOOL`` — execute the linked tool: a published ``tool_workflow`` runs via
    the engine, otherwise a custom (code) tool runs in the sandbox.

Handlers are registered at process start (see ``register_trigger_handlers``,
called from ``app.main`` lifespan). They look up the linked resource from the
DB lazily at execution time and persist an ``event_trigger_task_record`` row.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.application import Application
from app.models.models_provider import Model
from app.models.tool import Tool, ToolWorkflow
from app.models.trigger import TaskRecord
from app.trigger.manager import register_handler
from app.workflows.engine import WorkflowEngine


def _to_uuid(value: Any) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


def _parameter_to_inputs(parameter: Any) -> dict[str, Any]:
    """Best-effort conversion of a trigger ``parameter`` list into flat inputs.

    Legacy stores a list of ``{"name": ..., "value": ...}`` dicts; flatten to a
    single dict so workflow/tool nodes can resolve them.
    """
    if not isinstance(parameter, list):
        return {}
    inputs: dict[str, Any] = {}
    for item in parameter:
        if isinstance(item, dict) and "name" in item:
            inputs[str(item["name"])] = item.get("value")
        elif isinstance(item, dict) and len(item) == 1:
            k, v = next(iter(item.items()))
            inputs[str(k)] = v
    return inputs


async def _resolve_model_config(session, model_id: Any | None) -> dict[str, Any]:
    """Build ``{provider, model_name, credential}`` for the workflow engine."""
    mid = _to_uuid(model_id)
    if mid is None:
        return {}
    m = (await session.execute(select(Model).where(Model.id == mid))).scalar_one_or_none()
    if m is None:
        return {}
    cred: dict[str, Any] = {}
    if m.credential:
        try:
            cred = json.loads(m.credential)
        except (json.JSONDecodeError, TypeError):
            cred = {}
    return {"provider": m.provider, "model_name": m.model_name, "credential": cred}


def _write_record(
    session,
    *,
    trigger_id: str | None,
    trigger_task_id: str | None,
    source_type: str,
    source_id: str,
    state: str,
    result: dict[str, Any],
    run_time: float,
) -> None:
    record = TaskRecord(
        trigger_id=_to_uuid(trigger_id),
        trigger_task_id=_to_uuid(trigger_task_id) or uuid.uuid4(),
        source_type=source_type,
        source_id=_to_uuid(source_id) or uuid.uuid4(),
        meta=result,
        state=state,
        run_time=run_time,
    )
    session.add(record)


async def application_handler(payload: dict[str, Any]) -> dict[str, Any]:
    """Run the linked application's workflow and record the outcome."""
    trigger_id = payload.get("trigger_id")
    trigger_task_id = payload.get("trigger_task_id")
    source_type = payload.get("source_type") or "APPLICATION"
    source_id = payload.get("source_id")
    inputs = _parameter_to_inputs(payload.get("parameter"))

    async with SessionLocal() as session:
        app_row = (
            await session.execute(select(Application).where(Application.id == _to_uuid(source_id)))
        ).scalar_one_or_none()
        if app_row is None:
            result = {"error": f"application {source_id} not found"}
            _write_record(
                session,
                trigger_id=trigger_id,
                trigger_task_id=trigger_task_id,
                source_type=source_type,
                source_id=str(source_id),
                state="FAILURE",
                result=result,
                run_time=0.0,
            )
            await session.commit()
            return result

        flow = app_row.work_flow or {}
        if not flow.get("nodes"):
            result = {"error": "application has no workflow (work_flow empty)"}
            _write_record(
                session,
                trigger_id=trigger_id,
                trigger_task_id=trigger_task_id,
                source_type=source_type,
                source_id=str(source_id),
                state="FAILURE",
                result=result,
                run_time=0.0,
            )
            await session.commit()
            return result

        model_config = await _resolve_model_config(session, app_row.model_id)
        engine = WorkflowEngine(flow, params=inputs, model_config=model_config, embedding_config={})
        start = time.monotonic()
        try:
            result = await engine.run()
            state = "SUCCESS" if result.get("status") == 200 else "FAILURE"
        except Exception as e:  # surface as a recorded failure, don't crash the trigger
            result = {"error": str(e)}
            state = "FAILURE"
        run_time = round(time.monotonic() - start, 3)
        _write_record(
            session,
            trigger_id=trigger_id,
            trigger_task_id=trigger_task_id,
            source_type=source_type,
            source_id=str(app_row.id),
            state=state,
            result=result,
            run_time=run_time,
        )
        await session.commit()
        return result


async def tool_handler(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute the linked tool (workflow tool or custom code tool)."""
    trigger_id = payload.get("trigger_id")
    trigger_task_id = payload.get("trigger_task_id")
    source_type = payload.get("source_type") or "TOOL"
    source_id = payload.get("source_id")
    inputs = _parameter_to_inputs(payload.get("parameter"))

    async with SessionLocal() as session:
        tool = (await session.execute(select(Tool).where(Tool.id == _to_uuid(source_id)))).scalar_one_or_none()
        if tool is None:
            result = {"error": f"tool {source_id} not found"}
            _write_record(
                session,
                trigger_id=trigger_id,
                trigger_task_id=trigger_task_id,
                source_type=source_type,
                source_id=str(source_id),
                state="FAILURE",
                result=result,
                run_time=0.0,
            )
            await session.commit()
            return result

        # Published workflow tool -> run its flow through the engine.
        tw = (
            await session.execute(
                select(ToolWorkflow).where(
                    ToolWorkflow.tool_id == tool.id,
                    ToolWorkflow.is_publish == True,  # noqa: E712
                )
            )
        ).scalar_one_or_none()

        start = time.monotonic()
        try:
            if tw is not None and tw.work_flow:
                model_config = await _resolve_model_config(
                    session, tw.meta.get("model_id") if isinstance(tw.meta, dict) else None
                )
                engine = WorkflowEngine(tw.work_flow, params=inputs, model_config=model_config, embedding_config={})
                result = await engine.run()
                state = "SUCCESS" if result.get("status") == 200 else "FAILURE"
            else:
                from app.tools.code_tool import CodeTool

                code_tool = CodeTool(tool_id=str(tool.id), name=tool.name, code=tool.code, description=tool.desc)
                result = await code_tool.invoke(None, inputs)
                state = "SUCCESS" if isinstance(result, dict) and "error" not in result else "FAILURE"
        except Exception as e:  # recorded failure, trigger keeps running
            result = {"error": str(e)}
            state = "FAILURE"
        run_time = round(time.monotonic() - start, 3)
        _write_record(
            session,
            trigger_id=trigger_id,
            trigger_task_id=trigger_task_id,
            source_type=source_type,
            source_id=str(tool.id),
            state=state,
            result=result,
            run_time=run_time,
        )
        await session.commit()
        return result


def register_trigger_handlers() -> None:
    """Register the real APPLICATION / TOOL handlers into the TriggerManager.

    Called once at process start (web lifespan and arq worker import). Both
    cases are registered so a mis-cased ``source_type`` still dispatches.
    """
    register_handler("APPLICATION", application_handler)
    register_handler("TOOL", tool_handler)
    register_handler("application", application_handler)
    register_handler("tool", tool_handler)
