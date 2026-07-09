# coding=utf-8
"""Provider registry: maps legacy vendors to Agno Model / Embedder instances.

Strategy (see docs/STAGE0_AGNO_VERIFICATION.md):
  * Native vendors  -> agno.models.* classes (lazy-imported).
  * Most CN vendors  -> OpenAI-compatible endpoints via agno.models.openai.OpenAIChat.
  * Xunfei (iFlytek) -> self-implemented adapter (proprietary WebSocket API).
  * Embeddings       -> OpenAI-compatible OpenAIEmbedder (most endpoints comply).

Agno class paths follow the latest stable release; adjust NATIVE_LLM_MAP if a
class name differs after `uv sync`.
"""
from __future__ import annotations

import importlib
from typing import Any

# provider (normalized) -> (agno module, class name) for native integration.
NATIVE_LLM_MAP: dict[str, tuple[str, str]] = {
    "openai": ("agno.models.openai", "OpenAIChat"),
    "anthropic": ("agno.models.anthropic", "Anthropic"),
    "google": ("agno.models.google", "Gemini"),
    "deepseek": ("agno.models.deepseek", "DeepSeek"),
    "ollama": ("agno.models.ollama", "Ollama"),
    "vllm": ("agno.models.vllm", "VLLM"),
    "azure": ("agno.models.azure", "AzureOpenAI"),
    "aws": ("agno.models.aws", "Bedrock"),
    "minimax": ("agno.models.minimax", "MiniMax"),
    "xai": ("agno.models.xai", "XAI"),
    "dashscope": ("agno.models.dashscope", "DashScope"),
    "groq": ("agno.models.groq", "Groq"),
    "mistral": ("agno.models.mistral", "Mistral"),
    "cohere": ("agno.models.cohere", "Cohere"),
}

# provider (normalized) -> OpenAI-compatible base_url (None = supplied by caller).
OPENAI_COMPAT_ENDPOINTS: dict[str, str | None] = {
    "kimi": "https://api.moonshot.cn/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "silicon": "https://api.siliconflow.cn/v1",
    "siliconcloud": "https://api.siliconflow.cn/v1",
    "volcanic": "https://ark.cn-beijing.volces.com/api/v3",
    "tencent": "https://api.hunyuan.cloud.tencent.com/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    "xinference": None,
    "local": None,
    "regolo": "https://api.regolo.ai/v1",
    "docker": None,
    "baichuan": None,
}


def _norm(provider: str) -> str:
    """Normalize 'model_provider.openai' / 'OPENAI' -> 'openai'."""
    return (provider or "").split(".")[-1].lower()


def _api_key(credential: dict) -> str:
    return credential.get("api_key") or credential.get("apiKey") or credential.get("AK") or ""


def get_llm(provider: str, model_name: str, credential: dict, **kwargs: Any):
    """Return an Agno LLM model instance for the given legacy vendor."""
    p = _norm(provider)
    api_key = _api_key(credential)

    if p == "xunfei":
        from app.providers.xunfei import XunfeiModel

        return XunfeiModel(id=model_name, credential=credential)

    if p in NATIVE_LLM_MAP:
        module_path, cls_name = NATIVE_LLM_MAP[p]
        mod = importlib.import_module(module_path)
        cls = getattr(mod, cls_name)
        return cls(id=model_name, api_key=api_key, **kwargs)

    # OpenAI-compatible fallback (covers most CN vendors).
    base_url = credential.get("base_url") or OPENAI_COMPAT_ENDPOINTS.get(p)
    from agno.models.openai import OpenAIChat

    return OpenAIChat(id=model_name, api_key=api_key, base_url=base_url, **kwargs)


def get_embedder(
    provider: str,
    model_name: str,
    credential: dict,
    dimensions: int | None = None,
    **kwargs: Any,
):
    """Return an Agno Embedder instance (OpenAI-compatible by default)."""
    p = _norm(provider)
    api_key = _api_key(credential)
    base_url = credential.get("base_url") or OPENAI_COMPAT_ENDPOINTS.get(p)
    from agno.embedder.openai import OpenAIEmbedder

    return OpenAIEmbedder(
        id=model_name, api_key=api_key, base_url=base_url, dimensions=dimensions, **kwargs
    )
