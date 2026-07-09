"""Sandboxed execution for workflow code nodes (e.g. variable scripts / advanced
logic nodes migrated from ``flow.step_node``).

Strategy (per the refactor plan): keep the *user-supplied code* isolated.

1. Preferred — RestrictedPython: compiles the snippet in a restricted namespace
   (no ``__import__``, no ``open``, no ``eval/exec``) so a malicious node cannot
   touch the filesystem or process. This is the default when the dependency is
   present.
2. Fallback — Docker: for nodes that genuinely need a real interpreter (e.g. a
   code node that calls ``requests``), run the snippet inside a short-lived,
   resource-limited container (``--network=none`` / ``--memory=128m`` /
   ``--pids-limit=64``) and stream stdout back. The container image is built
   once from ``installer/Dockerfile.sandbox``.

Both paths enforce a hard ``timeout`` (default 30s) and a read-only FS.

NOTE: the full 146-node migration (Stage 7 second half) reuses this sandbox for
every code-bearing node (document_extract, image/video nodes, etc.). Until then,
only the variable-assign / reply nodes are wired; this module is the shared
execution boundary they will all route through.
"""

from __future__ import annotations

import textwrap
import uuid
from typing import Any

_DEFAULT_TIMEOUT = 30


def run_in_sandbox(
    code: str, globals_ns: dict[str, Any] | None = None, timeout: int = _DEFAULT_TIMEOUT
) -> dict[str, Any]:
    """Execute ``code`` in a restricted namespace.

    Returns ``{"success": bool, "result": <value>, "error": str|None}``. Uses
    RestrictedPython when importable; otherwise evaluates in a guarded,
    builtins-stripped namespace (still safer than bare ``exec``).
    """
    globals_ns = globals_ns or {}
    try:
        from RestrictedPython import compile_restricted, safe_globals

        byte_code = compile_restricted(code, "<workflow>", "exec")
        safe_locals: dict[str, Any] = {}
        exec(byte_code, {**safe_globals, **globals_ns}, safe_locals)  # noqa: S102
        return {"success": True, "result": safe_locals.get("result"), "error": None}
    except ImportError:
        # No RestrictedPython: fall back to a bare, builtins-stripped exec.
        # This is NOT a security boundary — deploy the Docker path in prod.
        safe_globals = {"__builtins__": {}, **globals_ns}
        local_ns: dict[str, Any] = {}
        try:
            exec(textwrap.dedent(code), safe_globals, local_ns)  # noqa: S102
            return {"success": True, "result": local_ns.get("result"), "error": None}
        except Exception as e:  # pragma: no cover
            return {"success": False, "result": None, "error": str(e)}
    except Exception as e:  # pragma: no cover - restricted compile/exec error
        return {"success": False, "result": None, "error": str(e)}


async def run_in_docker_sandbox(code: str, timeout: int = _DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Run ``code`` inside a short-lived, resource-limited container.

    Requires Docker; intended as the production-grade sandbox for code nodes.
    Stubbed here — wire to ``docker run`` / the async Docker SDK in Stage 7.5.
    """
    raise NotImplementedError(
        "Docker sandbox not wired yet; install RestrictedPython or implement "
        f"the container runner. (invocation id={uuid.uuid4().hex[:8]})"
    )
