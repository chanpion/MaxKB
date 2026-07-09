# coding=utf-8
"""Base tool abstraction bridging MaxKB tools to Agno Function tools.

A :class:`BaseTool` exposes two execution paths:

  * ``invoke(state, inputs)`` — the low-level async callable used by the
    workflow :class:`~app.workflows.nodes.tool.ToolNode`.
  * ``to_agno()`` — wraps the tool as an ``agno.tools.function.Function`` so it
    can be handed to an ``agno.agent.Agent`` for native function-calling.

Agno is imported lazily so this module is importable in dependency-light
environments (tests / CI before ``uv sync``).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseTool(ABC):
    name: str = "base-tool"
    description: str = ""

    def __init__(
        self,
        *,
        tool_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.id = tool_id
        self.name = name or self.name
        self.description = description or self.description
        self.input_schema = input_schema or {}

    @abstractmethod
    async def invoke(self, state: Any, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run the tool. ``state`` is the workflow ``WorkflowState`` (may be None)."""
        raise NotImplementedError

    def to_agno(self):
        """Return an ``agno.tools.function.Function`` for agent function-calling."""
        from agno.tools.function import Function

        async def _entry(**kwargs: Any) -> Any:
            return await self.invoke(None, kwargs)

        return Function(
            name=self.name,
            description=self.description,
            entrypoint=_entry,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__name__} {self.name!r}>"
