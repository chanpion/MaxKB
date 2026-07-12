"""API tests that run without a live PostgreSQL / Redis.

The DB session and the current-user dependency are overridden with lightweight
fakes so the route logic (CRUD plumbing, auth gating, serialization) is exercised
end-to-end. Provider-catalog and health endpoints need no overrides at all.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.db import get_session
from app.core.password import hash_password
from app.core.security import get_current_user
from app.main import app
from app.models.base import uuid7
from app.models.knowledge import Knowledge
from app.models.tool import Tool
from app.models.user import User

client = TestClient(app)


class FakeResult:
    def __init__(self, rows: list):
        self._rows = rows

    def scalars(self) -> FakeResult:
        return self

    def all(self) -> list:
        return self._rows

    def scalar(self):
        return self._rows[0] if self._rows else None

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None

    def first(self):
        return self._rows[0] if self._rows else None

    def mappings(self) -> FakeResult:
        return self


class FakeSession:
    """Minimal async session stand-in for the routes exercised by these tests."""

    def __init__(self) -> None:
        self._rows: list = []
        self._total: int = 0
        self._instance = None
        self.added: list = []
        self.deleted = None

    async def scalar(self, *args, **kwargs):
        return self._total

    async def execute(self, *args, **kwargs) -> FakeResult:
        return FakeResult(self._rows)

    async def get(self, model, ident, *args, **kwargs):
        return self._instance

    def add(self, obj) -> None:
        # Real AsyncSession.add is a synchronous method.
        self.added.append(obj)

    async def commit(self) -> None:
        pass

    async def refresh(self, obj) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid7()

    async def delete(self, obj) -> None:
        self.deleted = obj

    async def flush(self) -> None:
        pass


_ADMIN = User(
    id=uuid7(),
    username="admin",
    password=hash_password("topsecret"),
    nick_name="Admin",
    is_active=True,
    role="ADMIN",
)


@pytest.fixture
def session():
    s = FakeSession()

    def _override_session():
        yield s

    def _override_user():
        return _ADMIN

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = _override_user
    yield s
    app.dependency_overrides.clear()


# ----------------------------- no-auth endpoints -------------------------- #
def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_provider_catalog(session):
    r = client.get("/api/model/providers")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list) and len(body) > 0
    providers = {p["provider"] for p in body}
    assert "openai" in providers and "xunfei" in providers
    # structured metadata present
    openai = next(p for p in body if p["provider"] == "openai")
    assert openai["model_types"] and openai["credential_form"]


def test_unauthenticated_request_is_401():
    app.dependency_overrides.clear()
    r = client.get("/api/knowledge")
    assert r.status_code == 401


# ------------------------------- knowledge -------------------------------- #
def test_list_knowledge(session):
    k = Knowledge(name="KB1", user_id=_ADMIN.id)
    session._rows = [k]
    session._total = 1
    r = client.get("/api/knowledge")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["records"][0]["name"] == "KB1"


def test_create_knowledge(session):
    r = client.post(
        "/api/knowledge",
        json={"name": "New KB", "desc": "demo", "type": 0, "scope": "WORKSPACE"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "New KB"
    assert len(session.added) == 1


def test_get_knowledge_404(session):
    session._instance = None
    r = client.get(f"/api/knowledge/{uuid7()}")
    assert r.status_code == 404


# --------------------------------- tools ---------------------------------- #
def test_list_tools(session):
    t = Tool(name="calc", user_id=_ADMIN.id)
    session._rows = [t]
    session._total = 1
    r = client.get("/api/tool")
    assert r.status_code == 200
    assert r.json()["total"] == 1


def test_create_tool(session):
    r = client.post(
        "/api/tool",
        json={"name": "My Tool", "code": "def execute(**kwargs): return {'ok': True}", "tool_type": "CUSTOM"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "My Tool"
    assert len(session.added) == 1


def test_get_tool_404(session):
    session._instance = None
    r = client.get(f"/api/tool/{uuid7()}")
    assert r.status_code == 404


# -------------------------------- trigger --------------------------------- #
def test_list_triggers(session):
    from app.models.trigger import Trigger

    tr = Trigger(name="nightly", workspace_id="default", user_id=_ADMIN.id)
    session._rows = [tr]
    session._total = 1
    r = client.get("/api/trigger")
    assert r.status_code == 200
    assert isinstance(r.json(), list) and len(r.json()) == 1


# --------------------------------- auth ----------------------------------- #
def test_login_success(session):
    session._rows = [_ADMIN]
    r = client.post("/api/user/login", json={"username": "admin", "password": "topsecret"})
    assert r.status_code == 200, r.text
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password(session):
    session._rows = [_ADMIN]
    r = client.post("/api/user/login", json={"username": "admin", "password": "nope"})
    assert r.status_code == 401


# ----------------------------- route registry ----------------------------- #
def test_expected_routes_registered():
    paths = set(app.openapi()["paths"].keys())
    for expected in (
        "/api/health",
        "/api/user/login",
        "/api/knowledge",
        "/api/model/providers",
        "/api/tool",
        "/api/system/log",
        "/api/trigger",
    ):
        assert expected in paths, f"missing route {expected}"
