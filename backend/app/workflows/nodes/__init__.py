# coding=utf-8
"""Workflow node registry.

Maps a node ``type`` string (matching MaxKB's ``flow`` JSON) to its
:class:`StepNode` implementation. The minimal set (LLM / knowledge / tool /
condition / reply / variable) is implemented here; the remaining ~140 nodes
from ``apps/application/flow/step_node`` are progressively migrated and simply
added to ``node_map`` (see ``SANDBOX`` note in ``app.workflows.sandbox``).
"""
from __future__ import annotations

from typing import Dict, Type

from app.workflows.nodes.base import StepNode
from app.workflows.nodes.condition import ConditionNode
from app.workflows.nodes.direct_reply import DirectReplyNode
from app.workflows.nodes.llm_chat import LLMChatNode
from app.workflows.nodes.search_knowledge import SearchKnowledgeNode
from app.workflows.nodes.start import StartNode
from app.workflows.nodes.tool import ToolNode
from app.workflows.nodes.variable_assign import VariableAssignNode

# Minimal node set implemented for Stage 7.
node_map: Dict[str, Type[StepNode]] = {
    StartNode.type: StartNode,
    LLMChatNode.type: LLMChatNode,
    SearchKnowledgeNode.type: SearchKnowledgeNode,
    ToolNode.type: ToolNode,
    ConditionNode.type: ConditionNode,
    DirectReplyNode.type: DirectReplyNode,
    VariableAssignNode.type: VariableAssignNode,
}


def register_node(node_cls: Type[StepNode]) -> None:
    node_map[node_cls.type] = node_cls


def get_node(node_type: str) -> Type[StepNode] | None:
    return node_map.get(node_type)
