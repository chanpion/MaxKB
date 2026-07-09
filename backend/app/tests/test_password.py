"""Password compatibility tests (no DB / Django required).

Verifies :mod:`app.core.password` against the legacy Django hash formats the
shared ``user`` table may contain, plus the native bcrypt path used for new
local accounts.
"""

from __future__ import annotations

import base64
import hashlib

from app.core.password import hash_password, verify_password


def test_plaintext_fallback():
    assert verify_password("secret", "secret") is True
    assert verify_password("secret", "other") is False


def test_pbkdf2_sha256():
    salt = "abc123"
    iters = 260000
    digest = hashlib.pbkdf2_hmac("sha256", b"hunter2", salt.encode(), iters)
    stored = f"pbkdf2_sha256${iters}${salt}${base64.b64encode(digest).decode()}"
    assert verify_password("hunter2", stored) is True
    assert verify_password("wrong", stored) is False


def test_bcrypt_prefixed():
    import bcrypt

    raw = bcrypt.hashpw(b"pw", bcrypt.gensalt()).decode()
    stored = "bcrypt$" + raw
    assert verify_password("pw", stored) is True
    assert verify_password("nope", stored) is False


def test_bcrypt_raw_hash_roundtrip():
    # hash_password() emits a standard $2b$ hash; verify_password must accept it.
    h = hash_password("localpw")
    assert h.startswith("$2b$") or h.startswith("$2a$")
    assert verify_password("localpw", h) is True
    assert verify_password("wrong", h) is False
