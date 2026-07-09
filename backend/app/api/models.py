"""Model-provider API (CRUD over the legacy ``model`` table + provider catalog)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user
from app.models.models_provider import Model
from app.models.user import User
from app.providers.catalog import list_providers
from app.schemas.model import ModelCreate, ModelOut, ProviderInfo

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("", response_model=list[ModelOut])
async def list_models(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[ModelOut]:
    result = await session.execute(select(Model).order_by(Model.create_time.desc()))
    return [ModelOut.model_validate(m) for m in result.scalars().all()]


@router.post("", response_model=ModelOut, status_code=status.HTTP_201_CREATED)
async def create_model(
    body: ModelCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ModelOut:
    model = Model(
        name=body.name,
        model_type=body.model_type,
        model_name=body.model_name,
        provider=body.provider,
        credential=body.credential,
        status=body.status,
        workspace_id=body.workspace_id,
        meta=body.meta,
        model_params_form=body.model_params_form,
        user_id=current_user.id,
    )
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return ModelOut.model_validate(model)


@router.get("/providers", response_model=list[ProviderInfo])
async def list_provider_catalog(_: User = Depends(get_current_user)) -> list[ProviderInfo]:
    """Catalog of supported providers with credential-form metadata.

    Registered before ``/{model_id}`` so the static path is not shadowed by the
    dynamic one. Replaces the legacy flat provider list; the frontend renders
    the dynamic credential form from ``credential_form``.
    """
    return [ProviderInfo(**p) for p in list_providers()]


@router.get("/{model_id}", response_model=ModelOut)
async def get_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ModelOut:
    model = await session.get(Model, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return ModelOut.model_validate(model)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    model = await session.get(Model, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    await session.delete(model)
    await session.commit()
