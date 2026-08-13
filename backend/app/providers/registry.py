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

# Local sentence-transformers embedding model (mirrors legacy Django
# ``local_model_provider`` default). No API key required. When no explicit local
# checkpoint is configured (``settings.local_embedding_model_path``), this
# HuggingFace id is downloaded on first use. Dimension defaults to 768.
DEFAULT_LOCAL_EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"
LOCAL_EMBEDDING_DIM = 768

# Process-wide cache of local embedder instances, keyed by model id, so we
# never reload the ~400MB weights on every request.
_LOCAL_EMBEDDER_CACHE: dict[str, Any] = {}


def _norm(provider: str) -> str:
    """Normalize a provider id to its vendor key.

    Handles three representations that may be stored on a model:
      * ``openai``                         -> ``openai``
      * ``model_provider.openai``          -> ``openai``  (legacy dotted form)
      * ``model_openai_provider``          -> ``openai``  (UI catalog id)
    """
    p = (provider or "").split(".")[-1].lower()
    if p.startswith("model_"):
        p = p[len("model_"):]
    if p.endswith("_provider"):
        p = p[: -len("_provider")]
    return p


def _coerce_credential(credential: Any) -> dict:
    """Accept either a dict or a stored credential string (plaintext JSON or
    Fernet-encrypted). Returns a dict in all cases.

    ``Model.credential`` is persisted as a JSON/encrypted string, so callers
    sometimes pass the raw column value. Normalize here so ``get_embedder`` /
    ``get_llm`` never choke on a ``str`` (``'str' object has no attribute 'get'``).
    """
    if isinstance(credential, dict):
        return credential
    if isinstance(credential, str) and credential.strip():
        from app.providers.base import resolve_credential

        return resolve_credential(credential)
    return {}


def _api_key(credential: Any) -> str:
    if isinstance(credential, str):
        credential = _coerce_credential(credential)
    return credential.get("api_key") or credential.get("apiKey") or credential.get("AK") or ""


def get_llm(provider: str, model_name: str, credential: dict, **kwargs: Any):
    """Return an Agno LLM model instance for the given legacy vendor."""
    credential = _coerce_credential(credential)
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
    """Return an Agno Embedder instance.

    Local sentence-transformers fallback: when the provider is ``local`` and no
    remote ``base_url``/``api_key`` is configured (mirroring the legacy Django
    ``local_model_provider`` which ships ``shibing624/text2vec-base-chinese``
    with no credential), we load the model directly via
    ``SentenceTransformerEmbedder`` so embedding works without any API key.
    """
    credential = _coerce_credential(credential)
    p = _norm(provider)
    api_key = _api_key(credential)
    base_url = credential.get("base_url") or OPENAI_COMPAT_ENDPOINTS.get(p)

    if p == "local" and not base_url and not api_key:
        return _local_embedder(model_name or None, dimensions)

    from agno.knowledge.embedder.openai import OpenAIEmbedder

    return OpenAIEmbedder(id=model_name, api_key=api_key, base_url=base_url, dimensions=dimensions, **kwargs)


def _local_embedder(model_name: str | None = None, dimensions: int | None = None):
    """Load (and cache) a local sentence-transformers embedder.

    A configured local checkpoint path (``settings.local_embedding_model_path``)
    takes priority over ``model_name`` and over the built-in default, so ops can
    point at a pre-downloaded directory (e.g. a ModelScope snapshot). The output
    dimension is auto-detected from the loaded checkpoint (e.g. 384 for
    all-MiniLM-L6-v2) when not supplied, so storage and retrieval learn the
    correct size. Instances are cached per model id so weights load once.
    """
    from app.core.config import get_settings

    settings = get_settings()
    model_id = settings.local_embedding_model_path or model_name or DEFAULT_LOCAL_EMBEDDING_MODEL
    cached = _LOCAL_EMBEDDER_CACHE.get(model_id)
    if cached is not None:
        return cached
    try:
        from agno.knowledge.embedder.sentence_transformer import SentenceTransformerEmbedder
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "Local embedding requires the 'sentence-transformers' package. "
            "Install it with: uv sync --extra embedding-local"
        ) from exc
    embedder = SentenceTransformerEmbedder(
        id=model_id,
        dimensions=dimensions or LOCAL_EMBEDDING_DIM,
    )
    # Auto-detect the real output dimension so callers get the correct size
    # (the column is a variable-dimension pgvector, so this must be accurate).
    if dimensions is None:
        try:
            actual = embedder.sentence_transformer_client.get_sentence_embedding_dimension()
            if actual:
                embedder.dimensions = actual
        except Exception:
            pass
    _LOCAL_EMBEDDER_CACHE[model_id] = embedder
    return embedder


# --------------------------------------------------------------------------- #
# Multimedia provider registry (TTS / STT / TTI / TTV).
#
# Most vendors are OpenAI-compatible; dedicated agno.tools.* classes are used
# for ElevenLabs / Fal / Replicate / Luma / MLX where available.
# --------------------------------------------------------------------------- #

TTS_MAP: dict[str, tuple[str, str]] = {
    "elevenlabs": ("agno.tools.eleven_labs", "ElevenLabsTools"),
    "eleven_labs": ("agno.tools.eleven_labs", "ElevenLabsTools"),
}

STT_MAP: dict[str, tuple[str, str]] = {
    "mlx": ("agno.tools.mlx_transcribe", "MLXTranscribeTools"),
}

TTI_MAP: dict[str, tuple[str, str]] = {
    "dalle": ("agno.tools.dalle", "DalleTools"),
    "fal": ("agno.tools.fal", "FalTools"),
    "replicate": ("agno.tools.replicate", "ReplicateTools"),
}

TTV_MAP: dict[str, tuple[str, str]] = {
    "fal": ("agno.tools.fal", "FalTools"),
    "replicate": ("agno.tools.replicate", "ReplicateTools"),
    "luma": ("agno.tools.lumalab", "LumaLabTools"),
    "lumalab": ("agno.tools.lumalab", "LumaLabTools"),
}


def get_tts(provider: str, model_name: str, credential: dict, **kwargs: Any):
    """Return an Agno TTS tool for the given legacy vendor."""
    p = _norm(provider)
    api_key = _api_key(credential)
    if p in TTS_MAP:
        mod_path, cls_name = TTS_MAP[p]
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        if p in ("elevenlabs", "eleven_labs"):
            return cls(api_key=api_key, model_id=model_name, **kwargs)
        return cls(api_key=api_key, **kwargs)
    from agno.tools.openai import OpenAITools

    return OpenAITools(
        api_key=api_key,
        text_to_speech_model=model_name,
        enable_speech_generation=True,
        enable_transcription=False,
        enable_image_generation=False,
        **kwargs,
    )


def get_stt(provider: str, model_name: str, credential: dict, **kwargs: Any):
    """Return an Agno STT tool for the given legacy vendor."""
    p = _norm(provider)
    api_key = _api_key(credential)
    if p in STT_MAP:
        mod_path, cls_name = STT_MAP[p]
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        return cls(api_key=api_key, **kwargs)
    from agno.tools.openai import OpenAITools

    return OpenAITools(
        api_key=api_key,
        transcription_model=model_name,
        enable_transcription=True,
        enable_speech_generation=False,
        enable_image_generation=False,
        **kwargs,
    )


def get_tti(provider: str, model_name: str, credential: dict, **kwargs: Any):
    """Return an Agno image-generation tool for the given legacy vendor."""
    p = _norm(provider)
    api_key = _api_key(credential)
    if p in TTI_MAP:
        mod_path, cls_name = TTI_MAP[p]
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        if p == "dalle":
            return cls(model=model_name, api_key=api_key, **kwargs)
        return cls(api_key=api_key, **kwargs)
    from agno.tools.openai import OpenAITools

    return OpenAITools(
        api_key=api_key,
        image_model=model_name,
        enable_image_generation=True,
        enable_transcription=False,
        enable_speech_generation=False,
        **kwargs,
    )


def get_ttv(provider: str, model_name: str, credential: dict, **kwargs: Any):
    """Return an Agno video-generation tool for the given legacy vendor."""
    p = _norm(provider)
    api_key = _api_key(credential)
    if p in TTV_MAP:
        mod_path, cls_name = TTV_MAP[p]
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        return cls(api_key=api_key, **kwargs)
    from agno.tools.fal import FalTools

    return FalTools(api_key=api_key, **kwargs)
