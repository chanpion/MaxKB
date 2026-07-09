"""Tool-start node: marks the entry of a tool workflow.

Mirrors ``flow.step_node.tool_start_node``. A pure pass-through marker — the
tool workflow itself is executed by the surrounding engine, so this node simply
forwards its context.
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class ToolStartNode(StepNode):
    type = "tool-start-node"

    async def execute(self) -> NodeResult:
        return NodeResult({}, is_result=False)
