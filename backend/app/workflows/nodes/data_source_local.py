"""Local data source node: configures a local-file data source for ingestion.

Mirrors ``flow.step_node.data_source_local_node``. A configuration / placeholder
node that surfaces accepted file types, size and count limits to downstream
nodes. No file IO happens here.
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class DataSourceLocalNode(StepNode):
    type = "data-source-local-node"

    async def execute(self) -> NodeResult:
        config = {
            "source_type": "local",
            "file_type_list": self.resolve(self.node_data.get("file_type_list")) or [],
            "file_size_limit": self.resolve(self.node_data.get("file_size_limit")),
            "file_count_limit": self.resolve(self.node_data.get("file_count_limit")),
        }
        return NodeResult(config, is_result=False)
