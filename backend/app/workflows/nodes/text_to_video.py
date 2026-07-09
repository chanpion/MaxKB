"""Text-to-video node: generate a video from a prompt via Agno video tools.

Uses the TTV registry (``app.providers.get_ttv``) which maps to
``LumaLabTools`` / ``FalTools`` / ``ReplicateTools``. Replaces the legacy
``text_to_video_step_node``.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


def _extract_videos(res: Any) -> list[str]:
    items = getattr(res, "videos", None) or []
    return [u for u in (getattr(i, "url", None) for i in items) if u]


class TextToVideoNode(StepNode):
    type = "text-to-video-node"

    def _cfg(self) -> tuple[str, str, dict]:
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg.get("provider", ""), cfg.get("model_name", ""), cfg.get("credential", {})

    async def execute(self) -> NodeResult:
        prompt = self.resolve_template(self.node_data.get("prompt", "")) or ""
        if not prompt:
            return NodeResult(
                {"exception_message": "prompt is required"},
                status=500,
                exception_message="prompt is required",
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
            if hasattr(tool, "generate_video"):
                res = tool.generate_video(None, prompt)
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
            {"result": getattr(res, "content", ""), "video_list": _extract_videos(res)},
            is_result=self.is_result if self.is_result is not None else True,
        )
