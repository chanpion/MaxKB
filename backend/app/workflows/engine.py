"""Workflow engine: loads a MaxKB ``flow`` graph and executes it.

The engine is intentionally lightweight — it drives graph traversal itself
(necessary because MaxKB flows are *user-defined* graphs, not a static Agno
DAG), but every node delegates to Agno-native primitives where possible:

  * LLM node      -> ``agno.agent.Agent`` (via ``app.providers.get_llm``)
  * Knowledge node-> ``app.rag.retriever.PgVectorRetriever`` (existing pgvector)
  * Tool node     -> Agno Function tools (catalogue in Stage 8, ``app.tools``)

The traversal mirrors ``application.flow.workflow_manage.WorkflowManage``:
start node -> execute -> resolve next nodes from edges (with branch-anchor
matching for condition nodes and AND/OR fan-in) -> recurse. A node is a
"result" node when ``node_data.is_result`` is set or it has no successors.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.workflows.modes import DEFAULT_WORKFLOW_MODE, WorkflowMode
from app.workflows.nodes import get_node
from app.workflows.nodes.base import NodeResult, StepNode
from app.workflows.state import WorkflowState, serialize


def sse_event(payload: dict[str, Any]) -> str:
    return "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"


def _anchor(node_id: str, branch_id: str | None) -> str:
    if branch_id:
        return f"{node_id}_{branch_id}_right"
    return f"{node_id}_right"


class WorkflowEngine:
    def __init__(
        self,
        flow: dict[str, Any],
        params: dict[str, Any],
        *,
        model_config: dict[str, Any] | None = None,
        embedding_config: dict[str, Any] | None = None,
    ) -> None:
        self.flow = flow
        self.params = params
        self.params.setdefault("model_config", model_config or {})
        self.params.setdefault("embedding_config", embedding_config or {})
        self.nodes = {n["id"]: n for n in flow.get("nodes", [])}
        self.edges = flow.get("edges", [])
        # The flow declares which mode it runs in (application / knowledge /
        # tool, optionally looped). This mirrors Django's
        # ``WorkflowManage.flow.workflow_mode`` and selects the right node
        # implementation via the nested node registry.
        raw_mode = flow.get("workflow_mode", DEFAULT_WORKFLOW_MODE.value)
        try:
            self.workflow_mode: WorkflowMode = WorkflowMode(raw_mode)
        except ValueError:
            self.workflow_mode = DEFAULT_WORKFLOW_MODE
        self.node_names = {
            nid: (n.get("properties", {}) or {}).get("stepName", n.get("type", "")) for nid, n in self.nodes.items()
        }
        self.state = WorkflowState(params, node_names=self.node_names)
        # Workflow params are exposed as ``global.<key>`` so nodes can reference
        # them (e.g. a resumed form reads the supplied value as global.<name>).
        for _k, _v in self.params.items():
            if _k not in ("model_config", "embedding_config"):
                self.state.global_context.setdefault(_k, _v)
        self.executed: set[str] = set()
        self.runtime_details: dict[str, Any] = {}
        self.answers: list[str] = []
        self.interrupted: NodeResult | None = None

    # ----------------------------- graph helpers ----------------------------- #
    def _start_node_id(self) -> str:
        for nid, n in self.nodes.items():
            if n.get("type") == "start-node":
                return nid
        raise RuntimeError("flow has no start-node")

    def _outgoing(self, node_id: str) -> list[dict[str, Any]]:
        return [e for e in self.edges if e.get("sourceNodeId") == node_id]

    def _up_node_ids(self, node_id: str) -> list[str]:
        return [e.get("sourceNodeId") for e in self.edges if e.get("targetNodeId") == node_id]

    def _make_node(self, node_id: str, up_node_id_list: list[str]) -> StepNode:
        node = self.nodes[node_id]
        cls = get_node(node.get("type"), self.workflow_mode)
        if cls is None:
            raise RuntimeError(f"unsupported node type: {node.get('type')}")
        return cls(node, self.state, up_node_id_list)

    def _next_nodes(self, current: StepNode, result: NodeResult) -> list[str]:
        if result.interrupt:
            return []
        out = self._outgoing(current.id)
        candidates: list[str] = []
        for edge in out:
            anchor = edge.get("sourceAnchorId")
            if result.is_assertion_result:
                if _anchor(current.id, result.branch_id) == anchor:
                    candidates.append(edge["targetNodeId"])
            else:
                if _anchor(current.id, None) == anchor:
                    candidates.append(edge["targetNodeId"])
        # Resolve AND/OR fan-in: a target with condition=AND waits until all its
        # (active) incoming edges are satisfied; OR fires as soon as one arrives.
        ready: list[str] = []
        for tid in candidates:
            target = self.nodes[tid]
            if target.get("properties", {}).get("disabled"):
                continue
            cond = (target.get("properties", {}) or {}).get("condition", "AND")
            if cond == "OR":
                ready.append(tid)
            else:
                if self._dependent_executed(tid):
                    ready.append(tid)
        return ready

    def _dependent_executed(self, node_id: str) -> bool:
        for src_id in self._up_node_ids(node_id):
            src = self.nodes.get(src_id)
            if src is None:
                continue
            # The source must have run and finished.
            if src_id not in self.executed:
                return False
        return True

    def _has_next(self, node_id: str) -> bool:
        return len(self._outgoing(node_id)) > 0

    # ------------------------------- execution ------------------------------- #
    async def _exec_node(self, node_id: str, up_node_id_list: list[str], queue):
        """Execute a single node and return its candidates ``(next_id, up_list)``."""
        node = self._make_node(node_id, up_node_id_list)
        if node.disabled:
            self.executed.add(node_id)
            return []
        if queue is not None:
            await queue.put(("node_start", self._node_meta(node)))

        result: NodeResult
        try:
            result = await node.execute()
        except Exception as e:
            if node.enable_exception:
                result = NodeResult(
                    {"exception_message": str(e)},
                    status=500,
                    exception_message=str(e),
                    branch_id="exception",
                )
            else:
                if queue is not None:
                    await queue.put(("node_error", {**self._node_meta(node), "error": str(e)}))
                raise

        result.write_context(node, self.state)
        if result.interrupt:
            self.interrupted = result
        self.executed.add(node_id)
        self.runtime_details[node.id] = self._details(node, result)

        is_result = node.is_result
        if is_result is None:
            is_result = not self._has_next(node_id)
        if is_result and result.node_variable.get("answer") is not None:
            self.answers.append(str(result.node_variable.get("answer")))

        if queue is not None:
            await queue.put(
                (
                    "node_end",
                    {**self._node_meta(node), "is_result": bool(is_result), "status": result.status},
                )
            )

        if result.status == 500 and not node.enable_exception:
            return []

        candidates = []
        for tid in self._next_nodes(node, result):
            candidates.append((tid, [*up_node_id_list, node_id]))
        return candidates

    async def _drive(self, queue=None):
        """Iterative graph driver with AND-fan-in re-evaluation.

        A node whose AND dependencies are not yet satisfied is parked in
        ``pending`` and re-checked after every execution, so diamond-shaped
        joins resolve correctly.
        """
        ready = [(self._start_node_id(), [])]
        pending: list[tuple] = []
        while ready or pending:
            progressed = False
            still_pending: list[tuple] = []
            batch = ready + pending
            ready = []
            pending = []
            for node_id, up_list in batch:
                if node_id in self.executed:
                    progressed = True
                    continue
                # For AND-join targets, ensure all upstream executed.
                if not self._dependent_executed(node_id):
                    still_pending.append((node_id, up_list))
                    continue
                candidates = await self._exec_node(node_id, up_list, queue)
                progressed = True
                for nid, upl in candidates:
                    if nid in self.executed:
                        continue
                    if self._dependent_executed(nid):
                        ready.append((nid, upl))
                    else:
                        still_pending.append((nid, upl))
            if not progressed and not ready:
                break
            pending = still_pending

    # ------------------------------- public API ------------------------------ #
    async def run(self) -> dict[str, Any]:
        await self._drive()
        if self.interrupted is not None:
            # Workflow suspended at an interrupting node (e.g. a form awaiting
            # user input). Callers resume by re-running the engine with the
            # missing values supplied via params / global context.
            return {
                "answer": "",
                "details": self.runtime_details,
                "status": 423,
                "interrupted": True,
                "form": self.interrupted.node_variable,
            }
        return self._finalize()

    async def stream(self):
        queue: asyncio.Queue = asyncio.Queue()
        self.state.on_chunk = lambda text: queue.put_nowait(("chunk", (None, text)))

        async def producer() -> None:
            try:
                await self._drive(queue=queue)
            except Exception as e:  # pragma: no cover - propagate as SSE error
                await queue.put(("error", {"message": str(e)}))
            finally:
                await queue.put(("done", None))

        prod = asyncio.create_task(producer())
        while True:
            kind, payload = await queue.get()
            if kind == "done":
                break
            if kind == "chunk":
                _, text = payload
                yield sse_event({"type": "answer", "content": text})
            elif kind == "node_start":
                yield sse_event({"type": "node_start", **payload})
            elif kind == "node_end":
                yield sse_event({"type": "node_end", **payload})
            elif kind == "node_error":
                yield sse_event({"type": "node_error", **payload})
            elif kind == "error":
                yield sse_event({"type": "error", **payload})
        await prod
        if self.interrupted is not None:
            # A node (e.g. form) suspended the workflow awaiting user input.
            # Surface it as an ``interrupted`` frame so the client can render
            # the form and resume by re-running the engine with the values.
            yield sse_event(
                {"type": "interrupted", "form": self.interrupted.node_variable, "details": self.runtime_details}
            )
        final = self._finalize()
        yield sse_event({"type": "done", "answer": final["answer"], "details": final["details"]})

    # ------------------------------- helpers --------------------------------- #
    def _node_meta(self, node: StepNode) -> dict[str, Any]:
        return {
            "node_id": node.id,
            "node_type": node.type,
            "node_name": node.step_name,
        }

    def _details(self, node: StepNode, result: NodeResult) -> dict[str, Any]:
        return serialize(
            {
                "node_id": node.id,
                "node_type": node.type,
                "name": node.step_name,
                "run_time": node.context.get("run_time"),
                "status": result.status,
                "branch_id": result.branch_id,
                "err_message": result.exception_message,
                "context": result.node_variable,
            }
        )

    def _finalize(self) -> dict[str, Any]:
        answer = "\n\n".join(a for a in self.answers if a)
        return {
            "answer": answer,
            "details": self.runtime_details,
            "status": 200 if all(d.get("status") == 200 for d in self.runtime_details.values()) else 500,
        }
