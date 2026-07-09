# coding=utf-8
"""Agno-based workflow engine (Stage 7).

Replaces ``apps/application/flow`` with a provider-agnostic graph executor that
delegates to Agno-native primitives inside each node:

  * ``engine.WorkflowEngine`` — graph traversal + SSE streaming
  * ``nodes`` — minimal node set (start / llm / knowledge / tool / condition /
    reply / variable); remaining ~140 nodes documented in ``sandbox`` note
  * ``compare`` — condition comparators (ported from ``flow/compare``)
  * ``state`` — shared run context + reference resolution
  * ``sandbox`` — restricted execution boundary for code-bearing nodes
"""
from app.workflows.engine import WorkflowEngine, sse_event
from app.workflows.nodes import get_node, register_node
from app.workflows.state import WorkflowState

__all__ = [
    "WorkflowEngine",
    "sse_event",
    "get_node",
    "register_node",
    "WorkflowState",
]
