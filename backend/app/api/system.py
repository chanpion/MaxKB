"""System API: operation logs + system settings.

Read-only / admin surfaces over the legacy ``log`` and ``system_setting`` tables.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import require_roles
from app.models.system import Log, SystemSetting
from app.models.user import User
from app.schemas.common import PageData

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/log", response_model=PageData)
async def list_logs(
    page: int = 1,
    size: int = 20,
    operate: str | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> PageData:
    conditions = []
    if operate is not None:
        conditions.append(Log.operate == operate)
    total = await session.scalar(select(func.count()).select_from(Log).where(*conditions))
    result = await session.execute(
        select(Log).where(*conditions).order_by(Log.create_time.desc()).offset((page - 1) * size).limit(size)
    )
    rows = result.scalars().all()
    return PageData(**{"list": [r.id for r in rows], "total": total or 0})


@router.get("/setting", response_model=list[dict])
async def list_settings(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> list[dict]:
    result = await session.execute(select(SystemSetting))
    return [{"type": s.type, "meta": s.meta} for s in result.scalars().all()]


@router.get("/setting/{setting_type}", response_model=dict)
async def get_setting(
    setting_type: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> dict:
    setting = await session.get(SystemSetting, setting_type)
    if setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return {"type": setting.type, "meta": setting.meta}
