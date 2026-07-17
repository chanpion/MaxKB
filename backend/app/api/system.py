"""System API: operation logs, system settings, permissions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user, require_roles
from app.models.system import Log, ResourceMapping, SystemSetting, WorkspaceUserResourcePermission
from app.models.user import User
from app.schemas.common import PageData

router = APIRouter(prefix="/api/system", tags=["system"])


# ---------------------------------------------------------------------------
# Public profile — used by the login page (no auth required)
# ---------------------------------------------------------------------------


@router.get("/profile")
async def system_profile(session: AsyncSession = Depends(get_session)) -> dict:
    """Public system profile for the login / admin UI pages."""
    from app.core.rsa_util import get_or_create_key_pair

    setting = await session.get(SystemSetting, 1)
    email_config = {}
    if setting and setting.meta:
        email_config = {
            "email_host": setting.meta.get("email_host", ""),
            "email_port": setting.meta.get("email_port", 587),
        }

    # RSA public key for frontend password encryption
    rsa_pair = await get_or_create_key_pair(session)
    public_key = rsa_pair.get("key", "")

    return {
        "name": "MaxKB",
        "version": "2.0.0",
        "email_setting": email_config,
        "rsa": public_key,
        "license_is_valid": False,
        "edition": "CE",
    }


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


# ---------------------------------------------------------------------------
# Permissions — workspace user resource permissions
# ---------------------------------------------------------------------------

# Mirrors Django ``ResourceUserPermissionSerializer.permission_map``.
RESOURCE_PERMISSION_MAP = {
    "ROLE": ("ROLE", ["ROLE"]),
    "MANAGE": ("RESOURCE_PERMISSION_GROUP", ["MANAGE", "VIEW"]),
    "VIEW": ("RESOURCE_PERMISSION_GROUP", ["VIEW"]),
    "NOT_AUTH": ("RESOURCE_PERMISSION_GROUP", []),
}


def _derive_permission(perm_row) -> str:
    """Translate a ``WorkspaceUserResourcePermission`` row into a single
    effective permission label (NOT_AUTH / ROLE / MANAGE / VIEW)."""
    if perm_row is None:
        return "NOT_AUTH"
    pl = perm_row.permission_list or []
    if perm_row.auth_type == "ROLE" and "ROLE" in pl:
        return "ROLE"
    if perm_row.auth_type == "RESOURCE_PERMISSION_GROUP":
        if "MANAGE" in pl:
            return "MANAGE"
        if "VIEW" in pl:
            return "VIEW"
    return "NOT_AUTH"


@router.get("/resource_user_permission/resource/{target}/resource/{resource}/{current_page}/{page_size}")
async def list_resource_user_permissions(
    target: str,
    resource: str,
    current_page: int = 1,
    page_size: int = 20,
    nick_name: str | None = None,
    username: str | None = None,
    permission: list[str] | None = Query(default=None),
    workspace_id: str = "default",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """List users and their effective permission for a given resource (paginated).

    Path mirrors the legacy Django
    ``/workspace/<ws>/resource_user_permission/resource/<target>/resource/<resource>/<page>/<size>``.
    ``resource`` may carry a ``_FOLDER`` suffix which is stripped to the
    underlying auth target type (e.g. ``KNOWLEDGE_FOLDER`` -> ``KNOWLEDGE``).
    Returns ``{"records": [...], "total": N}`` (the legacy response middleware
    wraps it as ``{code, data:{records,total}, message}``).
    """
    auth_target_type = resource.replace("_FOLDER", "")

    user_conditions = []
    if nick_name:
        user_conditions.append(User.nick_name.contains(nick_name))
    if username:
        user_conditions.append(User.username.contains(username))
    users = (
        await session.execute(select(User).where(*user_conditions).order_by(User.nick_name))
    ).scalars().all()

    perm_rows = (
        await session.execute(
            select(WorkspaceUserResourcePermission).where(
                WorkspaceUserResourcePermission.workspace_id == workspace_id,
                WorkspaceUserResourcePermission.auth_target_type == auth_target_type,
                WorkspaceUserResourcePermission.target == target,
            )
        )
    ).scalars().all()
    perm_by_user = {p.user_id: p for p in perm_rows}

    records = []
    for u in users:
        perm = _derive_permission(perm_by_user.get(u.id))
        if permission and perm not in permission:
            continue
        records.append(
            {
                "id": str(u.id),
                "nick_name": u.nick_name,
                "username": u.username,
                "permission": perm,
            }
        )

    total = len(records)
    start = (current_page - 1) * page_size
    return {"records": records[start : start + page_size], "total": total}


@router.put("/resource_user_permission/resource/{target}/resource/{resource}")
async def edit_resource_user_permissions(
    target: str,
    resource: str,
    body: list[dict],
    workspace_id: str = "default",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Grant / revoke a list of users' permission on a resource.

    ``body`` is a list of ``{"user_id": ..., "permission": "VIEW"|"MANAGE"|"ROLE"|"NOT_AUTH",
    "include_children"?: bool, "folder_ids"?: [...]}`` (mirrors the Django
    ``ResourceUserPermissionSerializer.edit`` contract).
    """
    auth_target_type = resource.replace("_FOLDER", "")
    if not isinstance(body, list) or len(body) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty permission list")

    user_ids = [item.get("user_id") for item in body]
    include_children = body[0].get("include_children")
    folder_ids = body[0].get("folder_ids") or []
    if include_children and folder_ids:
        managed_resource_ids = list(folder_ids) + [target]
    else:
        managed_resource_ids = [target]
    # de-duplicate while preserving order
    managed_resource_ids = list(dict.fromkeys(managed_resource_ids))

    await session.execute(
        delete(WorkspaceUserResourcePermission).where(
            WorkspaceUserResourcePermission.workspace_id == workspace_id,
            WorkspaceUserResourcePermission.target.in_(managed_resource_ids),
            WorkspaceUserResourcePermission.auth_target_type == auth_target_type,
            WorkspaceUserResourcePermission.user_id.in_(user_ids),
        )
    )

    new_rows = []
    for resource_id in managed_resource_ids:
        for item in body:
            perm = item.get("permission", "VIEW")
            if perm not in RESOURCE_PERMISSION_MAP:
                continue
            auth_type, perm_list = RESOURCE_PERMISSION_MAP[perm]
            new_rows.append(
                WorkspaceUserResourcePermission(
                    workspace_id=workspace_id,
                    user_id=item.get("user_id"),
                    auth_target_type=auth_target_type,
                    target=resource_id,
                    auth_type=auth_type,
                    permission_list=perm_list,
                )
            )
    session.add_all(new_rows)
    await session.commit()
    return {"code": 200, "data": None, "message": "success"}


@router.get("/permission/user/{user_id}/resource/{resource_type}")
async def list_user_permissions(
    user_id: str,
    resource_type: str,
    workspace_id: str = "default",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[dict]:
    result = await session.execute(
        select(WorkspaceUserResourcePermission).where(
            WorkspaceUserResourcePermission.workspace_id == workspace_id,
            WorkspaceUserResourcePermission.user_id == user_id,
            WorkspaceUserResourcePermission.auth_target_type == resource_type,
        )
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "target": r.target,
            "auth_type": r.auth_type,
            "permission_list": r.permission_list,
        }
        for r in rows
    ]


@router.post("/permission/user/{user_id}/resource/{resource_type}", status_code=status.HTTP_201_CREATED)
async def grant_permission(
    user_id: str,
    resource_type: str,
    body: dict,
    workspace_id: str = "default",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    target = body.get("target", "")
    permission = WorkspaceUserResourcePermission(
        workspace_id=workspace_id,
        user_id=user_id,
        auth_target_type=resource_type,
        target=target,
        auth_type=body.get("auth_type", "ROLE"),
        permission_list=body.get("permission_list", ["VIEW"]),
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    return {
        "id": str(permission.id),
        "target": permission.target,
        "auth_type": permission.auth_type,
        "permission_list": permission.permission_list,
    }


@router.delete("/permission/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission(
    permission_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    permission = await session.get(WorkspaceUserResourcePermission, permission_id)
    if permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    await session.delete(permission)
    await session.commit()


@router.get("/email_setting")
async def get_email_setting(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> dict:
    setting = await session.get(SystemSetting, 1)
    if setting is None or not setting.meta.get("email_host"):
        return {"configured": False, "email_host": "", "email_port": 587}
    return {"configured": True, **setting.meta}


@router.put("/email_setting")
async def update_email_setting(
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
) -> dict:
    setting = await session.get(SystemSetting, 1)
    if setting is None:
        setting = SystemSetting(type=1, meta=body)
        session.add(setting)
    else:
        setting.meta = body
    await session.commit()
    return {"configured": True, **body}


# ---------------------------------------------------------------------------
# Resource mappings
# ---------------------------------------------------------------------------


@router.get("/resource_mapping/{resource_type}/{resource_id}")
async def get_resource_mapping(
    resource_type: str,
    resource_id: str,
    target_type: str | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[dict]:
    conditions = [
        ResourceMapping.source_type == resource_type,
        ResourceMapping.source_id == resource_id,
    ]
    if target_type:
        conditions.append(ResourceMapping.target_type == target_type)

    result = await session.execute(select(ResourceMapping).where(*conditions))
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "source_type": r.source_type,
            "target_type": r.target_type,
            "source_id": r.source_id,
            "target_id": r.target_id,
        }
        for r in rows
    ]
