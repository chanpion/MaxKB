"""Loop continue node: emits a CONTINUE signal that ends the current iteration.

Mirrors ``flow.step_node.loop_continue_node``. After the enclosing body finishes
its execution for the current round, the parent
:class:`~app.workflows.nodes.loop.LoopNode` advances to the next iteration.
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class LoopContinueNode(StepNode):
    type = "loop-continue-node"

    async def execute(self) -> NodeResult:
        return NodeResult(
            {"_loop_signal": "CONTINUE"},
            workflow_variable={"_loop_signal": "CONTINUE"},
            is_result=True,
        )
