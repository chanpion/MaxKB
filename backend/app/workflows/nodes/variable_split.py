"""Variable split node: extracts sub-fields from an upstream variable.

Mirrors ``flow.step_node.variable_splitting_node``. The legacy implementation
used ``jsonpath_ng``; this rewrite replaces it with plain Python dict/list path
traversal so the node has no external jsonpath dependency.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


def _navigate_path(data: Any, path: str) -> Any:
    """Resolve a path like ``a.b[0].c`` (or ``$.a.b``) against ``data``."""
    if data is None or not path:
        return data
    cleaned = path[1:] if path.startswith("$") else path
    parts: list[str] = []
    i, n = 0, len(cleaned)
    while i < n:
        ch = cleaned[i]
        if ch == ".":
            i += 1
            j = i
            while j < n and cleaned[j] not in ".[":
                j += 1
            if j > i:
                parts.append(cleaned[i:j])
            i = j
        elif ch == "[":
            j = cleaned.find("]", i)
            if j == -1:
                break
            parts.append(cleaned[i + 1 : j])
            i = j + 1
        else:
            j = i
            while j < n and cleaned[j] not in ".[":
                j += 1
            if j > i:
                parts.append(cleaned[i:j])
            i = j
    current: Any = data
    for part in parts:
        if current is None:
            return None
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, TypeError, IndexError):
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


class VariableSplitNode(StepNode):
    type = "variable-splitting-node"

    async def execute(self) -> NodeResult:
        input_variable = self.node_data.get("input_variable")
        if isinstance(input_variable, list) and input_variable:
            source = self.state.get_field(input_variable)
        else:
            source = self.resolve(input_variable)

        variable_list = self.node_data.get("variable_list") or []
        result: dict[str, Any] = {}
        for item in variable_list:
            if not isinstance(item, dict):
                continue
            field = item.get("field")
            if not field:
                continue
            expression = item.get("expression") or item.get("value") or ""
            if isinstance(expression, list):
                # Some front-ends pass a reference list instead of a jsonpath.
                value = self.state.get_field(expression)
            else:
                value = _navigate_path(source, str(expression))
            result[field] = value

        return NodeResult(
            {"result": result, **result},
            is_result=False,
        )
