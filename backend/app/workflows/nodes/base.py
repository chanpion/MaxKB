# coding=utf-8
"""Base classes for workflow step nodes.

Mirrors ``application.flow.i_step_node.INode`` / ``NodeResult`` but is fully
async and provider-agnostic. Each concrete node implements ``execute`` which
returns a :class:`NodeResult`; the engine merges ``node_variable`` into the
shared :class:`~app.workflows.state.WorkflowState`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.workflows.state import WorkflowState


class NodeResult:
    """Result of a single node execution (mirrors ``i_step_node.NodeResult``)."""

    def __init__(
        self,
        node_variable: Dict[str, Any],
        workflow_variable: Optional[Dict[str, Any]] = None,
        branch_id: Optional[str] = None,
        is_result: Optional[bool] = None,
        interrupt: bool = False,
        chunks: Optional[List[str]] = None,
        exception_message: Optional[str] = None,
        status: int = 200,
    ) -> None:
        self.node_variable = node_variable
        self.workflow_variable = workflow_variable or {}
        self.branch_id = branch_id
        self.is_result = is_result
        self.interrupt = interrupt
        self.chunks = chunks or []
        self.exception_message = exception_message
        self.status = status

    @property
    def is_assertion_result(self) -> bool:
        return self.branch_id is not None

    def write_context(self, node: "StepNode", state: WorkflowState) -> None:
        if self.node_variable:
            node.context.update(self.node_variable)
            state.set_node_context(node.id, node.step_name, node.context)
        if self.workflow_variable:
            state.global_context.update(self.workflow_variable)


@dataclass
class NodeInput:
    """Resolved inputs for a node (upstream outputs merged by the engine)."""

    fields: Dict[str, Any] = field(default_factory=dict)


class StepNode:
    """Base class for every workflow node."""

    type: str = "base-node"

    def __init__(
        self,
        node: Dict[str, Any],
        state: WorkflowState,
        up_node_id_list: Optional[List[str]] = None,
    ) -> None:
        self.id = node["id"]
        self.raw = node
        self.type = node.get("type", self.type)
        self.properties = node.get("properties", {}) or {}
        self.node_data = self.properties.get("node_data", {}) or {}
        self.step_name = self.properties.get("stepName", self.type)
        self.enable_exception = bool(self.properties.get("enableException", False))
        self.disabled = bool(self.properties.get("disabled", False))
        self.condition = self.properties.get("condition", "AND")
        self.state = state
        self.up_node_id_list = up_node_id_list or []
        self.context: Dict[str, Any] = {}
        self.status = 200
        self.err_message = ""

    # ----- helpers -----
    def resolve(self, value: Any) -> Any:
        return self.state.resolve_reference(value)

    def resolve_template(self, text: Any) -> Any:
        if not isinstance(text, str):
            return text
        return self.state.resolve_template(text)

    @property
    def is_result(self) -> Optional[bool]:
        if "is_result" in self.node_data:
            return bool(self.node_data["is_result"])
        return None

    def get_write_error(self, e: Exception) -> NodeResult:
        self.status = 500
        self.err_message = str(e)
        return NodeResult(
            {"exception_message": str(e)},
            status=500,
            exception_message=str(e),
        )

    async def execute(self) -> NodeResult:
        raise NotImplementedError
