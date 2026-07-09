"""Password verification compatible with legacy Django hashes.

The shared PostgreSQL ``user`` table stores Django-style password strings. We
support the common formats (pbkdf2_sha256, bcrypt) plus a plaintext fallback
for local/test accounts, so the new backend can authenticate against existing
rows without re-hashing.
"""

from __future__ import annotations

import base64
import hashlib

import bcrypt


def verify_password(plain: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("bcrypt$"):
        raw = stored[len("bcrypt$") :]
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), raw.encode("utf-8"))
        except (ValueError, TypeError):
            return False
    if stored.startswith(("$2b$", "$2a$")):
        # Standard bcrypt hash, as produced by ``hash_password`` / bcrypt.hashpw.
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
        except (ValueError, TypeError):
            return False
    if stored.startswith("pbkdf2_"):
        # format: pbkdf2_sha256$iterations$salt$hash_b64  (4 fields)
        try:
            algo, iters, salt, hash_b64 = stored.split("$")
            digest = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt.encode("utf-8"), int(iters))
            return base64.b64encode(digest).decode("utf-8") == hash_b64
        except (ValueError, TypeError):
            return False
    # plaintext fallback (local/test accounts)
    return plain == stored


def hash_password(plain: str) -> str:
    """Return a bcrypt hash for new local accounts."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
