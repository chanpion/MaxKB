"""Intent node: classifies the user input into one of several branches.

Mirrors ``application.flow.step_node.intent_node``. The matched branch id is
returned as ``branch_id`` so the engine routes along the corresponding edge
(``is_assertion_result``). When no branch matches, an ``isOther`` branch is
selected if present.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class IntentNode(StepNode):
    type = "intent-node"

    def _model_config(self) -> dict[str, Any]:
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg

    async def execute(self) -> NodeResult:
        user_input = self.resolve(self.node_data.get("content_list"))
        if isinstance(user_input, str):
            user_input = self.resolve_template(user_input)
        user_input = user_input or ""

        branches = self.node_data.get("branch") or []
        if not branches:
            return NodeResult(
                {"answer": "", "content": "", "branch_id": None},
                is_result=self.is_result,
            )

        cfg = self._model_config()
        if not cfg or not cfg.get("provider"):
            # No model configured: cannot classify, route to "other" if present.
            other = next((b for b in branches if b.get("isOther")), None)
            branch_id = other.get("id") if other else branches[0].get("id")
            return NodeResult(
                {"answer": "", "content": "", "branch_id": branch_id},
                is_result=self.is_result,
                branch_id=branch_id,
            )

        branch_text = "\n".join(f"{i + 1}. [{b.get('id')}] {b.get('content')}" for i, b in enumerate(branches))
        prompt = (
            "你是一个意图分类器。根据用户的问题，从下面的意图列表中选择最匹配的一个，"
            "只输出该意图对应的 id，不要输出其他内容。\n\n"
            f"用户问题：{user_input}\n\n"
            f"意图列表：\n{branch_text}\n\n"
            "最匹配意图的 id："
        )

        from agno.agent import Agent

        from app.providers import get_llm

        llm = get_llm(cfg["provider"], cfg["model_name"], cfg.get("credential", {}))
        agent = Agent(model=llm, markdown=False)
        try:
            answer_parts: list[str] = []
            async for event in agent.arun(prompt, stream=False):
                content = getattr(event, "content", None)
                if content:
                    answer_parts.append(content)
            raw = "".join(answer_parts).strip()
        except Exception as e:
            if self.enable_exception:
                return NodeResult(
                    {"answer": "", "branch_id": "exception", "exception_message": str(e)},
                    status=500,
                    exception_message=str(e),
                    branch_id="exception",
                )
            raise

        branch_id = self._match_branch(raw, branches)
        matched = next((b for b in branches if b.get("id") == branch_id), None)
        content = matched.get("content") if matched else raw
        return NodeResult(
            {"answer": content, "content": content, "branch_id": branch_id},
            is_result=self.is_result,
            branch_id=branch_id,
        )

    @staticmethod
    def _match_branch(raw: str, branches: list[dict[str, Any]]) -> Any:
        raw_clean = (raw or "").strip()
        for b in branches:
            bid = b.get("id")
            if bid is not None and str(bid) == raw_clean:
                return bid
        # Fallback: id appears anywhere in the (possibly verbose) answer.
        for b in branches:
            bid = b.get("id")
            if bid is not None and str(bid) in raw_clean:
                return bid
        other = next((b for b in branches if b.get("isOther")), None)
        return other.get("id") if other else branches[0].get("id")
