"""Workflow node registry.

Maps a node ``type`` string (matching MaxKB's ``flow`` JSON) to its
:class:`StepNode` implementation. The minimal set (LLM / knowledge / tool /
condition / reply / variable) is implemented here; the remaining nodes from
``apps/application/flow/step_node`` are progressively migrated and simply added
to ``node_map``.

Stage 9 migrated the full set — 36 node types, aligned with the legacy Django
workflow engine.
"""

from __future__ import annotations

from app.workflows.nodes.application import ApplicationNode
from app.workflows.nodes.base import StepNode
from app.workflows.nodes.condition import ConditionNode
from app.workflows.nodes.data_source_local import DataSourceLocalNode
from app.workflows.nodes.data_source_web import DataSourceWebNode
from app.workflows.nodes.direct_reply import DirectReplyNode
from app.workflows.nodes.document_extract import DocumentExtractNode
from app.workflows.nodes.document_split import DocumentSplitNode
from app.workflows.nodes.form import FormNode
from app.workflows.nodes.image_generate import ImageGenerateNode
from app.workflows.nodes.image_to_video import ImageToVideoNode
from app.workflows.nodes.image_understand import ImageUnderstandNode
from app.workflows.nodes.intent import IntentNode
from app.workflows.nodes.knowledge_write import KnowledgeWriteNode
from app.workflows.nodes.llm_chat import LLMChatNode
from app.workflows.nodes.loop import LoopNode
from app.workflows.nodes.loop_break import LoopBreakNode
from app.workflows.nodes.loop_continue import LoopContinueNode
from app.workflows.nodes.loop_start import LoopStartNode
from app.workflows.nodes.mcp import MCPNode
from app.workflows.nodes.parameter_extract import ParameterExtractNode
from app.workflows.nodes.question import QuestionNode
from app.workflows.nodes.rerank import RerankNode
from app.workflows.nodes.search_document import SearchDocumentNode
from app.workflows.nodes.search_knowledge import SearchKnowledgeNode
from app.workflows.nodes.speech_to_text import SpeechToTextNode
from app.workflows.nodes.start import StartNode
from app.workflows.nodes.text_to_speech import TextToSpeechNode
from app.workflows.nodes.text_to_video import TextToVideoNode
from app.workflows.nodes.tool import ToolNode
from app.workflows.nodes.tool_lib import ToolLibNode
from app.workflows.nodes.tool_start import ToolStartNode
from app.workflows.nodes.tool_workflow import ToolWorkflowNode
from app.workflows.nodes.variable_aggregate import VariableAggregateNode
from app.workflows.nodes.variable_assign import VariableAssignNode
from app.workflows.nodes.variable_split import VariableSplitNode
from app.workflows.nodes.video_understand import VideoUnderstandNode

# All 36 node types (aligned with the legacy Django workflow engine).
node_map: dict[str, type[StepNode]] = {
    # --- Stage 7 base set (12) ---
    StartNode.type: StartNode,
    QuestionNode.type: QuestionNode,
    LLMChatNode.type: LLMChatNode,
    SearchKnowledgeNode.type: SearchKnowledgeNode,
    ToolNode.type: ToolNode,
    ConditionNode.type: ConditionNode,
    DirectReplyNode.type: DirectReplyNode,
    VariableAssignNode.type: VariableAssignNode,
    RerankNode.type: RerankNode,
    FormNode.type: FormNode,
    IntentNode.type: IntentNode,
    ImageUnderstandNode.type: ImageUnderstandNode,
    # --- Stage 9 batch 1: workflow engine core (5) ---
    LoopNode.type: LoopNode,
    LoopStartNode.type: LoopStartNode,
    LoopBreakNode.type: LoopBreakNode,
    LoopContinueNode.type: LoopContinueNode,
    ApplicationNode.type: ApplicationNode,
    # --- Stage 9 batch 2: simple / config nodes (6) ---
    VariableSplitNode.type: VariableSplitNode,
    VariableAggregateNode.type: VariableAggregateNode,
    DataSourceWebNode.type: DataSourceWebNode,
    DataSourceLocalNode.type: DataSourceLocalNode,
    ToolStartNode.type: ToolStartNode,
    DocumentSplitNode.type: DocumentSplitNode,
    # --- Stage 9 batch 3: Agno-simplified nodes (6) ---
    MCPNode.type: MCPNode,
    ParameterExtractNode.type: ParameterExtractNode,
    ToolLibNode.type: ToolLibNode,
    ToolWorkflowNode.type: ToolWorkflowNode,
    KnowledgeWriteNode.type: KnowledgeWriteNode,
    DocumentExtractNode.type: DocumentExtractNode,
    # --- Stage 9 batch 4: multimedia nodes (7) ---
    SearchDocumentNode.type: SearchDocumentNode,
    ImageGenerateNode.type: ImageGenerateNode,
    VideoUnderstandNode.type: VideoUnderstandNode,
    TextToSpeechNode.type: TextToSpeechNode,
    SpeechToTextNode.type: SpeechToTextNode,
    ImageToVideoNode.type: ImageToVideoNode,
    TextToVideoNode.type: TextToVideoNode,
}

# Legacy ``reply-node`` alias (backend used ``direct-reply-node``).
node_map["reply-node"] = DirectReplyNode


def register_node(node_cls: type[StepNode]) -> None:
    node_map[node_cls.type] = node_cls


def get_node(node_type: str) -> type[StepNode] | None:
    return node_map.get(node_type)
