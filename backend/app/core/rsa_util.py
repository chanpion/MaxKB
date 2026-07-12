"""RSA key-pair management compatible with legacy Django rsa_util.

Key pairs are stored in the ``system_setting`` table (type=3).  On first use
a 2048-bit key is generated and persisted.
"""

from __future__ import annotations

import base64
from functools import lru_cache

from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
from Crypto.PublicKey import RSA
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

SECRET_CODE = "mac_kb_password"
RSA_SETTING_TYPE = 3


def _generate_key_pair() -> dict:
    key = RSA.generate(2048)
    encrypted_key = key.export_key(passphrase=SECRET_CODE, pkcs=8, protection="scryptAndAES128-CBC")
    return {
        "key": key.publickey().export_key().decode(),
        "value": encrypted_key.decode(),
    }


@lru_cache(maxsize=1)
def _get_cipher(pri_key: str):
    return PKCS1_cipher.new(RSA.import_key(pri_key, passphrase=SECRET_CODE))


async def get_or_create_key_pair(session: AsyncSession) -> dict:
    """Return ``{key: public_pem, value: private_pem}``, creating if needed."""
    from app.models.system import SystemSetting

    result = await session.execute(select(SystemSetting).where(SystemSetting.type == RSA_SETTING_TYPE))
    setting = result.scalar_one_or_none()
    if setting is None:
        kv = _generate_key_pair()
        setting = SystemSetting(type=RSA_SETTING_TYPE, meta=kv)
        session.add(setting)
        await session.commit()
        await session.refresh(setting)
    return setting.meta or {}


def decrypt(encrypted_msg: str, pri_key: str | None = None) -> str:
    """Decrypt an RSA-encrypted base64 message using *pri_key*."""
    cipher = _get_cipher(pri_key)
    raw = cipher.decrypt(base64.b64decode(encrypted_msg), 0)
    if isinstance(raw, int):
        # Try long decrypt (JSEncrypt may split long messages)
        return rsa_long_decrypt(encrypted_msg, pri_key)
    return raw.decode("utf-8")


def rsa_long_decrypt(message: str, pri_key: str | None = None, length: int = 256) -> str:
    """Decrypt a long RSA-encrypted message (split into 256-byte blocks)."""
    cipher = _get_cipher(pri_key)
    base64_de = base64.b64decode(message)
    result = bytearray()
    for i in range(0, len(base64_de), length):
        block = cipher.decrypt(base64_de[i : i + length], 0)
        if isinstance(block, int):
            raise ValueError(f"RSA decrypt failed at block {i // length}")
        result.extend(block)
    return result.decode("utf-8")
