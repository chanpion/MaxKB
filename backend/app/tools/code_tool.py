"""Custom (user-authored) tool execution.

Legacy custom tools store Python ``code`` in the ``tool`` table. MaxKB's
convention is that the code defines an ``execute(**kwargs) -> dict`` function (or
assigns a module-level ``result``). We run that code inside the workflow sandbox
(see ``app.workflows.sandbox``) so a malicious tool cannot escape the process.
"""

from __future__ import annotations

from typing import Any

from app.tools.base import BaseTool
from app.workflows.sandbox import run_in_sandbox


class CodeTool(BaseTool):
    def __init__(
        self, tool_id: str, name: str, code: str, description: str = "", input_schema: dict | None = None
    ) -> None:
        super().__init__(tool_id=tool_id, name=name, description=description, input_schema=input_schema)
        self.code = code

    async def invoke(self, state: Any, inputs: dict[str, Any]) -> dict[str, Any]:
        # Expose the resolved inputs to the sandboxed code.
        sandbox_ns: dict[str, Any] = {"params": inputs, **inputs}
        exec_result = run_in_sandbox(self.code, globals_ns=sandbox_ns)
        if not exec_result["success"]:
            return {"error": exec_result["error"]}
        local = exec_result.get("result")
        if callable(local):
            try:
                return await _maybe_await(local(**inputs))
            except Exception as e:  # pragma: no cover
                return {"error": str(e)}
        if isinstance(local, dict):
            return local
        return {"result": local}


async def _maybe_await(value: Any) -> Any:
    if hasattr(value, "__await__"):
        return await value
    return value
