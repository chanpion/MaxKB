# coding=utf-8
"""Provider base: credential encryption/validation mirroring BaseModelCredential."""
from __future__ import annotations

import base64
import hashlib
from typing import Any

from app.core.config import get_settings

_settings = get_settings()


def _derive_key() -> bytes:
    """Derive a 32-byte Fernet key from the configured secret material.

    Legacy MaxKB used a fixed key; here we derive deterministically from
    MAXKB_DB_PASSWORD so encrypted credentials remain reversible within a
    deployment. Externalize via MAXKB_SECRET_KEY in production.
    """
    digest = hashlib.sha256(_settings.db_password.encode()).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None:
        from cryptography.fernet import Fernet

        _fernet = Fernet(_derive_key())
    return _fernet


def encrypt_credential(plain: str) -> str:
    """Encrypt a plaintext credential (mirrors BaseModelCredential.encryption_dict)."""
    if not isinstance(plain, str):
        plain = str(plain)
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_credential(token: str) -> str:
    """Decrypt an encrypted credential back to plaintext."""
    return _get_fernet().decrypt(token.encode()).decode()


def is_valid_credential(credential: dict, required_keys: list[str]) -> bool:
    """Mirror BaseModelCredential.is_valid: all required keys present & non-empty."""
    return all(bool(credential.get(k)) for k in required_keys)


class ModelProvider:
    """Base provider. Subclasses return an Agno model instance for a vendor."""

    provider: str = ""
    model_type: str = ""  # LLM / EMBEDDING / STT / TTS / IMAGE / ...

    def get_model(self, model_name: str, credential: dict, **kwargs: Any):
        raise NotImplementedError
