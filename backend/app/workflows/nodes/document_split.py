"""Document split node: configures how ingested documents are chunked.

Mirrors ``flow.step_node.document_split_node``. This is a configuration node —
it validates and forwards the split strategy, chunk size, patterns and related
settings so a downstream knowledge-write / ingestion node can apply them. No
splitting is performed here (the actual chunking lives in ``app.rag``).
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class DocumentSplitNode(StepNode):
    type = "document-split-node"

    async def execute(self) -> NodeResult:
        keys = [
            "document_list",
            "split_strategy",
            "paragraph_title_relate_problem_type",
            "paragraph_title_relate_problem",
            "paragraph_title_relate_problem_reference",
            "document_name_relate_problem_type",
            "document_name_relate_problem",
            "document_name_relate_problem_reference",
            "limit",
            "limit_type",
            "limit_reference",
            "chunk_size",
            "chunk_size_type",
            "chunk_size_reference",
            "patterns",
            "patterns_type",
            "patterns_reference",
            "with_filter",
            "with_filter_type",
            "with_filter_reference",
        ]
        config: dict[str, Any] = {}
        for key in keys:
            if key in self.node_data:
                config[key] = self.resolve(self.node_data.get(key))
        # Sensible defaults matching the legacy serializer.
        config.setdefault("split_strategy", "auto")
        config.setdefault("chunk_size", 256)
        config.setdefault("limit", 4096)
        return NodeResult(config, is_result=False)
