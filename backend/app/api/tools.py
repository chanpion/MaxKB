"""Tool + tool-folder CRUD API.

Mirrors the legacy ``apps/tools`` views but is provider-agnostic. Custom tool
``code`` is executed (inside the workflow sandbox) by :class:`app.tools.code_tool.CodeTool`;
built-in tools live in the shared registry.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import get_current_user
from app.models.tool import Tool, ToolFolder, ToolWorkflow, ToolWorkflowVersion
from app.models.user import User
from app.schemas.tool import (
    ToolCreate,
    ToolFolderCreate,
    ToolFolderOut,
    ToolOut,
    ToolPage,
    ToolUpdate,
    ToolWorkflowCreate,
    ToolWorkflowOut,
    ToolWorkflowVersionOut,
)

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


# ---------------------------------------------------------------------------
# Tool sub-routes (MUST come before /{tool_id} catch-all)
# ---------------------------------------------------------------------------


@router.put("/upload_skill_file")
async def upload_skill_file(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload a skill file."""
    content = await file.read()
    return {"result": True, "file_name": file.filename, "size": len(content)}


@router.post("/test_connection")
async def test_connection(
    body: dict,
    _: User = Depends(get_current_user),
) -> dict:
    return {"result": True}


@router.post("/pylint")
async def pylint_check(
    body: dict,
    _: User = Depends(get_current_user),
) -> dict:
    return {"result": True, "errors": []}


@router.post("/generate_code")
async def generate_code(
    body: dict,
    _: User = Depends(get_current_user),
) -> dict:
    return {"result": True, "code": ""}


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


# ---------------------------- tool workflows ----------------------------------


@router.get("/{tool_id}/workflow", response_model=ToolWorkflowOut)
async def get_tool_workflow(
    tool_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ToolWorkflowOut:
    result = await session.execute(select(ToolWorkflow).where(ToolWorkflow.tool_id == tool_id))
    workflow = result.scalar_one_or_none()
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return ToolWorkflowOut.model_validate(workflow)


@router.post("/{tool_id}/workflow", response_model=ToolWorkflowOut, status_code=status.HTTP_201_CREATED)
async def create_tool_workflow(
    tool_id: str,
    body: ToolWorkflowCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ToolWorkflowOut:
    tool = await session.get(Tool, tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")

    # Update or create
    result = await session.execute(select(ToolWorkflow).where(ToolWorkflow.tool_id == tool_id))
    workflow = result.scalar_one_or_none()
    if workflow:
        workflow.work_flow = body.work_flow
    else:
        workflow = ToolWorkflow(
            tool_id=tool_id,
            workspace_id=tool.workspace_id,
            work_flow=body.work_flow,
        )
        session.add(workflow)

    await session.commit()
    await session.refresh(workflow)
    return ToolWorkflowOut.model_validate(workflow)


@router.put("/{tool_id}/publish", response_model=ToolWorkflowOut)
async def publish_tool_workflow(
    tool_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ToolWorkflowOut:
    result = await session.execute(select(ToolWorkflow).where(ToolWorkflow.tool_id == tool_id))
    workflow = result.scalar_one_or_none()
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    workflow.is_publish = True
    workflow.publish_time = datetime.now()

    # Create version snapshot
    version = ToolWorkflowVersion(
        tool_id=tool_id,
        workspace_id=workflow.workspace_id,
        name=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        work_flow=workflow.work_flow,
        publish_user_id=current_user.id,
        publish_user_name=current_user.username,
    )
    session.add(version)
    await session.commit()
    await session.refresh(workflow)
    return ToolWorkflowOut.model_validate(workflow)


@router.get("/{tool_id}/workflow/versions", response_model=list[ToolWorkflowVersionOut])
async def list_tool_workflow_versions(
    tool_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[ToolWorkflowVersionOut]:
    result = await session.execute(
        select(ToolWorkflowVersion)
        .where(ToolWorkflowVersion.tool_id == tool_id)
        .order_by(ToolWorkflowVersion.create_time.desc())
    )
    rows = result.scalars().all()
    return [ToolWorkflowVersionOut.model_validate(v) for v in rows]


# ---------------------------- batch operations ---------------------------------


@router.put("/batch_delete")
async def batch_delete_tools(
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    ids = body.get("ids", [])
    if ids:
        result = await session.execute(select(Tool).where(Tool.id.in_(ids)))
        for tool in result.scalars().all():
            await session.delete(tool)
        await session.commit()
    return {"result": True, "deleted": len(ids)}


@router.put("/batch_move")
async def batch_move_tools(
    body: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    ids = body.get("ids", [])
    folder_id = body.get("folder_id", "default")
    if ids:
        result = await session.execute(select(Tool).where(Tool.id.in_(ids)))
        for tool in result.scalars().all():
            tool.folder_id = folder_id
        await session.commit()
    return {"result": True, "moved": len(ids)}


# ---------------------------------------------------------------------------
# Legacy path-based pagination (must be last to avoid shadowing sub-routes)
# ---------------------------------------------------------------------------


@router.get("/{page}/{page_size}")
async def list_tools_paginated(
    page: int,
    page_size: int,
    folder_id: str | None = None,
    scope: str | None = None,
    tool_type: str | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    conditions = []
    if folder_id:
        conditions.append(Tool.folder_id == folder_id)
    if scope:
        conditions.append(Tool.scope == scope)
    if tool_type:
        conditions.append(Tool.tool_type == tool_type)
    total = await session.scalar(select(func.count()).select_from(Tool).where(*conditions))
    result = await session.execute(
        select(Tool)
        .where(*conditions)
        .order_by(Tool.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()
    return {"records": [ToolOut.model_validate(t) for t in rows], "total": total or 0}
