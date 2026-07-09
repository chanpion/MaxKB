"""Text-to-speech node: synthesise speech from text via Agno TTS tools.

Uses the TTS registry (``app.providers.get_tts``) which maps to
``ElevenLabsTools`` or OpenAI-compatible TTS. Replaces the legacy
``text_to_speech_step_node``.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


def _extract_audio(res: Any) -> list[str]:
    items = getattr(res, "audios", None) or []
    return [u for u in (getattr(i, "url", None) for i in items) if u]


class TextToSpeechNode(StepNode):
    type = "text-to-speech-node"

    def _cfg(self) -> tuple[str, str, dict]:
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg.get("provider", ""), cfg.get("model_name", ""), cfg.get("credential", {})

    async def execute(self) -> NodeResult:
        text = self.resolve_template(self.node_data.get("text") or self.node_data.get("content") or "")
        if not text:
            return NodeResult(
                {"exception_message": "text is required"},
                status=500,
                exception_message="text is required",
            )
        provider, model, credential = self._cfg()
        try:
            from app.providers import get_tts

            tool = get_tts(provider, model, credential)
        except Exception as e:  # pragma: no cover - provider/import failure
            return NodeResult(
                {"exception_message": str(e)},
                status=500,
                exception_message=str(e),
            )

        method = getattr(tool, "text_to_speech", None) or getattr(tool, "generate_speech", None)
        if method is None:
            return NodeResult(
                {"exception_message": "unsupported TTS tool"},
                status=500,
                exception_message="unsupported TTS tool",
            )

        try:
            res = method(None, text)
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
            {"result": getattr(res, "content", ""), "audio_list": _extract_audio(res)},
            is_result=self.is_result if self.is_result is not None else True,
        )
