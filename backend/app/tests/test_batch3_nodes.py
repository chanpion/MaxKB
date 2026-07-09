"""Tests for Stage 9 batch 3 nodes (Agno-simplified). No real DB/LLM/MCP."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.workflows.nodes.document_extract import DocumentExtractNode
from app.workflows.nodes.knowledge_write import KnowledgeWriteNode
from app.workflows.nodes.mcp import MCPNode
from app.workflows.nodes.parameter_extract import ParameterExtractNode
from app.workflows.nodes.tool_lib import ToolLibNode
from app.workflows.nodes.tool_workflow import ToolWorkflowNode
from app.workflows.state import WorkflowState


def _state(params: dict | None = None) -> WorkflowState:
    return WorkflowState(params or {})


async def _run(node: object) -> object:
    return await node.execute()


# ------------------------------- MCP ------------------------------- #
class _FakeMCPFn:
    def __init__(self, ret: Any):
        self.ret = ret

    async def entrypoint(self, **kwargs: Any) -> Any:
        return self.ret


class _FakeMCP:
    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs

    async def __aenter__(self) -> _FakeMCP:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def initialize(self) -> None:
        pass

    @property
    def functions(self) -> dict[str, Any]:
        return {"my_tool": _FakeMCPFn({"ok": True})}


def test_mcp_node_calls_tool(monkeypatch):
    try:
        import agno.tools.mcp as mcp_mod
    except ImportError:
        pytest.skip("agno.tools.mcp requires the 'mcp' package")
    monkeypatch.setattr(mcp_mod, "MCPTools", _FakeMCP)

    node = MCPNode(
        {
            "id": "m",
            "type": "mcp-node",
            "properties": {
                "stepName": "MCP",
                "node_data": {
                    "mcp_servers": {"s1": {"url": "http://x", "transport": "sse"}},
                    "mcp_server": "s1",
                    "mcp_tool": "my_tool",
                    "tool_params": {"q": "hi"},
                },
            },
        },
        _state(),
        [],
    )
    result = asyncio.run(_run(node))
    assert result.status == 200
    assert result.node_variable["result"] == {"ok": True}


# ------------------------- parameter extract ------------------------- #
class _FakeExtracted:
    def model_dump(self) -> dict[str, Any]:
        return {"name": "Alice", "age": 30}


class _FakeAgentRun:
    content = _FakeExtracted()


class _FakeAgent:
    def __init__(self, *args: Any, **kwargs: Any):
        self.kwargs = kwargs

    async def arun(self, message: str, **kwargs: Any):
        return _FakeAgentRun()


def test_parameter_extract(monkeypatch):
    import agno.agent as agent_mod

    import app.providers as providers_mod

    monkeypatch.setattr(agent_mod, "Agent", _FakeAgent)
    monkeypatch.setattr(providers_mod, "get_llm", lambda *a, **k: object())

    node = ParameterExtractNode(
        {
            "id": "p",
            "type": "parameter-extraction-node",
            "properties": {
                "stepName": "Extract",
                "node_data": {
                    "input": "My name is Alice and I am 30",
                    "fields": [
                        {"name": "name", "type": "str"},
                        {"name": "age", "type": "int"},
                    ],
                },
            },
        },
        _state({"model_config": {"provider": "openai", "model_name": "gpt", "credential": {}}}),
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["result"] == {"name": "Alice", "age": 30}


# ------------------------------ tool lib ----------------------------- #
class _FakeTool:
    id = "builtin:fake"

    async def invoke(self, state, inputs):
        return {"echo": inputs}


def test_tool_lib_node(monkeypatch):
    import app.tools as tools_mod

    monkeypatch.setattr(tools_mod, "get_tool", lambda tid: _FakeTool())

    node = ToolLibNode(
        {
            "id": "t",
            "type": "tool-lib-node",
            "properties": {
                "stepName": "ToolLib",
                "node_data": {"tool_ids": ["builtin:fake"], "input": {"x": 1}},
            },
        },
        _state(),
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["result"]["builtin:fake"] == {"echo": {"x": 1}}


# ---------------------------- tool workflow -------------------------- #
class _FakeTWAgent:
    def __init__(self, *a, **k):
        pass

    async def arun(self, message, stream=False):
        for chunk in ["done"]:
            yield SimpleNamespace(content=chunk)


def test_tool_workflow_node(monkeypatch):
    import agno.agent as agent_mod

    import app.providers as providers_mod
    import app.tools as tools_mod

    monkeypatch.setattr(agent_mod, "Agent", _FakeTWAgent)
    monkeypatch.setattr(providers_mod, "get_llm", lambda *a, **k: object())
    monkeypatch.setattr(tools_mod, "get_agno_tools", lambda ids: [])

    node = ToolWorkflowNode(
        {
            "id": "tw",
            "type": "tool-workflow-lib-node",
            "properties": {
                "stepName": "ToolWF",
                "node_data": {"tool_ids": ["builtin:fake"], "prompt": "go"},
            },
        },
        _state({"model_config": {"provider": "openai", "model_name": "gpt", "credential": {}}}),
        [],
    )
    result = asyncio.run(_run(node))
    assert "done" in result.node_variable["answer"]


# ---------------------------- knowledge write ------------------------ #
class _FakeIngestResult:
    paragraph_count = 3
    embedding_count = 5


class _FakeKBSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def commit(self):
        pass


def test_knowledge_write_node(monkeypatch):
    import app.core.db as db_mod
    import app.rag.pipeline as pipeline_mod

    monkeypatch.setattr(db_mod, "SessionLocal", lambda: _FakeKBSession())
    monkeypatch.setattr(pipeline_mod, "ingest_document", lambda *a, **k: _make_result())

    async def _make_result():
        return _FakeIngestResult()

    node = KnowledgeWriteNode(
        {
            "id": "kw",
            "type": "knowledge-write-node",
            "properties": {
                "stepName": "KW",
                "node_data": {"knowledge_id": "kb1", "content": "hello world"},
            },
        },
        _state({"embedding_config": {"provider": "openai", "model_name": "t", "credential": {}}}),
        [],
    )
    result = asyncio.run(_run(node))
    assert result.status == 200
    assert result.node_variable["paragraph_count"] == 3


# ---------------------------- document extract ----------------------- #
def test_document_extract_node():
    node = DocumentExtractNode(
        {
            "id": "de",
            "type": "document-extract-node",
            "properties": {
                "stepName": "DE",
                "node_data": {"filename": "a.txt", "content": "hello world"},
            },
        },
        _state(),
        [],
    )
    result = asyncio.run(_run(node))
    assert "hello world" in result.node_variable["content"]
