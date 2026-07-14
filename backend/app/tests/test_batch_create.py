"""batch_create_documents routing test — no live PG / LLM.

Verifies that ``batch_create`` persists a ``Document`` + one ``Paragraph`` row
per pre-split segment and triggers embedding (async arq enqueue, or the inline
fallback when enqueue fails), using a fake session and monkeypatched
pipeline/task helpers (链路 A).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.db import get_session
from app.core.password import hash_password
from app.core.security import get_current_user
from app.main import app
from app.models.base import uuid7
from app.models.knowledge import Document, Knowledge, Paragraph
from app.models.models_provider import Model
from app.models.user import User

client = TestClient(app)

_ADMIN = User(id=uuid7(), username="admin", password=hash_password("x"), nick_name="A", is_active=True, role="ADMIN")


class _FakeResult:
    def __init__(self, value) -> None:
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self, knowledge: Knowledge, model: Model | None) -> None:
        self._knowledge = knowledge
        self._model = model
        self._doc = None
        self.added: list = []

    async def get(self, model, ident, *args, **kwargs):
        if model is Knowledge:
            return self._knowledge
        if model is Model:
            return self._model
        if model is Document:
            if self._doc is None:
                self._doc = Document(id=ident, knowledge_id=self._knowledge.id, name="", status="", user_id=None)
            return self._doc
        return None

    async def execute(self, stmt, *args, **kwargs):
        # The "first available embedding model" select returns our fake model.
        return _FakeResult(self._model)

    def add(self, obj) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def refresh(self, obj) -> None:
        pass


def _fake_model() -> Model:
    return Model(
        id=uuid7(),
        provider="openai",
        model_name="text-embedding-3-small",
        model_type="embedding",
        credential='{"api_key": "x"}',
        meta={"dimensions": 1536},
    )


def _fake_knowledge() -> Knowledge:
    return Knowledge(id=uuid7(), name="KB", type=0, embedding_model_id=None, user_id=_ADMIN.id)


def test_batch_create_persists_paragraphs_and_enqueues(monkeypatch):
    knowledge = _fake_knowledge()
    model = _fake_model()
    session = _FakeSession(knowledge, model)

    enqueued: dict = {}

    async def _fake_enqueue(*, knowledge_id, document_id, user_id, embedding, **kwargs):
        enqueued[document_id] = embedding

    monkeypatch.setattr("app.core.tasks.enqueue_ingest_paragraphs", _fake_enqueue)

    async def _fake_embed(*args, **kwargs):
        raise AssertionError("inline fallback must not run when enqueue succeeds")

    monkeypatch.setattr("app.rag.pipeline.embed_paragraphs", _fake_embed)

    def _ov_session():
        yield session

    def _ov_user():
        return _ADMIN

    app.dependency_overrides[get_session] = _ov_session
    app.dependency_overrides[get_current_user] = _ov_user
    try:
        payload = [
            {
                "name": "README.md",
                "paragraphs": [
                    {"title": "t1", "content": "c1"},
                    {"title": "t2", "content": "c2"},
                ],
            }
        ]
        r = client.post(f"/api/knowledge/{knowledge.id}/document/batch_create", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["result"] is True
    assert data["count"] == 1
    assert len(data["document_ids"]) == 1

    docs = [o for o in session.added if isinstance(o, Document)]
    paras = [o for o in session.added if isinstance(o, Paragraph)]
    assert len(docs) == 1
    assert len(paras) == 2
    assert paras[0].content == "c1"
    assert paras[0].title == "t1"
    assert paras[0].position == 1
    assert paras[1].position == 2
    assert list(enqueued.keys()) == data["document_ids"]


def test_batch_create_inline_fallback_when_enqueue_fails(monkeypatch):
    knowledge = _fake_knowledge()
    model = _fake_model()
    session = _FakeSession(knowledge, model)

    async def _boom(*args, **kwargs):
        raise RuntimeError("redis down")

    monkeypatch.setattr("app.core.tasks.enqueue_ingest_paragraphs", _boom)

    embedded: dict = {}

    from app.rag.pipeline import IngestionResult

    async def _fake_embed(sess, *, knowledge_id, document_id, embedding):
        embedded[document_id] = embedding
        return IngestionResult(document_id=document_id, paragraph_count=1, embedding_count=1, char_length=2)

    monkeypatch.setattr("app.rag.pipeline.embed_paragraphs", _fake_embed)

    def _ov_session():
        yield session

    def _ov_user():
        return _ADMIN

    app.dependency_overrides[get_session] = _ov_session
    app.dependency_overrides[get_current_user] = _ov_user
    try:
        payload = [{"name": "D", "paragraphs": [{"title": "t", "content": "c"}]}]
        r = client.post(f"/api/knowledge/{knowledge.id}/document/batch_create", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200, r.text
    assert list(embedded.keys()) == r.json()["document_ids"]


def test_batch_create_400_on_non_list_body(monkeypatch):
    knowledge = _fake_knowledge()
    model = _fake_model()
    session = _FakeSession(knowledge, model)

    def _ov_session():
        yield session

    def _ov_user():
        return _ADMIN

    app.dependency_overrides[get_session] = _ov_session
    app.dependency_overrides[get_current_user] = _ov_user
    try:
        r = client.post(f"/api/knowledge/{knowledge.id}/document/batch_create", json={"name": "x"})
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 400
