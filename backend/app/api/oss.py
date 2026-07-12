"""OSS file upload / download API."""

from __future__ import annotations

import hashlib
import os
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.core.security import get_current_user
from app.models.knowledge import File
from app.models.user import User

router = APIRouter(prefix="/api/oss", tags=["oss"])

settings = get_settings()
_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(_UPLOAD_DIR, exist_ok=True)


@router.post("/file")
async def upload_file(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    content = await file.read()
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate by hash
    existing = await session.execute(select(File).where(File.sha256_hash == sha256_hash))
    existing_file = existing.scalar_one_or_none()
    if existing_file:
        return {
            "id": str(existing_file.id),
            "file_name": existing_file.file_name,
            "file_size": existing_file.file_size,
            "duplicate": True,
        }

    # Save to disk
    file_id = _uuid.uuid4()
    ext = os.path.splitext(file.filename or "file")[1]
    disk_path = os.path.join(_UPLOAD_DIR, f"{file_id}{ext}")
    with open(disk_path, "wb") as f:
        f.write(content)

    db_file = File(
        id=file_id,
        file_name=file.filename or "file",
        file_size=len(content),
        sha256_hash=sha256_hash,
        source_type="UPLOAD",
        source_id=str(file_id),
        meta={"disk_path": disk_path, "content_type": file.content_type},
    )
    session.add(db_file)
    await session.commit()

    return {
        "id": str(file_id),
        "file_name": db_file.file_name,
        "file_size": db_file.file_size,
        "duplicate": False,
    }


@router.get("/file/{file_id}")
async def get_file(
    file_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> FileResponse:
    db_file = await session.get(File, file_id)
    if db_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    disk_path = (db_file.meta or {}).get("disk_path")
    if not disk_path or not os.path.exists(disk_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")

    return FileResponse(
        disk_path,
        filename=db_file.file_name,
        media_type=(db_file.meta or {}).get("content_type", "application/octet-stream"),
    )


@router.delete("/file/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    db_file = await session.get(File, file_id)
    if db_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    disk_path = (db_file.meta or {}).get("disk_path")
    if disk_path and os.path.exists(disk_path):
        os.remove(disk_path)

    await session.delete(db_file)
    await session.commit()
