"""LLM chat node: builds an Agno ``Agent`` from the resolved model config and
runs the (templated) prompt, streaming the answer back through ``state.on_chunk``.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class LLMChatNode(StepNode):
    type = "ai-chat-node"

    def _model_config(self) -> dict[str, Any]:
        # The engine injects the active model credentials into params.
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            # Fall back to per-node model_id reference if provided.
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg

    async def execute(self) -> NodeResult:
        cfg = self._model_config()
        system = self.resolve_template(self.node_data.get("system", ""))
        prompt = self.resolve_template(self.node_data.get("prompt", ""))
        dialogue_number = int(self.node_data.get("dialogue_number", 0) or 0)
        is_result = self.is_result

        from agno.agent import Agent

        from app.providers import get_llm

        llm = get_llm(cfg["provider"], cfg["model_name"], cfg.get("credential", {}))
        agno_tools = []
        tool_ids = self.resolve(self.node_data.get("tool_ids")) or []
        if tool_ids:
            from app.tools import get_agno_tools

            agno_tools = get_agno_tools([str(t) for t in tool_ids])
        agent = Agent(model=llm, instructions=system or None, markdown=True, tools=agno_tools or None)

        answer_parts: list[str] = []

        def _sink(text: str) -> None:
            answer_parts.append(text)
            if self.state.on_chunk is not None:
                self.state.on_chunk(text)

        # Pull chat history (last N turns) when available.
        history = self.state.chat_context.get("history", [])
        history_block = ""
        if dialogue_number and history:
            for turn in history[-dialogue_number:]:
                history_block += f"User: {turn.get('problem_text', '')}\nAssistant: {turn.get('answer_text', '')}\n"

        user_message = (history_block + prompt).strip() or prompt
        try:
            async for event in agent.arun(user_message, stream=True):
                content = getattr(event, "content", None)
                if content:
                    _sink(content)
            answer = "".join(answer_parts)
        except Exception as e:  # pragma: no cover - network/provider failure
            if self.enable_exception:
                return NodeResult(
                    {"answer": "", "branch_id": "exception", "exception_message": str(e)},
                    status=500,
                    exception_message=str(e),
                )
            raise

        result = NodeResult(
            {"answer": answer, "content": answer, "data": answer},
            is_result=is_result if is_result is not None else True,
            chunks=answer_parts,
        )
        return result
