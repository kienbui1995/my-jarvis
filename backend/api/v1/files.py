"""File upload endpoint — store in MinIO, return key + URL."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from core.deps import get_current_user_id
from services.storage import get_file_url, upload_file

router = APIRouter()

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "application/pdf", "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"File type not allowed: {content_type}")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 20MB)")

    key = upload_file(data, file.filename or "file", content_type)
    url = get_file_url(key)

    return {"key": key, "url": url, "filename": file.filename, "size": len(data)}
