"""Provider catalog: richer metadata beyond the registry's LLM/Embedder factory.

The registry (``registry.py``) answers "how do I build an Agno model for vendor
X?"; this catalog answers "what does the UI need to render a credential form
for vendor X, and which model types does it support?".

It is intentionally data-only (no network) so the API can return it without a
DB. Every entry mirrors a legacy ``models_provider/impl`` provider. The
``credential_form`` fields drive the dynamic form engine used by the frontend.
"""

from __future__ import annotations

from typing import Any


def _field(
    field: str,
    label: str,
    input_type: str = "password",
    required: bool = True,
    default: str = "",
    props: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "field": field,
        "label": label,
        "input_type": input_type,
        "required": required,
        "default_value": default,
        "props": props or {},
    }


# model_type values align with MaxKB's ModelTypeConst.
_LLM = "LLM"
_EMBEDDING = "EMBEDDING"
_RERANKER = "RERANKER"
_TTI = "TTI"
_TTS = "TTS"
_STT = "STT"

PROVIDER_CATALOG: dict[str, dict[str, Any]] = {
    "openai": {
        "name": "OpenAI",
        "model_types": [_LLM, _EMBEDDING],
        "auth_type": "api_key",
        "base_url": "https://api.openai.com/v1",
        "credential_form": [
            _field("api_key", "API Key"),
        ],
    },
    "anthropic": {
        "name": "Anthropic",
        "model_types": [_LLM],
        "auth_type": "api_key",
        "base_url": "https://api.anthropic.com",
        "credential_form": [_field("api_key", "API Key")],
    },
    "deepseek": {
        "name": "DeepSeek",
        "model_types": [_LLM, _EMBEDDING],
        "auth_type": "api_key",
        "base_url": "https://api.deepseek.com/v1",
        "credential_form": [_field("api_key", "API Key")],
    },
    "qwen": {
        "name": "通义千问 (DashScope)",
        "model_types": [_LLM, _EMBEDDING, _TTS],
        "auth_type": "api_key",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "credential_form": [_field("api_key", "API Key (DashScope)")],
    },
    "zhipu": {
        "name": "智谱 GLM",
        "model_types": [_LLM, _EMBEDDING],
        "auth_type": "api_key",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "credential_form": [_field("api_key", "API Key")],
    },
    "kimi": {
        "name": "Kimi (Moonshot)",
        "model_types": [_LLM],
        "auth_type": "api_key",
        "base_url": "https://api.moonshot.cn/v1",
        "credential_form": [_field("api_key", "API Key")],
    },
    "ollama": {
        "name": "Ollama",
        "model_types": [_LLM, _EMBEDDING],
        "auth_type": "none",
        "base_url": "http://localhost:11434",
        "credential_form": [_field("base_url", "Base URL", input_type="input", required=False)],
    },
    "xunfei": {
        "name": "讯飞星火 (iFlytek)",
        "model_types": [_LLM, _TTS, _STT],
        "auth_type": "app_secret",
        "base_url": "",
        "credential_form": [
            _field("app_id", "APP ID", input_type="input"),
            _field("api_key", "API Key", input_type="input"),
            _field("api_secret", "API Secret"),
        ],
    },
    "tencent": {
        "name": "腾讯混元",
        "model_types": [_LLM, _EMBEDDING],
        "auth_type": "api_key",
        "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
        "credential_form": [_field("api_key", "API Key")],
    },
    "volcanic": {
        "name": "火山方舟 (Volcengine)",
        "model_types": [_LLM, _EMBEDDING],
        "auth_type": "api_key",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "credential_form": [_field("api_key", "API Key")],
    },
    "local": {
        "name": "本地模型 (OpenAI 兼容)",
        "model_types": [_LLM, _EMBEDDING],
        "auth_type": "none",
        "base_url": "http://localhost:8081/v1",
        "credential_form": [
            _field("base_url", "Base URL", input_type="input", required=True),
            _field("api_key", "API Key", required=False),
        ],
    },
}


# Model type -> the providers that support it (handy for the create-model form).
_MODEL_TYPE_INDEX: dict[str, list[str]] = {}


def providers_for_model_type(model_type: str) -> list[str]:
    return [p for p, meta in PROVIDER_CATALOG.items() if model_type in meta["model_types"]]


def list_providers() -> list[dict[str, Any]]:
    """Return the full catalog as a stable, ordered list of provider dicts."""
    return [
        {
            "provider": pid,
            "name": meta["name"],
            "model_types": meta["model_types"],
            "auth_type": meta["auth_type"],
            "base_url": meta["base_url"],
            "credential_form": meta["credential_form"],
        }
        for pid, meta in PROVIDER_CATALOG.items()
    ]


def get_provider(provider: str) -> dict[str, Any] | None:
    meta = PROVIDER_CATALOG.get(provider)
    if meta is None:
        return None
    return {
        "provider": provider,
        "name": meta["name"],
        "model_types": meta["model_types"],
        "auth_type": meta["auth_type"],
        "base_url": meta["base_url"],
        "credential_form": meta["credential_form"],
    }
