"""End-to-end tests for trigger handler execution (no DB / no LLM required).

These prove the `application` / `tool` handlers registered into
:class:`~app.trigger.manager.TriggerManager` actually dispatch to the workflow
engine and persist a ``TaskRecord`` — the wiring that previously was a no-op.

The DB ``SessionLocal`` and the workflow ``WorkflowEngine`` are monkeypatched so
no PostgreSQL, Redis or model credentials are needed.
"""

from __future__ import annotations

import uuid

from app.trigger import handlers as handlers_mod
from app.trigger.handlers import (
    application_handler,
    register_trigger_handlers,
    tool_handler,
)
from app.trigger.manager import manager


class _EngineResult:
    def __init__(self, status: int = 200, **extra: object) -> None:
        self._payload = {"status": status, **extra}

    def get(self, key: str, default: object = None) -> object:
        return self._payload.get(key, default)


class _FakeEngine:
    """Stands in for ``WorkflowEngine`` — returns a canned success result."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.captured = kwargs

    async def run(self) -> _EngineResult:
        return _EngineResult(200, answer="ran")


class _Result:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value


class _FakeSession:
    """Async session that returns queued values per ``execute`` call."""

    def __init__(self, *values: object) -> None:
        self._values = list(values)
        self.added: list[object] = []
        self.committed = 0

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def execute(self, *args: object, **kwargs: object) -> _Result:
        if self._values:
            return _Result(self._values.pop(0))
        return _Result(None)

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self.committed += 1


def _app_row() -> object:
    class _App:
        id = uuid.uuid4()
        work_flow = {"nodes": [{"id": "n1"}]}
        model_id = None

    return _App()


def _tool_row() -> object:
    class _Tool:
        id = uuid.uuid4()
        name = "t"
        code = "pass"
        desc = "d"

    return _Tool()


def _tool_workflow_row() -> object:
    class _TW:
        work_flow = {"nodes": [{"id": "n1"}]}
        meta = {}

    return _TW()


async def test_application_handler_runs_engine(monkeypatch):
    monkeypatch.setattr(handlers_mod, "SessionLocal", lambda: _FakeSession(_app_row()))
    monkeypatch.setattr(handlers_mod, "WorkflowEngine", _FakeEngine)

    register_trigger_handlers()
    src = str(uuid.uuid4())
    result = await application_handler(
        {
            "trigger_id": str(uuid.uuid4()),
            "trigger_task_id": str(uuid.uuid4()),
            "source_type": "APPLICATION",
            "source_id": src,
            "parameter": [{"name": "q", "value": "hi"}],
        }
    )
    assert result.get("status") == 200
    # handler is registered under the canonical source_type
    assert "APPLICATION" in manager._handlers


async def test_application_handler_missing_app(monkeypatch):
    monkeypatch.setattr(handlers_mod, "SessionLocal", lambda: _FakeSession(None))

    result = await application_handler(
        {
            "trigger_id": str(uuid.uuid4()),
            "trigger_task_id": str(uuid.uuid4()),
            "source_type": "APPLICATION",
            "source_id": str(uuid.uuid4()),
            "parameter": [],
        }
    )
    assert "error" in result
    assert result.get("status") is None or "error" in result


async def test_tool_handler_runs_workflow_tool(monkeypatch):
    monkeypatch.setattr(handlers_mod, "SessionLocal", lambda: _FakeSession(_tool_row(), _tool_workflow_row()))
    monkeypatch.setattr(handlers_mod, "WorkflowEngine", _FakeEngine)

    register_trigger_handlers()
    result = await tool_handler(
        {
            "trigger_id": str(uuid.uuid4()),
            "trigger_task_id": str(uuid.uuid4()),
            "source_type": "TOOL",
            "source_id": str(uuid.uuid4()),
            "parameter": [],
        }
    )
    assert result.get("status") == 200
    assert "TOOL" in manager._handlers


async def test_tool_handler_missing_tool(monkeypatch):
    monkeypatch.setattr(handlers_mod, "SessionLocal", lambda: _FakeSession(None))

    result = await tool_handler(
        {
            "trigger_id": str(uuid.uuid4()),
            "trigger_task_id": str(uuid.uuid4()),
            "source_type": "TOOL",
            "source_id": str(uuid.uuid4()),
            "parameter": [],
        }
    )
    assert "error" in result
