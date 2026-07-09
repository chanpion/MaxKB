"""Tests for Stage 9 batch 1 nodes: loop family + application node.

These run without any real PostgreSQL / Redis — the loop body is a pure
in-memory flow, and the application node's DB access is monkeypatched.
"""

from __future__ import annotations

from app.workflows.nodes.application import ApplicationNode
from app.workflows.nodes.loop import LoopNode
from app.workflows.nodes.loop_break import LoopBreakNode
from app.workflows.nodes.loop_continue import LoopContinueNode
from app.workflows.nodes.loop_start import LoopStartNode
from app.workflows.state import WorkflowState


def _sub_flow(nodes, edges):
    return {"nodes": nodes, "edges": edges}


def _start():
    return {"id": "s1", "type": "start-node", "properties": {"stepName": "开始"}}


def _assign(id_, key, value):
    return {
        "id": id_,
        "type": "variable-assign-node",
        "properties": {
            "stepName": id_,
            "node_data": {"variables": [{"key": key, "value": value}]},
        },
    }


def _edge(src, tgt):
    return {"sourceNodeId": src, "targetNodeId": tgt, "sourceAnchorId": f"{src}_right", "targetAnchorId": f"{tgt}_left"}


def _make_loop_node(loop_type, **extra):
    node_data = {"loop_type": loop_type, **extra}
    return {
        "id": "loop1",
        "type": "loop-node",
        "properties": {"stepName": "循环", "node_data": node_data},
    }


async def test_loop_number_runs_n_times():
    body = _sub_flow([_start(), _assign("v1", "r", "x")], [_edge("s1", "v1")])
    state = WorkflowState({})
    node = LoopNode(_make_loop_node("NUMBER", number=3, loop_body=body), state, [])
    result = await node.execute()
    assert result.status == 200
    assert len(result.node_variable["loop_node_data"]) == 3
    assert result.node_variable["index"] == 2


async def test_loop_array_iterates_elements():
    body = _sub_flow([_start(), _assign("v1", "r", "x")], [_edge("s1", "v1")])
    state = WorkflowState({})
    node = LoopNode(_make_loop_node("ARRAY", array=[10, 20, 30, 40], loop_body=body), state, [])
    result = await node.execute()
    assert len(result.node_variable["loop_node_data"]) == 4
    assert result.node_variable["item"] == 40


async def test_loop_break_stops_early():
    body = _sub_flow(
        [_start(), {"id": "b1", "type": "loop-break-node", "properties": {"stepName": "中断", "node_data": {}}}],
        [_edge("s1", "b1")],
    )
    state = WorkflowState({})
    node = LoopNode(_make_loop_node("NUMBER", number=10, loop_body=body), state, [])
    result = await node.execute()
    # BREAK on the very first iteration.
    assert len(result.node_variable["loop_node_data"]) == 1


async def test_loop_continue_advances():
    # CONTINUE still runs the full iteration; it just advances to the next round.
    body = _sub_flow(
        [_start(), {"id": "c1", "type": "loop-continue-node", "properties": {"stepName": "继续", "node_data": {}}}],
        [_edge("s1", "c1")],
    )
    state = WorkflowState({})
    node = LoopNode(_make_loop_node("NUMBER", number=4, loop_body=body), state, [])
    result = await node.execute()
    assert len(result.node_variable["loop_node_data"]) == 4


async def test_loop_signal_nodes_instantiate():
    state = WorkflowState({})
    for cls in (LoopStartNode, LoopBreakNode, LoopContinueNode):
        n = cls({"id": "x", "type": cls.type, "properties": {"stepName": "t", "node_data": {}}}, state, [])
        res = await n.execute()
        assert res.status == 200


async def test_loop_start_is_passthrough():
    state = WorkflowState({})
    n = LoopStartNode(
        {"id": "x", "type": "loop-start-node", "properties": {"stepName": "t", "node_data": {}}}, state, []
    )
    res = await n.execute()
    assert res.node_variable == {}


# ----------------------------- application node ----------------------------- #
class _FakeResult:
    def scalar_one_or_none(self):
        return _FakeApp()


class _FakeApp:
    work_flow = _sub_flow(
        [
            _start(),
            {
                "id": "r1",
                "type": "direct-reply-node",
                "properties": {"stepName": "回复", "node_data": {"content": "sub answer"}},
            },
        ],
        [_edge("s1", "r1")],
    )


class _FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, *args, **kwargs):
        return _FakeResult()


async def test_application_node_runs_sub_flow(monkeypatch):
    import app.core.db as db_mod

    monkeypatch.setattr(db_mod, "SessionLocal", lambda: _FakeSession())

    node = {
        "id": "app1",
        "type": "application-node",
        "properties": {
            "stepName": "子应用",
            "node_data": {
                "application_id": "00000000-0000-0000-0000-000000000001",
                "question_reference_address": ["global", "question"],
            },
        },
    }
    state = WorkflowState({"question": "hi"})
    n = ApplicationNode(node, state, [])
    result = await n.execute()
    assert result.status == 200
    assert result.node_variable["answer"] == "sub answer"


async def test_application_node_missing_id():
    state = WorkflowState({})
    node = {
        "id": "app1",
        "type": "application-node",
        "properties": {"stepName": "子应用", "node_data": {}},
    }
    n = ApplicationNode(node, state, [])
    result = await n.execute()
    assert result.status == 500
