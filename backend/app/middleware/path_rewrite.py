"""Path-rewrite ASGI middleware.

Rewrites legacy Django-style paths before they reach the FastAPI router.

- ``/admin/api/*`` → ``/api/*`` (or whatever ``api_prefix`` is)
- ``/chat/api/*`` → ``/api/*``
- ``/api/workspace/{wid}/*`` → ``/api/*``
"""

from __future__ import annotations

import re

WS_RE = re.compile(r"^/api/workspace/[^/]+/")

LEGACY_ALIASES: list[tuple[str, str]] = [
    (r"^/api/user_manage$", "/api/user"),
    (r"^/api/user_manage/(.+)$", r"/api/user/manage/\1"),
    (r"^/api/provider$", "/api/model/providers"),
    (r"^/api/provider/model_type_list", "/api/model/providers/model_type_list"),
    (r"^/api/provider/model_list", "/api/model/providers/model_list"),
    (r"^/api/provider/model_params_form", "/api/model/providers/model_params_form"),
    (r"^/api/provider/model_form", "/api/model/providers/model_form"),
    (r"^/api/model_list$", "/api/model/list"),
    (r"^/api/profile$", "/api/system/profile"),
]


def _rewrite(path: str, admin_prefix: str, chat_prefix: str) -> tuple[str, bool]:
    """Rewrite a legacy path. Returns (new_path, was_rewritten)."""
    rewritten = False

    if admin_prefix != "/api" and path.startswith(admin_prefix + "/"):
        path = "/api" + path[len(admin_prefix) :]
        rewritten = True
    elif chat_prefix != "/api" and path.startswith(chat_prefix + "/"):
        path = "/api" + path[len(chat_prefix) :]
        rewritten = True

    if "/workspace/" in path:
        new_path = WS_RE.sub("/api/", path)
        if new_path != path:
            path = new_path
            rewritten = True

    # Lowercase UPPERCASE resource types from workspace folder generic API
    # e.g. /api/KNOWLEDGE/folder → /api/knowledge/folder
    path = re.sub(
        r"^/api/(KNOWLEDGE|APPLICATION|MODEL|TOOL|TRIGGER)(/.*)",
        lambda m: "/api/" + m.group(1).lower() + m.group(2),
        path,
    )

    for pattern, replacement in LEGACY_ALIASES:
        new_path = re.sub(pattern, replacement, path)
        if new_path != path:
            path = new_path
            rewritten = True
            break

    return path, rewritten


class PathRewriteMiddleware:
    """ASGI middleware that rewrites legacy URL prefixes.

    Usage: ``app.add_middleware(PathRewriteMiddleware, admin_prefix="/admin/api", chat_prefix="/chat/api")``
    """

    def __init__(self, app, admin_prefix: str = "/api", chat_prefix: str = "/api"):
        self.app = app
        self.admin_prefix = admin_prefix.rstrip("/")
        self.chat_prefix = chat_prefix.rstrip("/")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope["path"]
        new_path, rewritten = _rewrite(path, self.admin_prefix, self.chat_prefix)

        if rewritten:
            scope = {**scope, "path": new_path, "state": {**(scope.get("state") or {}), "_legacy_api": True}}

        await self.app(scope, receive, send)
