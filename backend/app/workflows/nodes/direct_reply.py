"""Direct reply node: emits the (templated) content as the answer."""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class DirectReplyNode(StepNode):
    type = "direct-reply-node"

    async def execute(self) -> NodeResult:
        content = self.resolve_template(self.node_data.get("content", ""))
        chunks: list[str] = [content] if content else []
        if self.state.on_chunk is not None:
            for ch in chunks:
                self.state.on_chunk(ch)
        return NodeResult(
            {"answer": content, "content": content, "data": content},
            is_result=True,
            chunks=chunks,
        )
