"""Tests for Stage 9 batch 2 nodes (simple / config nodes). No real DB/LLM."""

from __future__ import annotations

import asyncio

from app.workflows.nodes.data_source_local import DataSourceLocalNode
from app.workflows.nodes.data_source_web import DataSourceWebNode
from app.workflows.nodes.document_split import DocumentSplitNode
from app.workflows.nodes.tool_start import ToolStartNode
from app.workflows.nodes.variable_aggregate import VariableAggregateNode
from app.workflows.nodes.variable_split import VariableSplitNode, _navigate_path
from app.workflows.state import WorkflowState


def _state_with(upstream: dict) -> WorkflowState:
    state = WorkflowState({})
    for nid, ctx in upstream.items():
        state.set_node_context(nid, nid, ctx)
    return state


async def _run(node: object) -> object:
    return await node.execute()


def test_navigate_path_basic():
    data = {"a": {"b": [10, 20, {"c": "x"}]}}
    assert _navigate_path(data, "$.a.b[2].c") == "x"
    assert _navigate_path(data, "a.b[0]") == 10
    assert _navigate_path(data, "a.missing") is None


def test_variable_split_extracts_fields():
    state = _state_with({"n1": {"data": {"name": "x", "items": [1, 2]}}})
    node = VariableSplitNode(
        {
            "id": "v",
            "type": "variable-splitting-node",
            "properties": {
                "stepName": "拆分",
                "node_data": {
                    "input_variable": ["n1", "data"],
                    "variable_list": [
                        {"field": "nm", "expression": "$.name"},
                        {"field": "first", "expression": "$.items[0]"},
                    ],
                },
            },
        },
        state,
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["nm"] == "x"
    assert result.node_variable["first"] == 1


def test_variable_aggregate_first_non_null():
    state = _state_with({"n1": {"val": None}, "n2": {"val": "hi"}})
    node = VariableAggregateNode(
        {
            "id": "a",
            "type": "variable-aggregation-node",
            "properties": {
                "stepName": "聚合",
                "node_data": {
                    "strategy": "first_non_null",
                    "group_list": [
                        {
                            "id": "g1",
                            "field": "g1",
                            "variable_list": [
                                {"v_id": "a", "variable": ["n1", "val"]},
                                {"v_id": "b", "variable": ["n2", "val"]},
                            ],
                        }
                    ],
                },
            },
        },
        state,
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["result"] == "hi"


def test_variable_aggregate_array():
    state = _state_with({"n1": {"val": 1}, "n2": {"val": 2}})
    node = VariableAggregateNode(
        {
            "id": "a",
            "type": "variable-aggregation-node",
            "properties": {
                "stepName": "聚合",
                "node_data": {
                    "strategy": "array",
                    "group_list": [
                        {
                            "id": "g1",
                            "field": "g1",
                            "variable_list": [
                                {"v_id": "a", "variable": ["n1", "val"]},
                                {"v_id": "b", "variable": ["n2", "val"]},
                            ],
                        }
                    ],
                },
            },
        },
        state,
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["result"] == [1, 2]


def test_data_source_web_passthrough():
    state = WorkflowState({})
    node = DataSourceWebNode(
        {
            "id": "d",
            "type": "data-source-web-node",
            "properties": {
                "stepName": "Web",
                "node_data": {"url_list": ["http://a"], "crawl_strategy": "depth"},
            },
        },
        state,
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["source_type"] == "web"
    assert result.node_variable["url_list"] == ["http://a"]


def test_data_source_local_passthrough():
    state = WorkflowState({})
    node = DataSourceLocalNode(
        {
            "id": "d",
            "type": "data-source-local-node",
            "properties": {
                "stepName": "Local",
                "node_data": {"file_type_list": ["pdf"], "file_size_limit": 10, "file_count_limit": 5},
            },
        },
        state,
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["file_type_list"] == ["pdf"]


def test_tool_start_passthrough():
    state = WorkflowState({})
    node = ToolStartNode(
        {"id": "t", "type": "tool-start-node", "properties": {"stepName": "T", "node_data": {}}},
        state,
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable == {}


def test_document_split_config():
    state = WorkflowState({})
    node = DocumentSplitNode(
        {
            "id": "s",
            "type": "document-split-node",
            "properties": {
                "stepName": "Split",
                "node_data": {"chunk_size": 512, "split_strategy": "custom"},
            },
        },
        state,
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["chunk_size"] == 512
    assert result.node_variable["split_strategy"] == "custom"
