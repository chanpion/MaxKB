# coding=utf-8
"""Self-implemented Agno-compatible model for Xunfei (iFlytek) Spark.

Xunfei uses a proprietary WebSocket protocol (not OpenAI-compatible), so it
cannot reuse OpenAIChat. This adapter implements the minimal model surface
(invoke / stream) and should call the Xunfei WS API. It is the ONLY vendor
requiring a custom adapter among the 24 legacy providers.
"""
from __future__ import annotations

from typing import Any, Iterator


class XunfeiModel:
    def __init__(self, id: str, credential: dict, **kwargs: Any) -> None:
        self.id = id
        self.credential = credential
        self.api_key = credential.get("api_key") or credential.get("apiKey") or ""
        self.app_id = (
            credential.get("app_id")
            or credential.get("XUNFEI_APP_ID")
            or credential.get("APPID")
            or ""
        )

    def invoke(self, messages: list, **kwargs: Any) -> str:
        raise NotImplementedError(
            "Xunfei Spark requires the proprietary WebSocket API; "
            "implement invoke() against the iFlytek endpoint (app_id + api_key + api_secret)."
        )

    def stream(self, messages: list, **kwargs: Any) -> Iterator[str]:
        raise NotImplementedError("See XunfeiModel.invoke for implementation notes.")
