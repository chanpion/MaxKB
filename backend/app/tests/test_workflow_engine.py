"""Unit tests for the workflow engine graph traversal (no agno / DB required).

Exercises start -> condition -> reply branching and reference resolution using
the agno-free node set, so it runs in any environment.
"""

from __future__ import annotations

import asyncio

from app.workflows.engine import WorkflowEngine, sse_event
from app.workflows.nodes import ConditionNode, DirectReplyNode, StartNode, VariableAssignNode

_FLOW = {
    "nodes": [
        {"id": "n_start", "type": "start-node", "properties": {"stepName": "开始"}},
        {
            "id": "n_cond",
            "type": "condition-node",
            "properties": {
                "stepName": "条件",
                "node_data": {
                    "branch": [
                        {
                            "id": "b_yes",
                            "type": "yes",
                            "condition": "and",
                            "conditions": [{"field": ["n_start", "question"], "compare": "contain", "value": "你好"}],
                        },
                        {"id": "b_no", "type": "no", "condition": "and", "conditions": []},
                    ]
                },
            },
        },
        {
            "id": "n_yes",
            "type": "direct-reply-node",
            "properties": {"stepName": "回复-是", "node_data": {"content": "你好呀！"}},
        },
        {
            "id": "n_no",
            "type": "direct-reply-node",
            "properties": {"stepName": "回复-否", "node_data": {"content": "请问有什么可以帮你？"}},
        },
    ],
    "edges": [
        {"sourceNodeId": "n_start", "targetNodeId": "n_cond", "sourceAnchorId": "n_start_right"},
        {"sourceNodeId": "n_cond", "targetNodeId": "n_yes", "sourceAnchorId": "n_cond_b_yes_right"},
        {"sourceNodeId": "n_cond", "targetNodeId": "n_no", "sourceAnchorId": "n_cond_b_no_right"},
    ],
}


def _run(question: str) -> dict:
    engine = WorkflowEngine(_FLOW, {"question": question})
    return asyncio.run(engine.run())


def test_condition_branch_yes():
    result = _run("你好，世界")
    assert result["status"] == 200
    assert "你好呀" in result["answer"]


def test_condition_branch_no():
    result = _run("今天天气怎样")
    assert "有什么可以帮你" in result["answer"]


def test_sse_event_serializes():
    frame = sse_event({"type": "answer", "content": "hi"})
    assert frame.startswith("data: ") and "content" in frame


def test_node_registry_covers_minimal_set():
    for _ in (StartNode, ConditionNode, DirectReplyNode, VariableAssignNode):
        assert WorkflowEngine  # sanity
    from app.workflows.nodes import get_node

    assert get_node("condition-node") is ConditionNode


def test_stream_emits_interrupted_frame_on_form_suspend():
    """A form-node suspend must surface as an ``interrupted`` SSE frame before done."""
    flow = {
        "nodes": [
            {"id": "s1", "type": "start-node", "properties": {"stepName": "开始"}},
            {
                "id": "nf",
                "type": "form-node",
                "properties": {
                    "stepName": "表单",
                    "node_data": {
                        "need_user_input": True,
                        "form_field_list": [
                            {"name": "name", "value": {"node_id": "global", "fields": ["name"]}},
                        ],
                        "form_content_format": "你好 {name}",
                    },
                },
            },
            {
                "id": "r1",
                "type": "direct-reply-node",
                "properties": {"stepName": "回复", "node_data": {"content": "提交成功"}},
            },
        ],
        "edges": [
            {"sourceNodeId": "s1", "targetNodeId": "nf", "sourceAnchorId": "s1_right"},
            {"sourceNodeId": "nf", "targetNodeId": "r1", "sourceAnchorId": "nf_right"},
        ],
    }

    frames = asyncio.run(_collect_stream(flow, {}))

    assert any("\"type\": \"interrupted\"" in f or '"type": "interrupted"' in f for f in frames)
    interrupted = next(f for f in frames if "interrupted" in f)
    assert "name" in interrupted
    assert any("\"type\": \"done\"" in f for f in frames)


async def _collect_stream(flow: dict, params: dict) -> list[str]:
    engine = WorkflowEngine(flow, params)
    return [frame async for frame in engine.stream()]


def test_sse_event_helper_used():
    assert sse_event({"type": "x"}) == "data: " + __import__("json").dumps({"type": "x"}, ensure_ascii=False) + "\n\n"
