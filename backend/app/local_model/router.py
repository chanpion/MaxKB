"""OpenAI-compatible proxy router for the local model service.

Forwards ``/v1`` style requests to a vLLM / llama.cpp / OpenAI-compatible server
running at ``local_model_protocol://local_model_host:local_model_port``. This
keeps the migration's local-model profile functionally equivalent to the legacy
one without re-implementing the inference server.
"""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.config import get_settings

router = APIRouter(prefix="/api/local_model/v1", tags=["local-model"])


def _base_url() -> str:
    s = get_settings()
    return f"{s.local_model_protocol}://{s.local_model_host}:{s.local_model_port}/v1"


async def _upstream(method: str, path: str, *, json: Any | None = None, params: Any | None = None) -> httpx.Response:
    """Single upstream call used by the JSON endpoints (mockable in tests)."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as client:
        return await client.request(method, f"{_base_url()}{path}", json=json, params=params)


@router.get("/models")
async def list_models() -> JSONResponse:
    resp = await _upstream("GET", "/models")
    return JSONResponse(resp.json(), status_code=resp.status_code)


@router.post("/chat/completions")
async def chat_completions(request: Request):
    payload = await request.json()
    if bool(payload.get("stream")):

        async def _gen():
            async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as client:
                async with client.stream("POST", f"{_base_url()}/chat/completions", json=payload) as r:
                    async for chunk in r.aiter_bytes():
                        yield chunk

        return StreamingResponse(_gen(), media_type="text/event-stream")
    resp = await _upstream("POST", "/chat/completions", json=payload)
    return JSONResponse(resp.json(), status_code=resp.status_code)


@router.post("/embeddings")
async def embeddings(request: Request) -> JSONResponse:
    payload = await request.json()
    resp = await _upstream("POST", "/embeddings", json=payload)
    return JSONResponse(resp.json(), status_code=resp.status_code)
