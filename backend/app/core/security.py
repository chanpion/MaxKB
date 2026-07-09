"""JWT authentication + RBAC dependencies (replaces Django auth)."""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.models.user import User

settings = get_settings()
ALGORITHM = "HS256"
# Derive a stable 32-byte HMAC secret from the configured password material so
# the key meets the HS256 minimum length (32 bytes). Externalize via a dedicated
# MAXKB_SECRET_KEY in production.
_JWT_SECRET = hashlib.sha256(settings.db_password.encode()).digest()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/user/login", auto_error=False)


def create_access_token(user_id: str, expires_minutes: int | None = None) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=expires_minutes or settings.session_timeout)
    payload = {"sub": str(user_id), "exp": exp}
    return jwt.encode(payload, _JWT_SECRET, algorithm=ALGORITHM)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from None
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*roles: str):
    """Dependency factory enforcing the user's `role` is in `roles`."""

    async def _checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if roles and current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return _checker
