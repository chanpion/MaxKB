"""Image-understand node: multimodal LLM call over one or more images.

Mirrors ``application.flow.step_node.image_understand_step_node``. The image(s)
are resolved from an upstream reference (URL or base64), combined with the
templated prompt, and sent to a vision-capable model via Agno.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


class ImageUnderstandNode(StepNode):
    type = "image-understand-node"

    def _model_config(self) -> dict[str, Any]:
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg

    def _resolve_images(self) -> list[str]:
        raw = self.resolve(self.node_data.get("image_list"))
        if isinstance(raw, str):
            return [raw]
        if isinstance(raw, list):
            return [str(i) for i in raw if i]
        return []

    async def execute(self) -> NodeResult:
        cfg = self._model_config()
        if not cfg or not cfg.get("provider"):
            return NodeResult(
                {"answer": "", "content": "", "exception_message": "no vision model configured"},
                status=500,
                exception_message="no vision model configured",
            )

        prompt = self.resolve_template(self.node_data.get("prompt", ""))
        system = self.resolve_template(self.node_data.get("system", "")) or None
        images = self._resolve_images()

        from agno.agent import Agent

        from app.providers import get_llm

        llm = get_llm(cfg["provider"], cfg["model_name"], cfg.get("credential", {}))
        agent = Agent(model=llm, instructions=system, markdown=True)

        answer_parts: list[str] = []
        try:
            agno_images = None
            if images:
                try:
                    from agno.media import Image as AgnoImage

                    agno_images = [
                        AgnoImage(url=img) if str(img).startswith(("http://", "https://")) else AgnoImage(content=img)
                        for img in images
                    ]
                except ImportError:
                    agno_images = None  # fall back to a text-only call below

            if agno_images is not None:
                async for event in agent.arun(prompt, images=agno_images, stream=True):
                    content = getattr(event, "content", None)
                    if content:
                        answer_parts.append(content)
            else:
                async for event in agent.arun(prompt, stream=True):
                    content = getattr(event, "content", None)
                    if content:
                        answer_parts.append(content)
            answer = "".join(answer_parts)
        except Exception as e:
            if self.enable_exception:
                return NodeResult(
                    {"answer": "", "content": "", "exception_message": str(e)},
                    status=500,
                    exception_message=str(e),
                )
            raise

        return NodeResult(
            {"answer": answer, "content": answer, "data": answer, "image_list": images},
            is_result=self.is_result if self.is_result is not None else True,
            chunks=answer_parts,
        )
