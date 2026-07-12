"""Authentication + user management.

Mounted at prefix ``/api/user`` so the OAuth2 ``tokenUrl`` ("api/user/login")
matches. Login verifies against legacy Django password hashes.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.password import hash_password, verify_password
from app.core.security import create_access_token, get_current_user, require_roles
from app.models.user import User
from app.schemas.auth import (
    LanguageRequest,
    LoginRequest,
    LoginResponse,
    PasswordResetRequest,
    ProfileUpdate,
    UserCreate,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/api/user", tags=["auth"])


def _to_user_out(user: User) -> UserOut:
    """Convert a User model to UserOut with frontend-compatible role/permission arrays."""
    base_role = (user.role or "USER").strip()
    role_list = [r.strip() for r in base_role.split(",") if r.strip()] or ["USER"]
    # Include workspace-scoped variants and basic roles for menu access
    ws_role_list = list(role_list)
    for r in role_list:
        ws_role_list.append(f"{r}:/WORKSPACE/default")
    # Admin gets USER role for basic menu access
    if "ADMIN" in role_list and "USER" not in role_list:
        ws_role_list.append("USER")
        ws_role_list.append("USER:/WORKSPACE/default")
    permissions = list(ws_role_list)
    if "ADMIN" in role_list:
        permissions.append("SYSTEM_MANAGE")
    return UserOut(
        id=user.id,
        username=user.username,
        nick_name=user.nick_name or user.username,
        email=user.email,
        role=ws_role_list,
        permissions=permissions,
        is_active=user.is_active,
        source=user.source or "LOCAL",
        language=user.language,
        create_time=user.create_time,
    )


# ---------------------------------------------------------------------------
# Legacy path aliases — map old Django URLs to new FastAPI handlers
# ---------------------------------------------------------------------------


@router.get("/profile", response_model=UserOut)
async def profile_alias(current_user: User = Depends(get_current_user)) -> UserOut:
    """Legacy alias for ``GET /api/user/me`` (old: ``/user/profile``)."""
    return _to_user_out(current_user)


@router.get("/list", response_model=list[UserOut])
async def list_users_alias(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> list[UserOut]:
    """Legacy alias for ``GET /api/user`` (old: ``/user/list``)."""
    result = await session.execute(select(User).order_by(User.create_time.desc()))
    return [_to_user_out(u) for u in result.scalars().all()]


@router.get("/logout")
async def logout() -> dict:
    """Legacy logout endpoint — JWT is stateless, always succeeds."""
    return {"code": 200, "data": None, "message": "success"}


@router.post("/re_password")
async def re_password_alias(
    body: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Legacy alias for ``PUT /api/user/password`` (old: ``/user/re_password``)."""
    if not verify_password(body.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid old password")
    current_user.password = hash_password(body.new_password)
    await session.commit()
    return {"code": 200, "data": None, "message": "success"}


@router.get("/captcha")
async def captcha(username: str = "") -> dict:
    """Captcha endpoint for login page."""
    import base64
    import secrets

    key = secrets.token_hex(16)
    return {"key": key, "image": base64.b64encode(b"captcha-placeholder").decode()}


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)) -> LoginResponse:
    import json as _json

    username = body.username
    password = body.password

    # Decrypt RSA-encrypted login payload if present
    encrypted_data = getattr(body, "encryptedData", None) or (body.model_extra or {}).get("encryptedData")
    if encrypted_data:
        from app.core.rsa_util import decrypt, get_or_create_key_pair

        rsa_pair = await get_or_create_key_pair(session)
        pri_key = rsa_pair.get("value", "")
        if pri_key:
            try:
                decrypted_raw = decrypt(encrypted_data, pri_key)
                decrypted_fields = _json.loads(decrypted_raw) if decrypted_raw else {}
                if isinstance(decrypted_fields, dict):
                    password = decrypted_fields.get("password", password)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid encrypted data") from None

    if not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")

    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token_str = create_access_token(str(user.id))
    return LoginResponse.create(token_str)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return _to_user_out(current_user)


@router.get("", response_model=list[UserOut])
async def list_users(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> list[UserOut]:
    result = await session.execute(select(User).order_by(User.create_time.desc()))
    return [_to_user_out(u) for u in result.scalars().all()]


# ---------------------------------------------------------------------------
# Profile management
# ---------------------------------------------------------------------------


@router.put("/me", response_model=UserOut)
async def update_profile(
    body: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await session.commit()
    await session.refresh(current_user)
    return _to_user_out(current_user)


@router.put("/language")
async def switch_language(
    body: LanguageRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    current_user.language = body.language
    await session.commit()
    return {"result": True, "language": body.language}


@router.put("/password")
async def reset_password(
    body: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not verify_password(body.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid old password")
    current_user.password = hash_password(body.new_password)
    await session.commit()
    return {"result": True}


# ---------------------------------------------------------------------------
# User management (admin)
# ---------------------------------------------------------------------------


@router.post("/manage", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> UserOut:
    # Check uniqueness
    existing = await session.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    user = User(
        username=body.username,
        nick_name=body.nick_name,
        email=body.email,
        password=hash_password(body.password),
        role=body.role,
        phone=body.phone,
        is_active=body.is_active,
        source="LOCAL",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return _to_user_out(user)


@router.put("/manage/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    body: UserUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> UserOut:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return _to_user_out(user)


@router.delete("/manage/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> None:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await session.delete(user)
    await session.commit()


# Re-export uuid so static analyzers don't flag the import; (kept for symmetry)
_ = uuid
