"""Tests for ChatAgent SSE streaming (no real LLM / credentials required).

The Agno ``Agent`` and the provider lookup are monkeypatched with fakes so the
streaming framing logic (SSE ``data:`` frames + trailing ``done``) is verified
end-to-end without network access.
"""

from __future__ import annotations

from app.agents import chat_agent as ca_mod
from app.agents.chat_agent import ChatAgent


class _Event:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeAgent:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs

    async def arun(self, message: str, **kwargs: object):
        for chunk in ("Hi", " there", "!"):
            yield _Event(chunk)


def _fake_llm(*_a, **_k):
    return object()


async def test_stream_yields_sse_frames(monkeypatch):
    monkeypatch.setattr(ca_mod, "Agent", FakeAgent)
    monkeypatch.setattr(ca_mod, "get_llm", _fake_llm)

    agent = ChatAgent(model_provider="openai", model_name="x", credential={})
    frames = [frame async for frame in agent.stream("hello")]

    joined = "".join(frames)
    # The three streamed chunks plus the trailing done frame.
    assert frames[0] == 'data: {"content": "Hi"}\n\n'
    assert '" there"' in joined
    assert '"!"' in joined
    assert '"done": true' in joined
    # Each frame is a well-formed SSE data frame.
    assert all(f.startswith("data: ") for f in frames)
