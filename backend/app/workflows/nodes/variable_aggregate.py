"""Variable aggregation node: merges several upstream variables.

Mirrors ``flow.step_node.variable_aggregation_node``. Supports the legacy
aggregation strategies:

  * ``first_non_null`` — first non-null resolved value across all inputs
  * ``array``         — collect every resolved value into a list
  * ``dict``          — map each ``key`` to its resolved value

Each group entry carries a ``variable_list`` of references
``[node_id, *fields]`` resolved through :meth:`WorkflowState.get_field`.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class VariableAggregateNode(StepNode):
    type = "variable-aggregation-node"

    def _resolve_group(self, group: dict[str, Any]) -> list[Any]:
        values: list[Any] = []
        for var in group.get("variable_list") or []:
            ref = var.get("variable")
            if isinstance(ref, list) and ref:
                values.append(self.state.get_field(ref))
            else:
                values.append(self.resolve(ref))
        return values

    async def execute(self) -> NodeResult:
        strategy = self.node_data.get("strategy", "first_non_null")
        group_list = self.node_data.get("group_list") or []

        collected: list[Any] = []
        for group in group_list:
            collected.extend(self._resolve_group(group))

        if strategy == "array":
            result: Any = [v for v in collected]
        elif strategy == "dict":
            result = {}
            for group in group_list:
                key = group.get("field") or group.get("id")
                vals = self._resolve_group(group)
                if key is not None and vals:
                    result[key] = vals[0]
        else:  # first_non_null
            result = next((v for v in collected if v is not None), None)

        return NodeResult(
            {"result": result, "strategy": strategy},
            is_result=False,
        )
