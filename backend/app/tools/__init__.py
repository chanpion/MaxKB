# coding=utf-8
"""Tools package (Stage 8).

Migrates MaxKB tools to Agno-native Function tools:

  * ``base.BaseTool``     — tool abstraction with both a low-level ``invoke``
                            (for the workflow ToolNode) and a ``to_agno`` wrapper.
  * ``registry``          — id -> tool map + ``get_agno_tools`` for agents.
  * ``builtin``           — example built-in tools (calculator / current_time).
  * ``code_tool.CodeTool``— executes user-authored ``tool.code`` in the sandbox.
"""
from app.tools.base import BaseTool
from app.tools.builtin import register_builtin_tools
from app.tools.registry import get_agno_tools, get_tool, register_tool

__all__ = [
    "BaseTool",
    "register_tool",
    "get_tool",
    "get_agno_tools",
    "register_builtin_tools",
]
