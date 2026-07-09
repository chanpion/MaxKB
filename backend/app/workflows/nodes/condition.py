"""Condition node: evaluates branch assertions and selects a branch id.

Mirrors ``flow.step_node.condition_node.impl.base_condition_node`` — each branch
carries ``id`` / ``type`` / ``condition`` (and|or) / ``conditions`` (a list of
field/compare/value). The first branch whose assertions pass wins.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class ConditionNode(StepNode):
    type = "condition-node"

    async def execute(self) -> NodeResult:
        branch_list: list[dict[str, Any]] = self.node_data.get("branch", []) or []
        branch = self._execute(branch_list)
        branch_id = branch.get("id") if branch else None
        return NodeResult(
            {"branch_name": branch.get("type") if branch else None},
            is_result=False,
            branch_id=branch_id,
        )

    def _execute(self, branch_list: list[dict[str, Any]]):
        for branch in branch_list:
            if self._branch_assertion(branch):
                return branch
        return None

    def _branch_assertion(self, branch: dict[str, Any]) -> bool:
        return self.state.do_assertion(branch.get("condition", "and"), branch.get("conditions", []))
