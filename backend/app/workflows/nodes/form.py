"""Form node: aggregates upstream values into a structured form.

Mirrors ``application.flow.step_node.form_node``. Each field may carry a
reference (resolved from upstream node context) or a static default. The node
renders ``form_content_format`` with the resolved values and exposes both the
structured ``form_data`` and the rendered ``form_content`` for downstream nodes.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class FormNode(StepNode):
    type = "form-node"

    async def execute(self) -> NodeResult:
        field_list = self.node_data.get("form_field_list") or []
        content_format = self.node_data.get("form_content_format") or ""
        defaults = self.node_data.get("form_data") or {}

        form_data: dict[str, Any] = {}
        for field in field_list:
            if not isinstance(field, dict):
                continue
            name = field.get("name") or field.get("field")
            if not name:
                continue
            # A field value may reference an upstream output or be a static default.
            value = self.resolve(field.get("value"))
            if value is None:
                value = defaults.get(name)
            if value is None:
                value = field.get("default_value")
            form_data[name] = value

        # Suspend the workflow when the form needs user input that is not yet
        # available. The caller resumes by re-running the engine with the filled
        # values supplied through params (resolved here via ``global.<name>``).
        if self.node_data.get("need_user_input"):
            missing = [name for name, val in form_data.items() if val is None]
            if missing:
                return NodeResult(
                    {
                        "form_field_list": field_list,
                        "form_data": form_data,
                        "form_content": "",
                        "missing": missing,
                    },
                    interrupt=True,
                    is_result=True,
                )

        # Render the content template, substituting field names.
        form_content = content_format
        if isinstance(content_format, str) and "{" in content_format:
            for key, val in form_data.items():
                form_content = form_content.replace("{" + str(key) + "}", "" if val is None else str(val))

        return NodeResult(
            {
                "form_field_list": field_list,
                "form_data": form_data,
                "form_content": form_content,
            },
            is_result=False,
        )
