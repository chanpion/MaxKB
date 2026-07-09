"""Tool library node: invokes tools from the MaxKB tool catalogue.

Mirrors ``flow.step_node.tool_lib_node``. Tools are loaded from the shared
:func:`app.tools.get_tool` registry (built-ins, code tools, ...). Each tool is
invoked with the (templated) node input and the result is collected into the
node context — identical execution model to :class:`app.workflows.nodes.tool.ToolNode`.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class ToolLibNode(StepNode):
    type = "tool-lib-node"

    async def execute(self) -> NodeResult:
        tool_ids = self.resolve(self.node_data.get("tool_ids")) or []
        if isinstance(tool_ids, str):
            tool_ids = [tool_ids]
        input_field = self.resolve_template(self.node_data.get("input", "{}"))
        try:
            tool_input = input_field if isinstance(input_field, dict) else {}
        except Exception:
            tool_input = {}

        from app.tools import get_tool

        results: dict[str, Any] = {}
        for tool_id in tool_ids:
            tool = get_tool(str(tool_id))
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
