# coding=utf-8
"""Built-in example tools demonstrating the Agno Function integration.

These stand in for the legacy ``apps/tools`` catalogue. Each is registered at
startup so workflows / agents can reference them by id.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict

from app.tools.base import BaseTool
from app.tools.registry import registry


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluate a basic arithmetic expression (+, -, *, /, parentheses)."

    async def invoke(self, state: Any, inputs: Dict[str, Any]) -> Dict[str, Any]:
        expr = str(inputs.get("expression", ""))
        # Restrict to a safe arithmetic subset.
        if not all(c.isdigit() or c in "+-*/(). " for c in expr):
            return {"error": "only arithmetic expressions are allowed"}
        try:
            result = eval(expr, {"__builtins__": {}}, {})  # noqa: S307 - arithmetic only
        except Exception as e:  # pragma: no cover
            return {"error": str(e)}
        return {"result": result}


class CurrentTimeTool(BaseTool):
    name = "current_time"
    description = "Return the current date/time, optionally formatted (default ISO)."

    async def invoke(self, state: Any, inputs: Dict[str, Any]) -> Dict[str, Any]:
        fmt = inputs.get("format")
        now = datetime.datetime.now()
        return {"result": now.strftime(fmt) if fmt else now.isoformat()}


def register_builtin_tools() -> None:
    for tool in (CalculatorTool(tool_id="builtin:calculator"), CurrentTimeTool(tool_id="builtin:current_time")):
        registry.register(tool)
