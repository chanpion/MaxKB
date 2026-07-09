"""Web data source node: configures a web-based data source for ingestion.

Mirrors ``flow.step_node.data_source_web_node``. This is a configuration /
placeholder node — it surfaces the web data-source parameters (e.g. URLs and
crawl settings) to the downstream document-split / knowledge-write nodes. No
external call happens here.
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class DataSourceWebNode(StepNode):
    type = "data-source-web-node"

    async def execute(self) -> NodeResult:
        # Pass through the configured web source settings for downstream nodes.
        config = {
            "source_type": "web",
            "url_list": self.resolve(self.node_data.get("url_list")) or [],
            "selector": self.resolve(self.node_data.get("selector")),
            "crawl_strategy": self.resolve(self.node_data.get("crawl_strategy")),
            "interval": self.resolve(self.node_data.get("interval")),
        }
        return NodeResult(config, is_result=False)
