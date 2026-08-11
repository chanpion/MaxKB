"""Embedding helpers: text normalization, chunking, ts_vector, and provider calls.

Ports the small utilities used by the legacy ``knowledge.vector`` store so the
new ingestion pipeline produces ``embedding`` rows identical to Django:
  * ``normalize_for_embedding`` removes emoji / collapses whitespace
  * ``chunk_text`` mirrors ``common.chunk.text_to_chunk`` (256-char mark chunks)
  * ``to_ts_vector`` mirrors ``common.utils.ts_vecto_util.to_ts_vector`` (jieba)
Embedding vectors come from the Agno embedder abstraction in ``app.providers``.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Sequence
from typing import Any

# --- normalize_for_embedding (port of knowledge/vector/base_vector.py) --------
_RE_EMOJI = re.compile(
    r"[\U0001F300-\U0001FAFF]"  # Emoji
    r"|[\u2600-\u27BF]"  # Dingbats / Symbols
    r"|[\uFE0E\uFE0F]",  # Variation Selectors
    flags=re.UNICODE,
)
_RE_WHITESPACE = re.compile(r"\s+")


def normalize_for_embedding(text: str) -> str:
    if not text:
        return ""
    text = _RE_EMOJI.sub("", text)
    text = _RE_WHITESPACE.sub(" ", text)
    return text.strip()


# --- chunk_text (port of common/chunk + MarkChunkHandle) ----------------------
_CHUNK_SPLIT = r".{1,%d}[。| |\.|！|;|；|!|\n]"
_CHUNK_MAX = r".{1,%d}"


def chunk_text(text: str, chunk_size: int = 256) -> list[str]:
    """Split a paragraph into <=chunk_size char pieces (preserves sentence ends)."""
    chunk_list = [text]
    split_pattern = _CHUNK_SPLIT % chunk_size
    max_pattern = _CHUNK_MAX % chunk_size
    result: list[str] = []
    for chunk in chunk_list:
        for c_r in re.findall(split_pattern, chunk, flags=re.DOTALL):
            if len(c_r.strip()) > 0:
                result.append(c_r.strip())
    if not result:
        result = [c for c in re.findall(max_pattern, text) if c.strip()]
    return result or [text]


def sub_array(array: list[Any], item_num: int = 10) -> list[list[Any]]:
    """Batch ``array`` into sub-arrays of at most ``item_num`` items."""
    result: list[list[Any]] = []
    temp: list[Any] = []
    for item in array:
        temp.append(item)
        if len(temp) >= item_num:
            result.append(temp)
            temp = []
    if temp:
        result.append(temp)
    return result


# --- to_ts_vector (port of common/utils/ts_vecto_util.py) ---------------------
def to_ts_vector(text: str, user_words: Sequence[str] | None = None) -> str:
    import jieba

    tokenizer = jieba if not user_words else _build_tokenizer(list(user_words))
    result = tokenizer.lcut(text, cut_all=True)
    return " ".join(result)


_jieba_tokenizer_cache: dict = {}
_jieba_tokenizer_lock = None


def _build_tokenizer(user_words: list[str]):
    global _jieba_tokenizer_lock
    if _jieba_tokenizer_lock is None:
        import threading

        _jieba_tokenizer_lock = threading.RLock()
    cache_key = tuple(user_words)
    with _jieba_tokenizer_lock:
        cached = _jieba_tokenizer_cache.get(cache_key)
        if cached is not None:
            return cached
        import jieba

        tokenizer = jieba.Tokenizer()
        for word in user_words:
            if word:
                tokenizer.add_word(word)
        _jieba_tokenizer_cache[cache_key] = tokenizer
        return tokenizer


# --- provider-backed embedding -------------------------------------------------
async def embed_texts(
    provider: str,
    model_name: str,
    credential: dict,
    texts: Sequence[str],
    dimensions: int | None = None,
) -> list[list[float]]:
    """Embed ``texts`` using the Agno embedder abstraction (sync call in thread)."""
    if not texts:
        return []
    from app.providers import get_embedder

    embedder = get_embedder(provider, model_name, credential, dimensions=dimensions)

    def _run() -> list[list[float]]:
        # Agno 2.x embedders expose ``get_embedding(text)``; try embed() first for compat.
        if hasattr(embedder, "embed"):
            try:
                result = embedder.embed(documents=list(texts))
                if result:
                    return [list(map(float, v)) for v in result]
            except TypeError:
                pass
        if hasattr(embedder, "get_embedding"):
            out = []
            errors: list[str] = []
            for t in texts:
                try:
                    vec = embedder.get_embedding(t)
                except Exception as exc:
                    errors.append(f"get_embedding('{t[:50]}...') raised: {exc}")
                    continue
                if vec:
                    out.append(list(map(float, vec)))
                else:
                    errors.append(f"get_embedding('{t[:50]}...') returned None (check API key / endpoint)")
            if not out and errors:
                raise RuntimeError(
                    f"Embedding failed for all {len(texts)} text(s): {'; '.join(errors[:3])}"
                )
            return out
        raise RuntimeError("Embedder exposes neither embed() nor get_embedding()")

    return await asyncio.to_thread(_run)
