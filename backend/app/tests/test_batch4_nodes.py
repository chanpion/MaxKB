"""Tests for Stage 9 batch 4 nodes (multimedia). No real LLM/SDK/DB.

External Agno tool classes (DalleTools, ElevenLabsTools, FalTools, ...) require
optional SDKs that may not be installed; the nodes obtain them through the
``app.providers`` registry getters, which we monkeypatch with fakes.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.workflows.nodes.image_generate import ImageGenerateNode
from app.workflows.nodes.image_to_video import ImageToVideoNode
from app.workflows.nodes.search_document import SearchDocumentNode
from app.workflows.nodes.speech_to_text import SpeechToTextNode
from app.workflows.nodes.text_to_speech import TextToSpeechNode
from app.workflows.nodes.text_to_video import TextToVideoNode
from app.workflows.nodes.video_understand import VideoUnderstandNode
from app.workflows.state import WorkflowState


def _state(params: dict | None = None) -> WorkflowState:
    return WorkflowState(params or {})


async def _run(node: object) -> object:
    return await node.execute()


# -------------------------- image generate -------------------------- #
class _FakeImageTool:
    def create_image(self, prompt: str):
        return SimpleNamespace(content="ok", images=[SimpleNamespace(url="http://img")])


def test_image_generate(monkeypatch):
    import app.providers as providers_mod

    monkeypatch.setattr(providers_mod, "get_tti", lambda *a, **k: _FakeImageTool())
    node = ImageGenerateNode(
        {
            "id": "ig",
            "type": "image-generate-node",
            "properties": {"stepName": "IG", "node_data": {"prompt": "a cat"}},
        },
        _state({"model_config": {"provider": "dalle", "model_name": "dall-e-3", "credential": {}}}),
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["image_list"] == ["http://img"]


# -------------------------- text to speech -------------------------- #
class _FakeTTSTool:
    def text_to_speech(self, agent, text: str):
        return SimpleNamespace(content="ok", audios=[SimpleNamespace(url="http://aud")])


def test_text_to_speech(monkeypatch):
    import app.providers as providers_mod

    monkeypatch.setattr(providers_mod, "get_tts", lambda *a, **k: _FakeTTSTool())
    node = TextToSpeechNode(
        {
            "id": "tts",
            "type": "text-to-speech-node",
            "properties": {"stepName": "TTS", "node_data": {"text": "hello"}},
        },
        _state({"model_config": {"provider": "elevenlabs", "model_name": "x", "credential": {}}}),
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["audio_list"] == ["http://aud"]


# -------------------------- speech to text -------------------------- #
class _FakeSTTTool:
    def transcribe(self, audio_path: str) -> str:
        return "transcript text"


def test_speech_to_text(monkeypatch):
    import app.providers as providers_mod

    monkeypatch.setattr(providers_mod, "get_stt", lambda *a, **k: _FakeSTTTool())
    node = SpeechToTextNode(
        {
            "id": "stt",
            "type": "speech-to-text-node",
            "properties": {"stepName": "STT", "node_data": {"audio": "/tmp/a.wav"}},
        },
        _state({"model_config": {"provider": "mlx", "model_name": "x", "credential": {}}}),
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["result"] == "transcript text"


# -------------------------- image to video -------------------------- #
class _FakeImageToVideoTool:
    def image_to_video(self, agent, prompt: str, image_url: str):
        return SimpleNamespace(content="ok", videos=[SimpleNamespace(url="http://vid")])


def test_image_to_video(monkeypatch):
    import app.providers as providers_mod

    monkeypatch.setattr(providers_mod, "get_ttv", lambda *a, **k: _FakeImageToVideoTool())
    node = ImageToVideoNode(
        {
            "id": "i2v",
            "type": "image-to-video-node",
            "properties": {"stepName": "I2V", "node_data": {"image": "http://img", "prompt": "move"}},
        },
        _state({"model_config": {"provider": "luma", "model_name": "x", "credential": {}}}),
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["video_list"] == ["http://vid"]


# -------------------------- text to video --------------------------- #
class _FakeTextToVideoTool:
    def generate_video(self, agent, prompt: str):
        return SimpleNamespace(content="ok", videos=[SimpleNamespace(url="http://vid2")])


def test_text_to_video(monkeypatch):
    import app.providers as providers_mod

    monkeypatch.setattr(providers_mod, "get_ttv", lambda *a, **k: _FakeTextToVideoTool())
    node = TextToVideoNode(
        {
            "id": "t2v",
            "type": "text-to-video-node",
            "properties": {"stepName": "T2V", "node_data": {"prompt": "a dog running"}},
        },
        _state({"model_config": {"provider": "luma", "model_name": "x", "credential": {}}}),
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["video_list"] == ["http://vid2"]


# -------------------------- video understand ------------------------ #
class _FakeVUAgent:
    def __init__(self, *a, **k):
        pass

    async def arun(self, message, videos=None, stream=False):
        for chunk in ["video answer"]:
            yield SimpleNamespace(content=chunk)


def test_video_understand(monkeypatch):
    import agno.agent as agent_mod

    import app.providers as providers_mod

    monkeypatch.setattr(agent_mod, "Agent", _FakeVUAgent)
    monkeypatch.setattr(providers_mod, "get_llm", lambda *a, **k: object())
    node = VideoUnderstandNode(
        {
            "id": "vu",
            "type": "video-understand-node",
            "properties": {
                "stepName": "VU",
                "node_data": {"prompt": "describe", "video_list": ["http://v.mp4"]},
            },
        },
        _state({"model_config": {"provider": "openai", "model_name": "gpt-4o", "credential": {}}}),
        [],
    )
    result = asyncio.run(_run(node))
    assert "video answer" in result.node_variable["answer"]


# -------------------------- search document ------------------------- #
class _FakeEmbedder:
    async def embed(self, texts):
        return [[0.1] * 8 for _ in texts]


class _FakeRetriever:
    def __init__(self, engine):
        self.engine = engine

    async def search(self, **kwargs):
        return [{"content": "doc1", "paragraph_id": "p1", "similarity": 0.9}]


def test_search_document(monkeypatch):
    import app.providers as providers_mod
    import app.rag.retriever as retriever_mod

    monkeypatch.setattr(providers_mod, "get_embedder", lambda *a, **k: _FakeEmbedder())
    monkeypatch.setattr(retriever_mod, "PgVectorRetriever", _FakeRetriever)
    node = SearchDocumentNode(
        {
            "id": "sd",
            "type": "search-document-node",
            "properties": {
                "stepName": "SD",
                "node_data": {"query": "hello", "knowledge_ids": ["kb1"], "top_n": 3},
            },
        },
        _state({"embedding_config": {"provider": "openai", "model_name": "t", "credential": {}}}),
        [],
    )
    result = asyncio.run(_run(node))
    assert result.node_variable["document_list"][0]["content"] == "doc1"
