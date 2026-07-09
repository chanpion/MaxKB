"""Loop start node: marks the entry of a loop body.

Mirrors ``flow.step_node.loop_start_node``. It is a pure pass-through marker —
the real iteration control lives in :class:`~app.workflows.nodes.loop.LoopNode`,
which instantiates a child :class:`~app.workflows.engine.WorkflowEngine` for the
loop body on every iteration.
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class LoopStartNode(StepNode):
    type = "loop-start-node"

    async def execute(self) -> NodeResult:
        return NodeResult({}, is_result=False)
