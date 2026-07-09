"""MCP node: invoke a tool exposed by an MCP (Model Context Protocol) server.

Uses Agno's native ``agno.tools.mcp.MCPTools`` to connect to a server (stdio /
SSE / streamable-http), enumerate its tools and call a single named tool with
the configured arguments. Replaces the legacy ``langchain_mcp_adapters`` based
implementation.
"""

from __future__ import annotations

import json
from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class MCPNode(StepNode):
    type = "mcp-node"

    def _servers(self) -> dict[str, Any]:
        raw = self.resolve(self.node_data.get("mcp_servers")) or {}
        if isinstance(raw, str):
            raw = json.loads(raw) if raw else {}
        return raw or {}

    def _tool_name(self) -> str:
        return self.resolve(self.node_data.get("mcp_tool")) or ""

    def _tool_params(self) -> dict[str, Any]:
        params = self.resolve(self.node_data.get("tool_params")) or {}
        if isinstance(params, str):
            params = json.loads(params) if params else {}
        return params or {}

    def _server_config(self) -> dict[str, Any]:
        servers = self._servers()
        server_key = self.resolve(self.node_data.get("mcp_server")) or ""
        if isinstance(server_key, dict):
            return server_key
        if server_key and server_key in servers:
            return servers[server_key]
        return next(iter(servers.values()), {}) if servers else {}

    async def execute(self) -> NodeResult:
        tool_name = self._tool_name()
        if not tool_name:
            return NodeResult(
                {"result": "", "exception_message": "mcp_tool is required"},
                status=500,
                exception_message="mcp_tool is required",
            )

        server_cfg = self._server_config()
        tool_params = self._tool_params()

        try:
            from agno.tools.mcp import MCPTools
        except ImportError as e:
            return NodeResult(
                {"result": "", "exception_message": f"mcp package not installed: {e}"},
                status=500,
                exception_message=f"mcp package not installed: {e}",
            )

        kwargs: dict[str, Any] = {"include_tools": [tool_name]}
        if server_cfg.get("command"):
            kwargs["command"] = server_cfg["command"]
        if server_cfg.get("url"):
            kwargs["url"] = server_cfg["url"]
        if server_cfg.get("transport"):
            kwargs["transport"] = server_cfg["transport"]
        if server_cfg.get("env"):
            kwargs["env"] = server_cfg["env"]

        try:
            async with MCPTools(**kwargs) as mcp:
                try:
                    await mcp.initialize()
                except Exception:
                    pass
                fn = mcp.functions.get(tool_name)
                if fn is None:
                    return NodeResult(
                        {"result": "", "exception_message": f"tool '{tool_name}' not found"},
                        status=500,
                        exception_message=f"tool '{tool_name}' not found",
                    )
                result = await fn.entrypoint(**tool_params)
        except Exception as e:  # pragma: no cover - network/server failure
            if self.enable_exception:
                return NodeResult(
                    {"result": "", "exception_message": str(e)},
                    status=500,
                    exception_message=str(e),
                    branch_id="exception",
                )
            raise

        return NodeResult(
            {"result": result, "data": str(result)},
            is_result=self.is_result if self.is_result is not None else False,
        )
