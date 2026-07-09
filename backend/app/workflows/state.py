"""Shared mutable state for a workflow run.

Mirrors ``WorkflowManage.context`` / ``chat_context`` / ``global`` plus the
reference-resolution logic used by ``WorkflowManage.reset_prompt`` and
``get_reference_field``.
"""

from __future__ import annotations

import json
from typing import Any

from app.workflows.compare import do_assertion

# A reference object stored inside node params, e.g.
# {"node_id": "abc", "fields": ["content"]} or {"node_id": "global", "fields": ["x"]}
Reference = dict[str, Any]


class WorkflowState:
    """Holds per-run context shared across nodes."""

    def __init__(self, params: dict[str, Any], *, node_names: dict[str, str] | None = None) -> None:
        # node_id -> node context dict
        self.context: dict[str, dict[str, Any]] = {}
        self.global_context: dict[str, Any] = {}
        self.chat_context: dict[str, Any] = {}
        self.params = params
        self.answers: list[str] = []
        self.details: dict[str, Any] = {}
        # node_id -> stepName (for template placeholder replacement)
        self.node_names = node_names or {}
        # cached placeholder index: "NodeName.field" -> (node_id, field)
        self._field_index: dict[str, Any] = {}
        # optional real-time streaming sink (set by the engine for SSE)
        self.on_chunk: Any | None = None
        self._build_field_index()

    # ------------------------------------------------------------------ #
    # Reference resolution
    # ------------------------------------------------------------------ #
    def _navigate(self, obj: Any, fields: list[str]) -> Any:
        for field in fields:
            if obj is None:
                return None
            obj = obj.get(field) if isinstance(obj, dict) else None
        return obj

    def get_field(self, field_list: list[str]) -> Any:
        """Resolve a reference field list to its value (mirrors ``INode.get_field``)."""
        if not field_list:
            return None
        node_id, *rest = field_list
        if node_id == "global":
            return self._navigate(self.global_context, rest)
        if node_id == "chat":
            return self._navigate(self.chat_context, rest)
        return self._navigate(self.context.get(node_id, {}), rest)

    def resolve_reference(self, value: Any) -> Any:
        """If ``value`` is a reference object, resolve it; otherwise return as-is."""
        if isinstance(value, dict) and "node_id" in value and "fields" in value:
            return self.get_field([value["node_id"], *value["fields"]])
        return value

    def _build_field_index(self) -> None:
        for node_id, name in self.node_names.items():
            ctx = self.context.get(node_id, {})
            for key, _ in ctx.items():
                self._field_index[f"{name}.{key}"] = (node_id, key)
                self._field_index[f"{node_id}.{key}"] = (node_id, key)
        for key in self.global_context:
            self._field_index[f"global.{key}"] = ("global", key)
            self._field_index[f"全局变量.{key}"] = ("global", key)
        for key in self.chat_context:
            self._field_index[f"chat.{key}"] = ("chat", key)

    def resolve_template(self, template: str) -> str:
        """Replace ``NodeName.field`` / ``global.field`` / ``chat.field`` placeholders."""
        if not isinstance(template, str) or "{" not in template:
            return template
        result = template
        for placeholder, (node_id, field) in self._field_index.items():
            if placeholder in result:
                value = self.get_field([node_id, field])
                result = result.replace(placeholder, "" if value is None else str(value))
        return result

    def set_node_context(self, node_id: str, node_name: str, ctx: dict[str, Any]) -> None:
        self.context[node_id] = ctx
        if node_name:
            self.node_names[node_id] = node_name
            self._build_field_index()

    def append_answer(self, content: str) -> None:
        if self.answers and not self.answers[-1].endswith("\n\n") and content:
            self.answers[-1] = self.answers[-1] + content
        elif self.answers:
            self.answers[-1] = self.answers[-1] + content
        else:
            self.answers.append(content)

    def do_assertion(self, condition: str, condition_list: list[dict[str, Any]]) -> bool:
        return do_assertion(self.get_field, self.resolve_template, condition, condition_list)


def serialize(value: Any) -> Any:
    """JSON-safe serialization for details/streaming payloads."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)
