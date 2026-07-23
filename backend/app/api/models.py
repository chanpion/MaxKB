"""Model-provider API — CRUD, provider catalog, model management."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user
from app.models.models_provider import Model
from app.models.user import User
from app.providers.catalog import PROVIDER_CATALOG, list_providers
from app.schemas.model import ModelCreate, ModelOut, ProviderInfo

router = APIRouter(prefix="/api/model", tags=["model"])


# ---------------------------------------------------------------------------
# Provider catalog sub-routes (must come before /{model_id})
# ---------------------------------------------------------------------------


@router.get("/providers", response_model=list[ProviderInfo])
async def provider_catalog(
    model_type: str | None = Query(None),
    _: User = Depends(get_current_user),
) -> list[ProviderInfo]:
    """Catalog of supported providers, optionally filtered by model_type."""
    providers = [ProviderInfo(**p) for p in list_providers()]
    if model_type:
        providers = [p for p in providers if model_type in (p.model_types or [])]
    return providers


# Human-readable labels for model types (aligned with legacy ``ModelTypeConst``).
MODEL_TYPE_LABELS: dict[str, str] = {
    "LLM": "大语言模型",
    "EMBEDDING": "向量模型",
    "STT": "语音识别",
    "TTS": "语音合成",
    "IMAGE": "视觉模型",
    "TTI": "图片生成",
    "RERANKER": "重排模型",
    "TTV": "文生视频",
    "ITV": "图生视频",
}


@router.get("/providers/model_type_list")
async def provider_model_type_list(
    provider: str | None = Query(None),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """List model types for a given provider as KeyValue pairs ``{key: label, value: code}``."""
    if provider:
        meta = PROVIDER_CATALOG.get(provider)
        types = meta.get("model_types", []) if meta else []
    else:
        # Return all unique model types across all providers
        unique: set[str] = set()
        for meta in PROVIDER_CATALOG.values():
            unique.update(meta.get("model_types", []))
        types = sorted(unique)
    return [{"key": MODEL_TYPE_LABELS.get(t, t), "value": t} for t in types]


# Known model names per provider/model_type combo
_MODEL_NAMES: dict[str, dict[str, list[str]]] = {
    "openai": {
        "LLM": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o3-mini", "o1"],
        "EMBEDDING": ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
    },
    "deepseek": {
        "LLM": ["deepseek-chat", "deepseek-reasoner"],
        "EMBEDDING": ["deepseek-text-embedding"],
    },
    "qwen": {
        "LLM": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen2.5-72b-instruct", "qwq-32b"],
        "EMBEDDING": ["text-embedding-v3"],
        "TTS": ["cosyvoice-v1", "sambert-zhichu-v1"],
    },
    "zhipu": {
        "LLM": ["glm-4-plus", "glm-4-flash", "glm-4-air"],
        "EMBEDDING": ["embedding-3"],
    },
    "anthropic": {"LLM": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]},
    "kimi": {"LLM": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]},
    "ollama": {"LLM": [], "EMBEDDING": []},
    "xunfei": {
        "LLM": ["spark-lite", "spark-v4.0", "spark-max"],
        "TTS": ["tts-xunfei-v1"],
        "STT": ["stt-xunfei-v1"],
    },
    "tencent": {
        "LLM": ["hunyuan-turbos-latest", "hunyuan-lite"],
        "EMBEDDING": ["hunyuan-embedding"],
    },
    "volcanic": {
        "LLM": ["doubao-pro-256k", "doubao-lite-128k"],
        "EMBEDDING": ["doubao-embedding"],
    },
    "local": {"LLM": [], "EMBEDDING": []},
}


@router.get("/providers/model_list")
async def provider_model_list(
    provider: str = Query(...),
    model_type: str = Query(...),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """List available model names for a provider/model_type combination as ``BaseModel`` objects."""
    names = _MODEL_NAMES.get(provider, {}).get(model_type, [])
    return [{"name": n, "desc": "", "model_type": model_type} for n in names]


@router.post("/providers/model_params_form")
async def provider_model_params_form(
    body: dict,
    _: User = Depends(get_current_user),
) -> dict:
    """Return credential form + model params form for a provider/model_type/model_name."""
    provider_name = body.get("provider", "")
    provider_meta = PROVIDER_CATALOG.get(provider_name, {})
    return {
        "credential_form": provider_meta.get("credential_form", []),
        "model_params_form": {},
    }


@router.post("/providers/model_form")
async def provider_model_form(
    body: dict,
    _: User = Depends(get_current_user),
) -> dict:
    """Return the complete model creation form metadata for a provider."""
    provider_name = body.get("provider", "")
    model_type = body.get("model_type", "")
    provider_meta = PROVIDER_CATALOG.get(provider_name, {})
    model_names = _MODEL_NAMES.get(provider_name, {}).get(model_type, [])
    return {
        "provider": provider_name,
        "name": provider_meta.get("name", ""),
        "model_type": model_type,
        "model_list": model_names,
        "credential_form": provider_meta.get("credential_form", []),
        "model_params_form": {},
    }


@router.get("/providers/model_params_form")
async def provider_model_params_form_get(
    provider: str = Query(...),
    model_type: str = Query(...),
    model_name: str = Query(...),
    _: User = Depends(get_current_user),
) -> dict:
    """GET variant of model params form (legacy frontend)."""
    provider_meta = PROVIDER_CATALOG.get(provider, {})
    return {
        "credential_form": provider_meta.get("credential_form", []),
        "model_params_form": {},
    }


@router.get("/providers/model_form")
async def provider_model_form_get(
    provider: str = Query(...),
    model_type: str = Query(...),
    model_name: str = Query(...),
    _: User = Depends(get_current_user),
) -> dict:
    """GET variant of model creation form (legacy frontend)."""
    provider_meta = PROVIDER_CATALOG.get(provider, {})
    model_names = _MODEL_NAMES.get(provider, {}).get(model_type, [])
    return {
        "provider": provider,
        "name": provider_meta.get("name", ""),
        "model_type": model_type,
        "model_list": model_names,
        "credential_form": provider_meta.get("credential_form", []),
        "model_params_form": {},
    }


# ---------------------------------------------------------------------------
# Model list (with query-param pagination)
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ModelOut])
async def list_models(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[ModelOut]:
    result = await session.execute(select(Model).order_by(Model.create_time.desc()))
    return [ModelOut.model_validate(m) for m in result.scalars().all()]


# ---------------------------------------------------------------------------
# Model dropdown list (no pagination, used by select dropdowns)
# ---------------------------------------------------------------------------


@router.get("/list")
async def model_dropdown_list(
    model_type: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Compact dropdown list of all models, split by scope."""
    conditions = []
    if model_type:
        conditions.append(Model.model_type == model_type)
    result = await session.execute(select(Model).where(*conditions).order_by(Model.name))
    model_list = [
        {
            "id": str(m.id),
            "name": m.name,
            "model_type": m.model_type,
            "provider": m.provider,
            "model_name": m.model_name,
            "status": m.status,
        }
        for m in result.scalars().all()
    ]
    return {
        "shared_model": [],
        "model": model_list,
    }


# ---------------------------------------------------------------------------
# Model list (shared workspace variant — /system/shared/model)
# ---------------------------------------------------------------------------


@router.get("/shared")
async def shared_models(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[ModelOut]:
    result = await session.execute(select(Model).order_by(Model.create_time.desc()))
    return [ModelOut.model_validate(m) for m in result.scalars().all()]


@router.get("/shared/{model_id}")
async def shared_model_detail(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ModelOut:
    model = await session.get(Model, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return ModelOut.model_validate(model)


@router.post("/shared", response_model=ModelOut, status_code=status.HTTP_201_CREATED)
async def create_shared_model(
    body: ModelCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ModelOut:
    return await _create_model(body, session, current_user)


@router.put("/shared/{model_id}", response_model=ModelOut)
async def update_shared_model(
    model_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ModelOut:
    return await _update_model(model_id, body, session)


@router.delete("/shared/{model_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_shared_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    await _delete_model(model_id, session)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def _create_model(body: ModelCreate, session: AsyncSession, current_user: User) -> ModelOut:
    model = Model(
        name=body.name,
        model_type=body.model_type,
        model_name=body.model_name,
        provider=body.provider,
        credential=json.dumps(body.credential, ensure_ascii=False)
        if isinstance(body.credential, dict)
        else body.credential,
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


@router.post("", response_model=ModelOut, status_code=status.HTTP_201_CREATED)
async def create_model(
    body: ModelCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ModelOut:
    return await _create_model(body, session, current_user)


# ---------------------------------------------------------------------------
# Model detail & mutation
# ---------------------------------------------------------------------------


async def _update_model(model_id: str, body: dict, session: AsyncSession) -> ModelOut:
    model = await session.get(Model, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    for field, value in body.items():
        if hasattr(model, field) and value is not None:
            setattr(model, field, value)
    await session.commit()
    await session.refresh(model)
    return ModelOut.model_validate(model)


async def _delete_model(model_id: str, session: AsyncSession) -> None:
    model = await session.get(Model, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    await session.delete(model)
    await session.commit()


# ---------------------------------------------------------------------------
# Model folders (for generic workspace folder API)
# ---------------------------------------------------------------------------


@router.get("/folder")
async def list_model_folders(
    _: User = Depends(get_current_user),
) -> list[dict]:
    return []


@router.post("/folder", status_code=status.HTTP_201_CREATED)
async def create_model_folder(
    _: User = Depends(get_current_user),
) -> dict:
    return {"result": True}


@router.get("/{model_id}", response_model=ModelOut)
async def get_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ModelOut:
    # Guard against non-UUID segments (e.g. legacy path rewrites) reaching the DB.
    try:
        uuid.UUID(model_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found") from None
    model = await session.get(Model, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return ModelOut.model_validate(model)


@router.put("/{model_id}", response_model=ModelOut)
async def update_model(
    model_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ModelOut:
    return await _update_model(model_id, body, session)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    await _delete_model(model_id, session)


# ---------------------------------------------------------------------------
# Model detail operations
# ---------------------------------------------------------------------------


@router.get("/{model_id}/model_params_form")
async def get_model_params_form(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    model = await session.get(Model, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model.model_params_form or {}


@router.put("/{model_id}/model_params_form")
async def update_model_params_form(
    model_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    model = await session.get(Model, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    model.model_params_form = body
    await session.commit()
    return {"result": True}


@router.get("/{model_id}/meta")
async def get_model_meta(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Model metadata without credentials."""
    model = await session.get(Model, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return {
        "id": str(model.id),
        "name": model.name,
        "model_type": model.model_type,
        "model_name": model.model_name,
        "provider": model.provider,
        "status": model.status,
        "meta": model.meta,
    }


@router.put("/{model_id}/pause_download")
async def pause_model_download(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    model = await session.get(Model, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    model.status = "PAUSE"
    await session.commit()
    return {"result": True}


# ---------------------------------------------------------------------------
# Path-based pagination (must be last to avoid shadowing sub-routes)
# ---------------------------------------------------------------------------


@router.get("/{page}/{page_size}")
async def list_models_paginated(
    page: int,
    page_size: int,
    name: str | None = Query(None),
    model_type: str | None = Query(None),
    provider: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Legacy path-based pagination: ``/{page}/{page_size}``."""
    conditions = []
    if name:
        conditions.append(Model.name.ilike(f"%{name}%"))
    if model_type:
        conditions.append(Model.model_type == model_type)
    if provider:
        conditions.append(Model.provider == provider)
    total = await session.scalar(select(func.count()).select_from(Model).where(*conditions))
    result = await session.execute(
        select(Model)
        .where(*conditions)
        .order_by(Model.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()
    return {"records": [ModelOut.model_validate(m) for m in rows], "total": total or 0}
