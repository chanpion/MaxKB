"""Trigger (scheduled / event task) API.

CRUD over the legacy ``event_trigger`` table plus manual execution via the
:class:`app.trigger.manager.TriggerManager`. Scheduled triggers are driven by
arq cron jobs registered at worker start (see ``app.core.tasks``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user, require_roles
from app.models.trigger import Trigger, TriggerTask
from app.models.user import User
from app.schemas.trigger import (
    TriggerCreate,
    TriggerOut,
    TriggerTaskOut,
    TriggerUpdate,
)

router = APIRouter(prefix="/api/trigger", tags=["trigger"])


@router.get("", response_model=list[TriggerOut])
async def list_triggers(
    workspace_id: str = "default",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[TriggerOut]:
    result = await session.execute(
        select(Trigger).where(Trigger.workspace_id == workspace_id).order_by(Trigger.create_time.desc())
    )
    return [TriggerOut.model_validate(t) for t in result.scalars().all()]


@router.post("", response_model=TriggerOut, status_code=status.HTTP_201_CREATED)
async def create_trigger(
    body: TriggerCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TriggerOut:
    trigger = Trigger(
        workspace_id=body.workspace_id,
        name=body.name,
        desc=body.desc,
        trigger_type=body.trigger_type,
        trigger_setting=body.trigger_setting,
        meta=body.meta,
        is_active=body.is_active,
        user_id=current_user.id,
    )
    session.add(trigger)
    await session.commit()
    await session.refresh(trigger)
    return TriggerOut.model_validate(trigger)


@router.get("/{trigger_id}", response_model=TriggerOut)
async def get_trigger(
    trigger_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> TriggerOut:
    trigger = await session.get(Trigger, trigger_id)
    if trigger is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trigger not found")
    return TriggerOut.model_validate(trigger)


@router.put("/{trigger_id}", response_model=TriggerOut)
async def update_trigger(
    trigger_id: str,
    body: TriggerUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> TriggerOut:
    trigger = await session.get(Trigger, trigger_id)
    if trigger is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trigger not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(trigger, field, value)
    await session.commit()
    await session.refresh(trigger)
    return TriggerOut.model_validate(trigger)


@router.delete("/{trigger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trigger(
    trigger_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    trigger = await session.get(Trigger, trigger_id)
    if trigger is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trigger not found")
    await session.delete(trigger)
    await session.commit()


@router.get("/{trigger_id}/tasks", response_model=list[TriggerTaskOut])
async def list_trigger_tasks(
    trigger_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[TriggerTaskOut]:
    trigger = await session.get(Trigger, trigger_id)
    if trigger is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trigger not found")
    result = await session.execute(select(TriggerTask).where(TriggerTask.trigger_id == trigger_id))
    return [TriggerTaskOut.model_validate(t) for t in result.scalars().all()]


@router.post("/{trigger_id}/run")
async def run_trigger(
    trigger_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> dict:
    """Manually execute a trigger's linked tasks (admin only)."""
    trigger = await session.get(Trigger, trigger_id)
    if trigger is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trigger not found")
    from app.trigger.manager import execute_trigger

    results = await execute_trigger(trigger_id)
    return {"trigger_id": trigger_id, "results": results}
