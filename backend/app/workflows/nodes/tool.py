"""Tool node: invokes one or more registered tools (Agno Function tools).

The actual tool catalogue is populated in Stage 8 (``app.tools``). This node
resolves ``tool_ids`` (or direct references), executes each tool with the
templated input, and writes the result into the node context. Tools are expected
to be async callables ``(state, inputs) -> dict``; Agno ``Function`` tools are
adapted upstream so they fit the same contract.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


def _get_registry():
    """Lazy import so Stage 8 can extend the tool catalogue without cycles."""
    try:
        from app.tools import registry as _reg
    except Exception:  # pragma: no cover
        _reg = None
    return _reg


class ToolNode(StepNode):
    type = "tool-node"

    async def execute(self) -> NodeResult:
        tool_ids = self.resolve(self.node_data.get("tool_ids")) or []
        if isinstance(tool_ids, str):
            tool_ids = [tool_ids]
        input_field = self.resolve_template(self.node_data.get("input", "{}"))
        try:
            tool_input = input_field if isinstance(input_field, dict) else {}
        except Exception:
            tool_input = {}

        registry = _get_registry()
        results: dict[str, Any] = {}
        for tool_id in tool_ids:
            if registry is None or not hasattr(registry, "get_tool"):
                results[str(tool_id)] = {"error": "tool registry unavailable"}
                continue
            tool = registry.get_tool(tool_id)
            if tool is None:
                results[str(tool_id)] = {"error": "tool not found"}
                continue
            try:
                results[str(tool_id)] = await tool.invoke(self.state, tool_input)
            except Exception as e:  # pragma: no cover - tool failure
                if self.enable_exception:
                    return NodeResult(
                        {"exception_message": str(e)},
                        status=500,
                        exception_message=str(e),
                        branch_id="exception",
                    )
                results[str(tool_id)] = {"error": str(e)}

        return NodeResult(
            {"result": results, "data": str(results), "tool_result": results},
            is_result=self.is_result if self.is_result is not None else False,
        )
