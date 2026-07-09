# coding=utf-8
"""Start node: seeds the workflow with the user question / form data."""
from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class StartNode(StepNode):
    type = "start-node"

    async def execute(self) -> NodeResult:
        question = self.state.params.get("question", "")
        form_data = self.state.params.get("form_data", {})
        self.context.update({"question": question, "form_data": form_data, "data": question})
        return NodeResult(
            {"question": question, "form_data": form_data, "data": question},
            is_result=False,
        )
