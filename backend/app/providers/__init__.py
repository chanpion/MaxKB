# coding=utf-8
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
from app.providers.registry import get_embedder, get_llm

__all__ = [
    "ModelProvider",
    "encrypt_credential",
    "decrypt_credential",
    "is_valid_credential",
    "get_llm",
    "get_embedder",
]
