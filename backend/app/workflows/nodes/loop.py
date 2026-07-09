"""Loop node: drives a child workflow as a loop body.

Mirrors ``flow.step_node.loop_node.impl.base_loop_node.BaseLoopNode``. Three
loop modes are supported (matching legacy ``loop_type``):

  * ``NUMBER`` — iterate ``number`` times, ``index`` = 0..n-1, ``item`` = index
  * ``ARRAY``  — iterate over ``array`` items, ``index`` = position, ``item`` = element
  * ``LOOP``   — unbounded while-style loop, bounded by ``max_loop_count``

On each iteration a fresh :class:`~app.workflows.engine.WorkflowEngine` is
created for ``loop_body`` with ``{"index": ..., "item": ...}`` injected into the
params. Two control signals produced by descendant nodes are honoured:

  * ``_loop_signal == "BREAK"``    -> stop the whole loop (break)
  * ``_loop_signal == "CONTINUE"`` -> finish current round, start next (continue)
  * ``_loop_interrupt``            -> a descendant (e.g. a future form node) needs
                                      human input; the whole workflow is suspended
                                      via ``NodeResult(interrupt=True)``.

All per-iteration runtime details and answers are collected and surfaced in the
node context, mirroring ``loop_node_data`` / ``loop_answer_data``.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode

DEFAULT_MAX_LOOP_COUNT = 500


class LoopNode(StepNode):
    type = "loop-node"

    # ----------------------------- helpers ----------------------------- #
    def _resolve_array(self) -> list[Any]:
        raw = self.node_data.get("array")
        if isinstance(raw, dict) and "node_id" in raw:
            value = self.resolve(raw)
        elif isinstance(raw, list) and raw and isinstance(raw[0], dict) and "node_id" in raw[0]:
            # array passed as a single-reference list [{"node_id":..., "fields":...}]
            value = self.resolve(raw[0])
        else:
            value = self.resolve(raw)
        return list(value) if isinstance(value, (list, tuple)) else []

    def _resolve_number(self) -> int:
        value = self.resolve(self.node_data.get("number"))
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _iteration_items(self, loop_type: str, array: list[Any], number: int) -> list[Any]:
        if loop_type == "ARRAY":
            return list(array)
        if loop_type == "NUMBER":
            return list(range(number))
        # LOOP (while): unbounded, bounded by max_loop_count at runtime.
        return list(range(DEFAULT_MAX_LOOP_COUNT))

    async def _run_iteration(self, index: int, item: Any, loop_body: dict[str, Any]) -> dict[str, Any]:
        params = dict(self.state.params)
        params["index"] = index
        params["item"] = item
        # Imported lazily to avoid a circular import (engine <-> nodes).
        from app.workflows.engine import WorkflowEngine

        engine = WorkflowEngine(loop_body, params)
        await engine.run()
        signal = engine.state.global_context.get("_loop_signal")
        # Collect non-internal global context for the outer scope.
        context = {k: v for k, v in engine.state.global_context.items() if not k.startswith("_loop")}
        return {
            "details": engine.runtime_details,
            "answers": engine.answers,
            "context": context,
            "signal": signal,
            "interrupted": bool(engine.state.global_context.get("_loop_interrupt", False)),
        }

    # ------------------------------ main ------------------------------- #
    async def execute(self) -> NodeResult:
        loop_type = self.node_data.get("loop_type")
        loop_body = self.node_data.get("loop_body") or {}
        if not loop_body:
            return NodeResult({}, is_result=False)

        array = self._resolve_array() if loop_type == "ARRAY" else []
        number = self._resolve_number() if loop_type == "NUMBER" else 0
        items = self._iteration_items(loop_type, array, number)

        max_count = DEFAULT_MAX_LOOP_COUNT
        loop_node_data: list[Any] = []
        loop_answer_data: list[Any] = []
        loop_context_data: dict[str, Any] = {}

        current_index = 0
        current_item: Any = None

        for index, item in enumerate(items):
            if 0 < max_count <= index:
                break
            current_index = index
            current_item = item
            res = await self._run_iteration(index, item, loop_body)
            if res["interrupted"]:
                # Suspend the whole workflow pending human input.
                return NodeResult(
                    {
                        "loop_context_data": loop_context_data,
                        "loop_node_data": loop_node_data,
                        "loop_answer_data": loop_answer_data,
                        "index": current_index,
                        "item": current_item,
                        "_loop_interrupt": True,
                    },
                    is_result=False,
                    interrupt=True,
                )
            loop_node_data.append(res["details"])
            loop_answer_data.append(res["answers"])
            loop_context_data.update(res["context"])
            if res["signal"] == "BREAK":
                break
            # CONTINUE (and any other signal) simply advances to the next round.

        aggregated_answer = "\n\n".join("\n\n".join(a for a in (ans or []) if a) for ans in loop_answer_data)
        return NodeResult(
            {
                "loop_context_data": loop_context_data,
                "loop_node_data": loop_node_data,
                "loop_answer_data": loop_answer_data,
                "index": current_index,
                "item": current_item,
                "answer": aggregated_answer,
            },
            is_result=False,
        )
