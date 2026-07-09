"""Speech-to-text node: transcribe audio via Agno STT tools.

Uses the STT registry (``app.providers.get_stt``) which maps to
``MLXTranscribeTools`` or OpenAI-compatible transcription. Replaces the legacy
``speech_to_text_step_node``.
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class SpeechToTextNode(StepNode):
    type = "speech-to-text-node"

    def _cfg(self) -> tuple[str, str, dict]:
        cfg = self.state.params.get("model_config") or {}
        if not cfg:
            cfg = self.resolve(self.node_data.get("model_id")) or {}
        return cfg.get("provider", ""), cfg.get("model_name", ""), cfg.get("credential", {})

    async def execute(self) -> NodeResult:
        audio = self.resolve(self.node_data.get("audio") or self.node_data.get("audio_url") or "")
        if not audio:
            return NodeResult(
                {"exception_message": "audio is required"},
                status=500,
                exception_message="audio is required",
            )
        provider, model, credential = self._cfg()
        try:
            from app.providers import get_stt

            tool = get_stt(provider, model, credential)
        except Exception as e:  # pragma: no cover - provider/import failure
            return NodeResult(
                {"exception_message": str(e)},
                status=500,
                exception_message=str(e),
            )

        method = getattr(tool, "transcribe", None) or getattr(tool, "transcribe_audio", None)
        if method is None:
            return NodeResult(
                {"exception_message": "unsupported STT tool"},
                status=500,
                exception_message="unsupported STT tool",
            )

        try:
            res = method(audio)
        except Exception as e:  # pragma: no cover - provider failure
            if self.enable_exception:
                return NodeResult(
                    {"exception_message": str(e)},
                    status=500,
                    exception_message=str(e),
                    branch_id="exception",
                )
            raise

        text = res if isinstance(res, str) else getattr(res, "content", "")
        return NodeResult(
            {"result": text, "content": text, "data": text},
            is_result=self.is_result if self.is_result is not None else True,
        )
