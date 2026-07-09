"""Image-generate node: text-to-image via Agno image tools.

Uses the TTI registry (``app.providers.get_tti``) which maps to ``DalleTools``,
``FalTools``, ``ReplicateTools`` or OpenAI-compatible generation. Replaces the
legacy ``image_generate_step_node`` self-rolled image pipeline.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


def _extract_urls(res: Any, attr: str) -> list[str]:
    items = getattr(res, attr, None) or []
    return [u for u in (getattr(i, "url", None) for i in items) if u]


class ImageGenerateNode(StepNode):
    type = "image-generate-node"

    def _cfg(self) -> tuple[str, str, dict]:
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg.get("provider", ""), cfg.get("model_name", ""), cfg.get("credential", {})

    async def execute(self) -> NodeResult:
        provider, model, credential = self._cfg()
        prompt = self.resolve_template(self.node_data.get("prompt", "")) or ""
        try:
            from app.providers import get_tti

            tool = get_tti(provider, model, credential)
        except Exception as e:  # pragma: no cover - provider/import failure
            return NodeResult(
                {"exception_message": str(e)},
                status=500,
                exception_message=str(e),
            )

        try:
            if hasattr(tool, "create_image"):
                res = tool.create_image(prompt)
            else:
                res = tool.generate_media(None, prompt)
        except Exception as e:  # pragma: no cover - provider failure
            if self.enable_exception:
                return NodeResult(
                    {"exception_message": str(e)},
                    status=500,
                    exception_message=str(e),
                    branch_id="exception",
                )
            raise

        return NodeResult(
            {"result": getattr(res, "content", ""), "image_list": _extract_urls(res, "images")},
            is_result=self.is_result if self.is_result is not None else True,
        )
