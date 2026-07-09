"""Model provider abstraction backed by Agno.

Exposes credential encryption/validation and a `get_model` factory that maps
legacy `models_provider` vendors to Agno Model / Embedder instances.
"""

from app.providers.base import (
    ModelProvider,
    decrypt_credential,
    encrypt_credential,
    is_valid_credential,
)
from app.providers.catalog import get_provider, list_providers, providers_for_model_type
from app.providers.registry import (
    get_embedder,
    get_llm,
    get_stt,
    get_tti,
    get_tts,
    get_ttv,
)

__all__ = [
    "ModelProvider",
    "encrypt_credential",
    "decrypt_credential",
    "is_valid_credential",
    "get_llm",
    "get_embedder",
    "get_tts",
    "get_stt",
    "get_tti",
    "get_ttv",
    "list_providers",
    "get_provider",
    "providers_for_model_type",
]
