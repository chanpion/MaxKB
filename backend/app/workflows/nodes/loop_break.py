"""Loop break node: emits a BREAK signal that terminates the enclosing loop.

The signal is written into the loop body's global context (via
``workflow_variable``) so the parent
:class:`~app.workflows.nodes.loop.LoopNode` can detect it after each iteration.
Mirrors ``flow.step_node.loop_break_node``.
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class LoopBreakNode(StepNode):
    type = "loop-break-node"

    async def execute(self) -> NodeResult:
        return NodeResult(
            {"_loop_signal": "BREAK"},
            workflow_variable={"_loop_signal": "BREAK"},
            is_result=True,
        )
