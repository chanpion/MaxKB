"""Conversational chat agent built on Agno.

Replaces the legacy ``application.chat_pipeline`` (search_dataset ->
generate_human_message -> chat_step) with a single Agno :class:`Agent` that:

  * retrieves relevant paragraphs through a pgvector-backed retriever,
  * keeps cross-turn context via Agno ``memory`` (long-term memory),
  * streams the answer token-by-token using ``arun(stream=True)``.

The retriever adapter reuses :class:`app.rag.retriever.PgVectorRetriever`,
which executes the SAME pgvector SQL as the Django backend, so the new
service shares the existing ``embedding`` / ``paragraph`` tables.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Sequence
from typing import Any

from agno.agent import Agent

from app.providers import get_llm
from app.rag.embed import embed_texts, normalize_for_embedding
from app.rag.retriever import PgVectorRetriever

_DEFAULT_INSTRUCTIONS = (
    "You are MaxKB, an enterprise knowledge assistant. "
    "Answer the user's question using ONLY the retrieved knowledge context. "
    "If the context does not contain the answer, say you don't know instead of "
    "making things up. Keep answers concise and in the user's language."
)


class AgnoRetriever:
    """Agno-compatible retriever adapter around :class:`PgVectorRetriever`.

    Agno calls ``arun(query, **kwargs)`` and expects a list of
    ``{"content": str, "title": str, ...}`` dicts.
    """

    def __init__(
        self,
        knowledge_ids: Sequence[str],
        embedding: dict[str, Any],
        top_n: int = 5,
        similarity: float = 0.5,
        search_mode: str = "embedding",
    ) -> None:
        self.knowledge_ids = list(knowledge_ids)
        self.embedding = embedding
        self.top_n = top_n
        self.similarity = similarity
        self.search_mode = search_mode
        self._retriever = PgVectorRetriever()

    async def arun(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        provider = self.embedding["provider"]
        model_name = self.embedding["model_name"]
        credential = self.embedding.get("credential", {})
        dimensions = self.embedding.get("dimensions")
        vectors = await embed_texts(
            provider, model_name, credential, [normalize_for_embedding(query)], dimensions=dimensions
        )
        if not vectors:
            return []
        rows = await self._retriever.search(
            query_embedding=vectors[0],
            knowledge_ids=self.knowledge_ids,
            top_n=self.top_n,
            similarity=self.similarity,
            search_mode=self.search_mode,
            query_text=query,
        )
        return [
            {
                "content": r.get("content"),
                "title": r.get("title"),
                "similarity": r.get("similarity"),
            }
            for r in rows
        ]

    # Synchronous fallback used by some Agno code paths.
    def run(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        import asyncio

        return asyncio.get_event_loop().run_until_complete(self.arun(query, **kwargs))


def build_memory(user_id: str | None = None):
    """Build an Agno long-term memory (DB-backed) if available.

    Falls back to ``None`` (stateless) when the postgres memory backend is not
    configured, so the agent always works even without memory wiring.
    """
    try:
        from agno.memory.db.postgres import PostgresMemory

        from app.core.db import engine

        return PostgresMemory(db_url=str(engine.url), table_name="agent_memory")
    except Exception:  # pragma: no cover - optional dependency / config
        return None


class ChatAgent:
    """Thin wrapper around an Agno :class:`Agent` for RAG chat."""

    def __init__(
        self,
        *,
        model_provider: str,
        model_name: str,
        credential: dict[str, Any],
        knowledge_ids: Sequence[str] | None = None,
        embedding: dict[str, Any] | None = None,
        instructions: str | None = None,
        memory=None,
        top_n: int = 5,
        similarity: float = 0.5,
        search_mode: str = "embedding",
    ) -> None:
        self.llm = get_llm(model_provider, model_name, credential)
        retriever = None
        if knowledge_ids and embedding:
            retriever = AgnoRetriever(
                knowledge_ids=knowledge_ids,
                embedding=embedding,
                top_n=top_n,
                similarity=similarity,
                search_mode=search_mode,
            )
        self.agent = Agent(
            model=self.llm,
            retriever=retriever,
            memory=memory,
            instructions=instructions or _DEFAULT_INSTRUCTIONS,
            markdown=True,
        )

    async def stream(self, message: str, *, session_id: str | None = None) -> AsyncGenerator[str, None]:
        """Stream the answer as Server-Sent-Events chunks.

        Yields raw SSE frames (``data: {...}\\n\\n``). The FastAPI route wraps
        this generator in a ``StreamingResponse``.
        """
        kwargs: dict[str, Any] = {"stream": True}
        if session_id is not None:
            kwargs["session_id"] = session_id
        async for event in self.agent.arun(message, **kwargs):
            content = getattr(event, "content", None)
            if content:
                yield "data: " + json.dumps({"content": content}, ensure_ascii=False) + "\n\n"
        yield "data: " + json.dumps({"done": True}) + "\n\n"


def sse_event(payload: dict[str, Any]) -> str:
    """Helper to format an SSE frame from a dict payload."""
    return "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"
