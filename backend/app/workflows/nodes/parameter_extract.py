"""Parameter extraction node: structured field extraction via an LLM.

Uses Agno's native structured output: an ``agno.agent.Agent`` is configured with
a dynamically built pydantic ``response_model`` derived from the node's field
definitions. This replaces the legacy LangChain prompt + JSON parsing approach.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode

_TYPE_MAP = {
    "str": str,
    "string": str,
    "int": int,
    "integer": int,
    "float": float,
    "number": float,
    "bool": bool,
    "boolean": bool,
    "list": list,
    "array": list,
    "dict": dict,
    "object": dict,
}


class ParameterExtractNode(StepNode):
    type = "parameter-extraction-node"

    def _model_config(self) -> dict[str, Any]:
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg

    def _build_model(self):
        from pydantic import Field, create_model

        fields = self.node_data.get("fields") or []
        field_defs: dict[str, Any] = {}
        for f in fields:
            if not isinstance(f, dict):
                continue
            name = f.get("name")
            if not name:
                continue
            py_type = _TYPE_MAP.get(str(f.get("type", "str")).lower(), str)
            field_defs[name] = (py_type, Field(default=None, description=f.get("description", "")))
        return create_model("ExtractedParams", **field_defs)

    async def execute(self) -> NodeResult:
        text = self.resolve_template(self.node_data.get("input", "")) or ""
        model_cls = self._build_model()

        from agno.agent import Agent

        from app.providers import get_llm

        cfg = self._model_config()
        if not cfg:
            return NodeResult(
                {"result": {}, "exception_message": "model_config is required"},
                status=500,
                exception_message="model_config is required",
            )
        llm = get_llm(cfg["provider"], cfg["model_name"], cfg.get("credential", {}))
        agent = Agent(model=llm, response_model=model_cls, markdown=False)

        try:
            run = await agent.arun(text)
            extracted = run.content if hasattr(run, "content") else run
        except Exception as e:  # pragma: no cover - provider failure
            if self.enable_exception:
                return NodeResult(
                    {"result": {}, "exception_message": str(e)},
                    status=500,
                    exception_message=str(e),
                    branch_id="exception",
                )
            raise

        if hasattr(extracted, "model_dump"):
            data = extracted.model_dump()
        elif isinstance(extracted, dict):
            data = extracted
        else:
            data = {k: getattr(extracted, k, None) for k in model_cls.model_fields}

        return NodeResult(
            {"result": data, "data": data},
            is_result=self.is_result if self.is_result is not None else True,
        )
