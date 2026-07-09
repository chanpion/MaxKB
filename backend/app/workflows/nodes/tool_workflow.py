"""Tool-workflow node: runs a set of catalogue tools inside an Agno Agent.

Mirrors ``flow.step_node.tool_workflow_lib_node``. Unlike :class:`ToolLibNode`
(which calls each tool directly), this node hands the tools to an Agno Agent as
native function-calling tools, letting the model orchestrate multi-step tool
use from the node's prompt.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class ToolWorkflowNode(StepNode):
    type = "tool-workflow-lib-node"

    def _model_config(self) -> dict[str, Any]:
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg

    async def execute(self) -> NodeResult:
        tool_ids = self.resolve(self.node_data.get("tool_ids")) or []
        if isinstance(tool_ids, str):
            tool_ids = [tool_ids]
        prompt = self.resolve_template(self.node_data.get("prompt", ""))

        from agno.agent import Agent

        from app.providers import get_llm
        from app.tools import get_agno_tools

        cfg = self._model_config()
        if not cfg:
            return NodeResult(
                {"answer": "", "exception_message": "model_config is required"},
                status=500,
                exception_message="model_config is required",
            )
        llm = get_llm(cfg["provider"], cfg["model_name"], cfg.get("credential", {}))
        agno_tools = get_agno_tools([str(t) for t in tool_ids])
        agent = Agent(model=llm, tools=agno_tools or None, markdown=True)

        answer_parts: list[str] = []
        try:
            async for event in agent.arun(prompt, stream=True):
                content = getattr(event, "content", None)
                if content:
                    answer_parts.append(content)
                    if self.state.on_chunk is not None:
                        self.state.on_chunk(content)
        except Exception as e:  # pragma: no cover - provider/tool failure
            if self.enable_exception:
                return NodeResult(
                    {"answer": "", "exception_message": str(e)},
                    status=500,
                    exception_message=str(e),
                    branch_id="exception",
                )
            raise

        answer = "".join(answer_parts)
        return NodeResult(
            {"answer": answer, "content": answer, "data": answer},
            is_result=self.is_result if self.is_result is not None else True,
            chunks=answer_parts,
        )
