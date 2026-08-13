"""Provider brand icons (SVG strings) for the model-provider catalog.

The SVG files were copied from the legacy Django backend
(``apps/models_provider/impl/<provider>_model_provider/icon/*_icon_svg``) so the
refactor backend stays self-contained. They are loaded lazily and cached, so the
large vllm/tencent/volcanic SVGs only ever exist in memory once.
"""

from __future__ import annotations

import os
from functools import cache

_ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")

# catalog-style provider key (``model_<name>_provider``) -> svg filename
_PROVIDER_ICON_FILES: dict[str, str] = {
    "model_openai_provider": "openai.svg",
    "model_anthropic_provider": "anthropic.svg",
    "model_deepseek_provider": "deepseek.svg",
    "model_qwen_provider": "qwen.svg",
    "model_zhipu_provider": "zhipu.svg",
    "model_kimi_provider": "kimi.svg",
    "model_ollama_provider": "ollama.svg",
    "model_xunfei_provider": "xunfei.svg",
    "model_tencent_provider": "tencent.svg",
    "model_volcanic_provider": "volcanic.svg",
    "model_local_provider": "local.svg",
    "model_xinference_provider": "xinference.svg",
    "model_vllm_provider": "vllm.svg",
    "model_docker_ai_provider": "docker_ai.svg",
}


@cache
def get_icon(provider_key: str) -> str:
    """Return the SVG string for a provider key, or ``""`` when unavailable."""
    filename = _PROVIDER_ICON_FILES.get(provider_key)
    if not filename:
        return ""
    path = os.path.join(_ICON_DIR, filename)
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""
