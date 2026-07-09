"""Unit tests for the migrated workflow nodes (no agno / DB / network required).

Covers rerank (score ordering), form (aggregation + template), intent
(LLM branch classification) and image-understand (multimodal call). The LLM /
vision calls are mocked so the node logic runs in any environment.
"""

from __future__ import annotations

import asyncio

from app.workflows.engine import WorkflowEngine
from app.workflows.nodes.image_understand import ImageUnderstandNode
from app.workflows.nodes.intent import IntentNode
from app.workflows.nodes.rerank import RerankNode
from app.workflows.state import WorkflowState


def _make_node(cls, node_data, params=None):
    state = WorkflowState(params or {})
    return cls(
        {"id": "x", "type": cls.type, "properties": {"stepName": "n", "node_data": node_data}},
        state,
    )


def test_rerank_orders_by_score():
    node = _make_node(
        RerankNode,
        {
            "reranker_setting": {"top_n": 2, "similarity": 0.0, "max_paragraph_char_number": 1000},
            "reranker_reference_list": [
                {"content": "low", "similarity": 0.2},
                {"content": "high", "similarity": 0.9},
            ],
            "question": "q",
            "show_knowledge": False,
        },
    )
    res = asyncio.run(node.execute())
    rl = res.node_variable["result_list"]
    assert [r["content"] for r in rl] == ["high", "low"]
    assert res.node_variable["result"] == "high\nlow"


def test_rerank_filters_by_similarity_and_top_n():
    node = _make_node(
        RerankNode,
        {
            "reranker_setting": {"top_n": 1, "similarity": 0.5, "max_paragraph_char_number": 1000},
            "reranker_reference_list": [
                {"content": "keep", "similarity": 0.9},
                {"content": "drop_low", "similarity": 0.1},
            ],
            "question": "q",
        },
    )
    res = asyncio.run(node.execute())
    rl = res.node_variable["result_list"]
    assert len(rl) == 1
    assert rl[0]["content"] == "keep"


def test_form_node_aggregates_and_renders():
    flow = {
        "nodes": [
            {"id": "s", "type": "start-node", "properties": {"stepName": "开始"}},
            {
                "id": "f",
                "type": "form-node",
                "properties": {
                    "stepName": "表单",
                    "node_data": {
                        "form_field_list": [
                            {"name": "name", "value": {"node_id": "s", "fields": ["question"]}},
                            {"name": "age", "default_value": 18},
                        ],
                        "form_content_format": "姓名：{name}，年龄：{age}",
                    },
                },
            },
        ],
        "edges": [{"sourceNodeId": "s", "targetNodeId": "f", "sourceAnchorId": "s_right"}],
    }
    engine = WorkflowEngine(flow, {"question": "张三"})
    result = asyncio.run(engine.run())
    ctx = result["details"]["f"]["context"]
    assert ctx["form_data"]["name"] == "张三"
    assert ctx["form_data"]["age"] == 18
    assert "姓名：张三，年龄：18" in ctx["form_content"]


class _FakeEvent:
    def __init__(self, content):
        self.content = content


class _FakeAgent:
    def __init__(self, *args, **kwargs):
        pass

    async def arun(self, message, images=None, stream=True):
        yield _FakeEvent("b2")


def test_intent_matches_branch(monkeypatch):
    import agno.agent as agent_mod

    import app.providers as providers_mod

    monkeypatch.setattr(agent_mod, "Agent", _FakeAgent)
    monkeypatch.setattr(providers_mod, "get_llm", lambda *a, **k: object())

    node = _make_node(
        IntentNode,
        {
            "content_list": {"node_id": "s", "fields": ["question"]},
            "branch": [
                {"id": "b1", "content": "退款", "isOther": False},
                {"id": "b2", "content": "物流", "isOther": False},
                {"id": "other", "content": "其他", "isOther": True},
            ],
        },
        params={"model_config": {"provider": "openai", "model_name": "x", "credential": {}}},
    )
    res = asyncio.run(node.execute())
    assert res.branch_id == "b2"
    assert res.node_variable["answer"] == "物流"


def test_intent_falls_back_to_other_without_model():
    node = _make_node(
        IntentNode,
        {
            "content_list": {"node_id": "s", "fields": ["question"]},
            "branch": [
                {"id": "b1", "content": "退款", "isOther": False},
                {"id": "other", "content": "其他", "isOther": True},
            ],
        },
    )
    res = asyncio.run(node.execute())
    assert res.branch_id == "other"


def test_image_understand_errors_without_model():
    node = _make_node(ImageUnderstandNode, {"prompt": "描述图片", "image_list": ["http://x/y.png"]})
    res = asyncio.run(node.execute())
    assert res.status == 500


def test_image_understand_mocked(monkeypatch):
    import agno.agent as agent_mod
    import agno.media as media_mod

    import app.providers as providers_mod

    monkeypatch.setattr(agent_mod, "Agent", _FakeAgent)
    monkeypatch.setattr(media_mod, "Image", lambda *a, **k: None)
    monkeypatch.setattr(providers_mod, "get_llm", lambda *a, **k: object())

    node = _make_node(
        ImageUnderstandNode,
        {"prompt": "描述图片", "image_list": ["http://x/y.png"]},
        params={"model_config": {"provider": "openai", "model_name": "x", "credential": {}}},
    )
    res = asyncio.run(node.execute())
    assert res.node_variable["answer"] == "b2"
