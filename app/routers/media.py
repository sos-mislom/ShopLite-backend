import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
import mimetypes

from app.config import settings
from app.services.auth_service import AuthService

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/upload")
async def upload_image(
    file: Annotated[UploadFile, File(...)],
    current_user=Depends(AuthService.get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")

    suffix = Path(file.filename or "").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{suffix}"
    upload_dir = Path(settings.MEDIA_ROOT)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest_path = upload_dir / filename

    contents = await file.read()
    with open(dest_path, "wb") as out:
        out.write(contents)

    # Статическая раздача /uploads может быть недоступна за прокси,
    # поэтому отдаём API-путь, который точно проходит: /v1/api/media/upload/{filename}
    api_path = f"/v1/api/media/upload/{filename}"
    return {"url": api_path, "filename": filename}


@router.get("/upload/{filename}")
async def get_uploaded_image(filename: str):
    upload_dir = Path(settings.MEDIA_ROOT)
    file_path = (upload_dir / filename).resolve()
    try:
        file_path.relative_to(upload_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(str(file_path), media_type=media_type or "application/octet-stream")
