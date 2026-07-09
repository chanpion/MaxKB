"""Tests for the local-model OpenAI-compatible proxy router (no real server).

``httpx.AsyncClient`` is monkeypatched so the proxy wiring (path routing, JSON
pass-through, status code) is exercised without a running vLLM / llama.cpp.
"""

from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class _FakeResp:
    def __init__(self, data: dict, status: int = 200) -> None:
        self._data = data
        self.status_code = status

    def json(self) -> dict:
        return self._data


class _FakeClient:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    async def __aenter__(self) -> _FakeClient:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def request(self, method: str, url: str, **kwargs: object) -> _FakeResp:
        if url.rstrip("/").endswith("/models"):
            return _FakeResp({"object": "list", "data": [{"id": "m1"}]})
        if url.rstrip("/").endswith("/chat/completions"):
            return _FakeResp({"choices": [{"message": {"content": "hi"}}]})
        if url.rstrip("/").endswith("/embeddings"):
            return _FakeResp({"data": [{"embedding": [0.1]}]})
        return _FakeResp({})


def test_models_proxies(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    r = client.get("/api/local_model/v1/models")
    assert r.status_code == 200
    assert r.json()["data"][0]["id"] == "m1"


def test_chat_completions_proxies(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    r = client.post("/api/local_model/v1/chat/completions", json={"model": "x", "messages": []})
    assert r.status_code == 200
    assert r.json()["choices"][0]["message"]["content"] == "hi"


def test_embeddings_proxies(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    r = client.post("/api/local_model/v1/embeddings", json={"input": "x"})
    assert r.status_code == 200
    assert r.json()["data"][0]["embedding"] == [0.1]
