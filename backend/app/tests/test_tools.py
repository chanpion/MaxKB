"""Tests for the tools registry and built-in tools (no agno / DB required)."""

from __future__ import annotations

import asyncio

from app.tools.builtin import CalculatorTool, CurrentTimeTool, register_builtin_tools
from app.tools.registry import ToolRegistry, get_tool


def test_calculator_tool():
    tool = CalculatorTool(tool_id="builtin:calculator")
    result = asyncio.run(tool.invoke(None, {"expression": "2 * (3 + 4)"}))
    assert result == {"result": 14}


def test_calculator_rejects_non_arithmetic():
    tool = CalculatorTool(tool_id="builtin:calculator")
    result = asyncio.run(tool.invoke(None, {"expression": "__import__('os')"}))
    assert "error" in result


def test_current_time_tool():
    tool = CurrentTimeTool(tool_id="builtin:current_time")
    result = asyncio.run(tool.invoke(None, {}))
    assert "result" in result


def test_registry_register_and_get():
    reg = ToolRegistry()
    reg.register(CalculatorTool(tool_id="t1"))
    assert reg.get_tool("t1") is not None
    assert reg.get_tool("missing") is None


def test_builtin_registration():
    register_builtin_tools()
    assert get_tool("builtin:calculator") is not None
    assert get_tool("builtin:current_time") is not None
