"""Question node: captures / rewrites the user question for the workflow.

Mirrors MaxKB's ``question-node``. It resolves the question from upstream
context (``question``) or its own ``node_data.question``, optionally applies a
prompt template, and exposes it as ``question`` / ``answer`` for downstream
knowledge / LLM nodes. It is a pass-through (not a result node by default).
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class QuestionNode(StepNode):
    type = "question-node"

    async def execute(self) -> NodeResult:
        # Prefer an upstream-provided question, else this node's own question.
        upstream = self.state.global_context.get("question")
        question = self.resolve(self.node_data.get("question")) or upstream or ""
        question = self.resolve_template(question) if isinstance(question, str) else question
        chunks = [question] if question else []
        if self.state.on_chunk is not None and question:
            self.state.on_chunk(question)
        return NodeResult(
            {"question": question, "answer": question, "content": question, "data": question},
            is_result=self.is_result if self.is_result is not None else False,
            chunks=chunks,
        )
