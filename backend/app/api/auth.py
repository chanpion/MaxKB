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
from app.core.password import verify_password
from app.core.security import create_access_token, get_current_user, require_roles
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, UserOut

router = APIRouter(prefix="/api/user", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)) -> Token:
    result = await session.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.get("", response_model=list[UserOut])
async def list_users(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> list[UserOut]:
    result = await session.execute(select(User).order_by(User.create_time.desc()))
    return [UserOut.model_validate(u) for u in result.scalars().all()]


# Re-export uuid so static analyzers don't flag the import; (kept for symmetry)
_ = uuid
