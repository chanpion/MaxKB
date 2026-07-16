"""Workflow execution modes and per-node support table.

Mirrors ``application.flow.common.WorkflowMode`` and the ``support`` lists
declared on each Django ``INode`` subclass (``step_node/__init__.node_map`` is
built as ``{n.type: {w: n for w in n.support} ...}``). We keep the support
table in one place so :mod:`app.workflows.nodes` can rebuild the nested
``node_map`` and the engine can (optionally) validate a node against the
flow's ``workflow_mode``.
"""

from __future__ import annotations

from enum import Enum


class WorkflowMode(str, Enum):
    APPLICATION = "application"
    APPLICATION_LOOP = "application-loop"
    KNOWLEDGE = "knowledge"
    KNOWLEDGE_LOOP = "knowledge-loop"
    TOOL = "tool"
    TOOL_LOOP = "tool-loop"


# Default mode when a flow does not declare one (admin application flows).
DEFAULT_WORKFLOW_MODE = WorkflowMode.APPLICATION


# Per-node-type supported modes, aligned 1:1 with the Django ``support`` lists.
NODE_SUPPORT: dict[str, list[WorkflowMode]] = {
    "start-node": [WorkflowMode.APPLICATION],
    "question-node": [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP, WorkflowMode.KNOWLEDGE],
    "ai-chat-node": [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP, WorkflowMode.KNOWLEDGE_LOOP],
    "search-knowledge-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.TOOL,
        WorkflowMode.TOOL_LOOP,
    ],
    "tool-node": [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP, WorkflowMode.KNOWLEDGE],
    "condition-node": [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP, WorkflowMode.KNOWLEDGE],
    "direct-reply-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE_LOOP,
    ],
    "variable-assign-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "reranker-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.TOOL,
        WorkflowMode.TOOL_LOOP,
    ],
    "form-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.TOOL,
        WorkflowMode.TOOL_LOOP,
    ],
    "intent-node": [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP, WorkflowMode.KNOWLEDGE],
    "image-understand-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "application-node": [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP],
    "loop-node": [WorkflowMode.APPLICATION, WorkflowMode.KNOWLEDGE, WorkflowMode.TOOL],
    "loop-start-node": [
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE_LOOP,
        WorkflowMode.TOOL_LOOP,
    ],
    "loop-break-node": [
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE_LOOP,
        WorkflowMode.TOOL_LOOP,
    ],
    "loop-continue-node": [
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE_LOOP,
        WorkflowMode.TOOL_LOOP,
    ],
    "variable-splitting-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "parameter-extraction-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "variable-aggregation-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "data-source-local-node": [WorkflowMode.KNOWLEDGE],
    "data-source-web-node": [WorkflowMode.KNOWLEDGE],
    "tool-start-node": [WorkflowMode.TOOL],
    "document-split-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE_LOOP,
        WorkflowMode.KNOWLEDGE,
        WorkflowMode.TOOL,
        WorkflowMode.TOOL_LOOP,
    ],
    "mcp-node": [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP, WorkflowMode.KNOWLEDGE],
    "tool-lib-node": [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP, WorkflowMode.KNOWLEDGE],
    "tool-workflow-lib-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "knowledge-write-node": [WorkflowMode.KNOWLEDGE, WorkflowMode.KNOWLEDGE_LOOP],
    "document-extract-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE_LOOP,
    ],
    "search-document-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.TOOL,
        WorkflowMode.TOOL_LOOP,
    ],
    "image-generate-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "video-understand-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "text-to-speech-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "speech-to-text-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "text-to-video-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
    "image-to-video-node": [
        WorkflowMode.APPLICATION,
        WorkflowMode.APPLICATION_LOOP,
        WorkflowMode.KNOWLEDGE,
    ],
}
