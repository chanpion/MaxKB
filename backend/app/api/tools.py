"""Tool + tool-folder CRUD API.

Mirrors the legacy ``apps/tools`` views but is provider-agnostic. Custom tool
``code`` is executed (inside the workflow sandbox) by :class:`app.tools.code_tool.CodeTool`;
built-in tools live in the shared registry.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user
from app.models.tool import Tool, ToolFolder
from app.models.user import User
from app.schemas.tool import ToolCreate, ToolFolderCreate, ToolFolderOut, ToolOut, ToolPage, ToolUpdate

router = APIRouter(prefix="/api/tool", tags=["tool"])


# ----------------------------- folders ----------------------------------- #
@router.get("/folder", response_model=list[ToolFolderOut])
async def list_tool_folders(
    workspace_id: str = "default",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[ToolFolderOut]:
    result = await session.execute(
        select(ToolFolder).where(ToolFolder.workspace_id == workspace_id).order_by(ToolFolder.lft.asc())
    )
    return [ToolFolderOut.model_validate(f) for f in result.scalars().all()]


@router.post("/folder", response_model=ToolFolderOut, status_code=status.HTTP_201_CREATED)
async def create_tool_folder(
    body: ToolFolderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ToolFolderOut:
    folder = ToolFolder(
        name=body.name,
        desc=body.desc or None,
        parent_id=body.parent_id,
        workspace_id=body.workspace_id,
        user_id=current_user.id,
    )
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return ToolFolderOut.model_validate(folder)


# ------------------------------- tools ----------------------------------- #
@router.get("", response_model=ToolPage)
async def list_tools(
    page: int = 1,
    size: int = 10,
    folder_id: str | None = None,
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ToolPage:
    conditions = []
    if folder_id is not None:
        conditions.append(Tool.folder_id == folder_id)
    if is_active is not None:
        conditions.append(Tool.is_active == is_active)
    total = await session.scalar(select(func.count()).select_from(Tool).where(*conditions))
    result = await session.execute(
        select(Tool).where(*conditions).order_by(Tool.create_time.desc()).offset((page - 1) * size).limit(size)
    )
    rows = result.scalars().all()
    return ToolPage(list=[ToolOut.model_validate(t) for t in rows], total=total or 0)


@router.post("", response_model=ToolOut, status_code=status.HTTP_201_CREATED)
async def create_tool(
    body: ToolCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ToolOut:
    tool = Tool(
        name=body.name,
        desc=body.desc,
        code=body.code,
        tool_type=body.tool_type,
        folder_id=body.folder_id,
        workspace_id=body.workspace_id,
        icon=body.icon,
        is_active=body.is_active,
        input_field_list=body.input_field_list,
        init_field_list=body.init_field_list,
        init_params=body.init_params,
        label=body.label,
        user_id=current_user.id,
    )
    session.add(tool)
    await session.commit()
    await session.refresh(tool)
    return ToolOut.model_validate(tool)


@router.get("/{tool_id}", response_model=ToolOut)
async def get_tool(
    tool_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ToolOut:
    tool = await session.get(Tool, tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    return ToolOut.model_validate(tool)


@router.put("/{tool_id}", response_model=ToolOut)
async def update_tool(
    tool_id: str,
    body: ToolUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ToolOut:
    tool = await session.get(Tool, tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tool, field, value)
    await session.commit()
    await session.refresh(tool)
    return ToolOut.model_validate(tool)


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    tool = await session.get(Tool, tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    await session.delete(tool)
    await session.commit()
