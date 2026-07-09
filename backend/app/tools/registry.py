"""Tool registry: maps tool ids to :class:`BaseTool` instances and builds Agno
tool lists for agents.

Mirrors the legacy ``apps/tools`` catalogue but is provider-agnostic. Custom
tools whose source lives in the ``tool`` table (``code`` column) are loaded via
:class:`~app.tools.code_tool.CodeTool`, executed inside the workflow sandbox.
"""

from __future__ import annotations

from typing import Any

from app.tools.base import BaseTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        key = tool.id or tool.name
        self._tools[key] = tool

    def get_tool(self, tool_id: str) -> BaseTool | None:
        return self._tools.get(tool_id)

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def get_agno_tools(self, tool_ids: list[str]) -> list[Any]:
        """Build a list of Agno Function tools for the given ids."""
        agno_tools: list[Any] = []
        for tid in tool_ids:
            tool = self.get_tool(tid)
            if tool is not None:
                agno_tools.append(tool.to_agno())
        return agno_tools


# Process-wide default registry (populated at startup from the DB / builtins).
registry = ToolRegistry()


def register_tool(tool: BaseTool) -> None:
    registry.register(tool)


def get_tool(tool_id: str) -> BaseTool | None:
    return registry.get_tool(tool_id)


def get_agno_tools(tool_ids: list[str]) -> list[Any]:
    return registry.get_agno_tools(tool_ids)
