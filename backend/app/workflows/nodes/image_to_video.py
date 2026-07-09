"""Image-to-video node: turn an image into a video via Agno video tools.

Uses the TTV registry (``app.providers.get_ttv``) which maps to
``LumaLabTools`` / ``FalTools``. Replaces the legacy
``image_to_video_step_node``.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


def _extract_videos(res: Any) -> list[str]:
    items = getattr(res, "videos", None) or []
    return [u for u in (getattr(i, "url", None) for i in items) if u]


class ImageToVideoNode(StepNode):
    type = "image-to-video-node"

    def _cfg(self) -> tuple[str, str, dict]:
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg.get("provider", ""), cfg.get("model_name", ""), cfg.get("credential", {})

    async def execute(self) -> NodeResult:
        image = self.resolve(self.node_data.get("image") or self.node_data.get("image_url") or "")
        prompt = self.resolve_template(self.node_data.get("prompt", "")) or ""
        if not image:
            return NodeResult(
                {"exception_message": "image is required"},
                status=500,
                exception_message="image is required",
            )
        provider, model, credential = self._cfg()
        try:
            from app.providers import get_ttv

            tool = get_ttv(provider, model, credential)
        except Exception as e:  # pragma: no cover - provider/import failure
            return NodeResult(
                {"exception_message": str(e)},
                status=500,
                exception_message=str(e),
            )

        try:
            if hasattr(tool, "image_to_video"):
                res = tool.image_to_video(None, prompt=prompt, image_url=image)
            else:
                res = tool.image_to_image(None, prompt, image_url=image)
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
            {"result": getattr(res, "content", ""), "video_list": _extract_videos(res)},
            is_result=self.is_result if self.is_result is not None else True,
        )
