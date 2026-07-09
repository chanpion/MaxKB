# coding=utf-8
"""Variable assign node: writes resolved key/value pairs into the node context
(and optionally into the global workflow context)."""
from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class VariableAssignNode(StepNode):
    type = "variable-assign-node"

    async def execute(self) -> NodeResult:
        variables = self.node_data.get("variables", []) or []
        node_var: dict = {}
        global_var: dict = {}
        for item in variables:
            key = item.get("key")
            value = self.resolve(item.get("value"))
            if item.get("is_global"):
                global_var[key] = value
            else:
                node_var[key] = value
        return NodeResult(node_var, workflow_variable=global_var, is_result=False)
