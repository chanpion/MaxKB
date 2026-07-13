"""WORK_FLOW chat routing test — no live PG / agno.

Verifies that a ``WORK_FLOW``-type application routes through the
:class:`WorkflowEngine` and streams SSE frames, using a fake session and a
fake engine so the route wiring is exercised without a database or LLM.

Covers both ``application.py``'s ``/{application_id}/chat`` endpoint and
``chat.py``'s ``/chat_message/{chat_id}`` endpoint (``链路 C``).
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core.db import get_session
from app.core.password import hash_password
from app.core.security import get_current_user
from app.main import app
from app.models.application import Application, Chat
from app.models.base import uuid7
from app.models.user import User

client = TestClient(app)

_ADMIN = User(id=uuid7(), username="admin", password=hash_password("x"), nick_name="A", is_active=True, role="ADMIN")


class _FakeSession:
    def __init__(self, application: Application) -> None:
        self._application = application
        self.added: list = []

    async def get(self, model, ident, *args, **kwargs):
        if model is Application:
            return self._application
        if model is Chat:
            return Chat(id=uuid7(), application_id=self._application.id, abstract="新对话", chat_record_count=0)
        return None

    async def execute(self, *args, **kwargs):
        from app.tests.test_api import FakeResult

        return FakeResult([])

    def add(self, obj) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        pass

    async def refresh(self, obj) -> None:
        pass

    async def flush(self) -> None:
        pass


class _FakeEngine:
    def __init__(self, flow, params, *, model_config=None, embedding_config=None) -> None:
        self.params = params

    async def stream(self):
        yield "data: " + json.dumps({"type": "answer", "content": "hi"}, ensure_ascii=False) + "\n\n"
        yield "data: " + json.dumps({"type": "done", "answer": "hi", "details": {}}, ensure_ascii=False) + "\n\n"


# ---------------------------------------------------------------------------
# application.py — /{application_id}/chat (链路 B)
# ---------------------------------------------------------------------------


def test_workflow_chat_routes_to_engine(monkeypatch):
    application = Application(
        id=uuid7(),
        name="WF",
        type="WORK_FLOW",
        work_flow={"nodes": [{"id": "n1", "type": "start-node"}], "edges": []},
    )
    session = _FakeSession(application)

    def _ov_session():
        yield session

    def _ov_user():
        return _ADMIN

    monkeypatch.setattr("app.workflows.engine.WorkflowEngine", _FakeEngine)
    app.dependency_overrides[get_session] = _ov_session
    app.dependency_overrides[get_current_user] = _ov_user

    try:
        r = client.post(
            "/api/application/00000000-0000-0000-0000-000000000000/chat",
            json={"message": "你好"},
        )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert "answer" in r.text
    assert '"type": "done"' in r.text


def test_workflow_chat_400_when_no_graph(monkeypatch):
    application = Application(id=uuid7(), name="WF", type="WORK_FLOW", work_flow={})
    session = _FakeSession(application)

    def _ov_session():
        yield session

    def _ov_user():
        return _ADMIN

    monkeypatch.setattr("app.workflows.engine.WorkflowEngine", _FakeEngine)
    app.dependency_overrides[get_session] = _ov_session
    app.dependency_overrides[get_current_user] = _ov_user

    try:
        r = client.post(
            "/api/application/00000000-0000-0000-0000-000000000000/chat",
            json={"message": "你好"},
        )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 400


# ---------------------------------------------------------------------------
# chat.py — /chat_message/{chat_id} (链路 C)
# ---------------------------------------------------------------------------


def test_chat_message_workflow_routes_to_engine(monkeypatch):
    """WORK_FLOW application should route to WorkflowEngine via chat_message endpoint."""
    application = Application(
        id=uuid7(),
        name="WF",
        type="WORK_FLOW",
        work_flow={"nodes": [{"id": "n1", "type": "start-node"}], "edges": []},
    )
    session = _FakeSession(application)

    def _ov_session():
        yield session

    monkeypatch.setattr("app.workflows.engine.WorkflowEngine", _FakeEngine)
    app.dependency_overrides[get_session] = _ov_session

    try:
        r = client.post(
            "/api/chat/chat_message/00000000-0000-0000-0000-000000000000",
            json={"message": "你好", "stream": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert "answer" in r.text
    assert '"type": "done"' in r.text


def test_chat_message_workflow_400_when_no_graph(monkeypatch):
    """chat_message should return 400 when WORK_FLOW app has no workflow graph."""
    application = Application(id=uuid7(), name="WF", type="WORK_FLOW", work_flow={})
    session = _FakeSession(application)

    def _ov_session():
        yield session

    monkeypatch.setattr("app.workflows.engine.WorkflowEngine", _FakeEngine)
    app.dependency_overrides[get_session] = _ov_session

    try:
        r = client.post(
            "/api/chat/chat_message/00000000-0000-0000-0000-000000000000",
            json={"message": "你好"},
        )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 400
