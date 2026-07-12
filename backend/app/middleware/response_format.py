"""Response-format middleware.

Wraps plain JSON responses in the Django REST Framework envelope
``{code: 200, data: ..., message: "success"}`` for requests that arrived
through the legacy ``/admin/api`` or ``/chat/api`` prefix.

New-frontend requests (``/api/*``) are passed through unchanged.
"""

from __future__ import annotations

import gzip
import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class LegacyResponseMiddleware(BaseHTTPMiddleware):
    """Wrap JSON responses for legacy frontend compatibility."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Only transform for requests that arrived through legacy prefixes
        is_legacy = request.scope.get("state", {}).get("_legacy_api", False)
        if not is_legacy:
            return response

        # Only wrap JSON responses, skip streaming / non-200-success
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Don't wrap error responses — let the original body + HTTP status pass through
        if response.status_code >= 400:
            return response

        if response.status_code == 204:
            return Response(
                content=json.dumps({"code": 200, "data": None, "message": "success"}, ensure_ascii=False),
                status_code=200,
                media_type="application/json",
            )

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Some responses may arrive gzip-compressed (e.g. proxied upstreams, or if
        # GZipMiddleware ordering ever changes). Decompress before parsing so we
        # never feed gzip bytes to json.loads.
        if response.headers.get("content-encoding", "").lower() == "gzip":
            try:
                body = gzip.decompress(body)
            except (OSError, EOFError):
                pass

        if not body:
            return Response(
                content=json.dumps({"code": 200, "data": None, "message": "success"}, ensure_ascii=False),
                media_type="application/json",
                status_code=200,
            )

        try:
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            # Not JSON (could be a proxied binary/compressed payload) — pass through
            # verbatim so we don't corrupt the response.
            return Response(content=body, media_type=response.media_type, status_code=response.status_code)

        wrapped = {"code": 200, "data": data, "message": "success"}
        # Override to 200 so the frontend promise helper (which checks res.status===200)
        # doesn't reject successful 201/204 responses.
        return Response(
            content=json.dumps(wrapped, ensure_ascii=False, default=str),
            media_type="application/json",
            status_code=200,
        )
