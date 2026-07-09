"""Video-understand node: multimodal LLM call over a video.

Mirrors ``application.flow.step_node.video_understand_step_node``. The video is
resolved from an upstream reference (URL or base64) and sent, together with the
templated prompt, to a vision-capable model via an Agno ``Agent`` +
``agno.media.Video`` — the same pattern as ``image_understand``.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class VideoUnderstandNode(StepNode):
    type = "video-understand-node"

    def _model_config(self) -> dict[str, Any]:
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg

    def _resolve_videos(self) -> list[str]:
        raw = self.resolve(self.node_data.get("video_list"))
        if isinstance(raw, str):
            return [raw]
        if isinstance(raw, list):
            return [str(v) for v in raw if v]
        return []

    async def execute(self) -> NodeResult:
        cfg = self._model_config()
        if not cfg or not cfg.get("provider"):
            return NodeResult(
                {"answer": "", "exception_message": "no vision model configured"},
                status=500,
                exception_message="no vision model configured",
            )

        prompt = self.resolve_template(self.node_data.get("prompt", ""))
        system = self.resolve_template(self.node_data.get("system", "")) or None
        videos = self._resolve_videos()

        from agno.agent import Agent

        from app.providers import get_llm

        llm = get_llm(cfg["provider"], cfg["model_name"], cfg.get("credential", {}))
        agent = Agent(model=llm, instructions=system, markdown=True)

        answer_parts: list[str] = []
        try:
            agno_videos = None
            if videos:
                try:
                    from agno.media import Video as AgnoVideo

                    agno_videos = [
                        AgnoVideo(url=v) if str(v).startswith(("http://", "https://")) else AgnoVideo(content=v)
                        for v in videos
                    ]
                except ImportError:
                    agno_videos = None

            if agno_videos is not None:
                async for event in agent.arun(prompt, videos=agno_videos, stream=True):
                    content = getattr(event, "content", None)
                    if content:
                        answer_parts.append(content)
            else:
                async for event in agent.arun(prompt, stream=True):
                    content = getattr(event, "content", None)
                    if content:
                        answer_parts.append(content)
            answer = "".join(answer_parts)
        except Exception as e:  # pragma: no cover - provider failure
            if self.enable_exception:
                return NodeResult(
                    {"answer": "", "exception_message": str(e)},
                    status=500,
                    exception_message=str(e),
                )
            raise

        return NodeResult(
            {"answer": answer, "content": answer, "data": answer, "video_list": videos},
            is_result=self.is_result if self.is_result is not None else True,
            chunks=answer_parts,
        )
