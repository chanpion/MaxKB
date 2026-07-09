"""Application node: invokes a nested MaxKB application (sub-workflow).

Mirrors ``flow.step_node.application_node.impl.base_application_node``. Instead of
calling the Django chat API (which would create a circular dependency in the new
backend), the sub-application's ``work_flow`` graph is executed directly through a
nested :class:`~app.workflows.engine.WorkflowEngine`. The ``question`` and the
configured API / user input fields are resolved from upstream context and passed
as the child workflow's params.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class ApplicationNode(StepNode):
    type = "application-node"

    def _resolve_question(self) -> str:
        ref = self.node_data.get("question_reference_address")
        if isinstance(ref, dict) and "node_id" in ref:
            value = self.resolve(ref)
        elif isinstance(ref, list) and ref:
            # Reference path: [node_id, *fields]
            value = self.state.get_field(ref)
        else:
            value = ""
        return "" if value is None else str(value)

    def _resolve_input_fields(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        api_fields = self.node_data.get("api_input_field_list") or []
        for field in api_fields:
            if not isinstance(field, dict):
                continue
            key = field.get("variable")
            if not key:
                continue
            kwargs[key] = self.resolve(field.get("value"))

        user_fields = self.node_data.get("user_input_field_list") or []
        for field in user_fields:
            if not isinstance(field, dict):
                continue
            key = field.get("field")
            if not key:
                continue
            kwargs[key] = self.resolve(field.get("value"))
        return kwargs

    async def execute(self) -> NodeResult:
        application_id = self.resolve(self.node_data.get("application_id"))
        if not application_id:
            return NodeResult(
                {"error": "application_id is required"},
                status=500,
                exception_message="application_id is required",
            )

        question = self._resolve_question()
        kwargs = self._resolve_input_fields()

        # Load the sub-application from the shared PostgreSQL database.
        from sqlmodel import select

        from app.core.db import SessionLocal
        from app.models.application import Application

        async with SessionLocal() as session:
            stmt = select(Application).where(Application.id == application_id)
            app = (await session.execute(stmt)).scalar_one_or_none()

        if app is None:
            return NodeResult(
                {"error": f"application {application_id} not found"},
                status=500,
                exception_message=f"application {application_id} not found",
            )

        sub_flow = app.work_flow or {}
        if not sub_flow:
            return NodeResult(
                {"error": f"application {application_id} has no workflow"},
                status=500,
                exception_message=f"application {application_id} has no workflow",
            )

        params = dict(self.state.params)
        params["question"] = question
        params.update(kwargs)

        from app.workflows.engine import WorkflowEngine

        engine = WorkflowEngine(sub_flow, params)
        result = await engine.run()

        return NodeResult(
            {
                "answer": result["answer"],
                "result": result["answer"],
                "question": question,
                "application_node_dict": result["details"],
            },
            is_result=self.is_result if self.is_result is not None else True,
        )
