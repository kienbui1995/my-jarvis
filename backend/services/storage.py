"""MinIO object storage — file upload/download."""
import logging
import uuid
from io import BytesIO

from minio import Minio

from core.config import settings

logger = logging.getLogger(__name__)

_client: Minio | None = None


def get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        if not _client.bucket_exists(settings.MINIO_BUCKET):
            _client.make_bucket(settings.MINIO_BUCKET)
    return _client


def upload_file(
    data: bytes, filename: str, content_type: str = "application/octet-stream",
) -> str:
    """Upload file to MinIO. Returns the object key."""
    client = get_client()
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    key = f"uploads/{uuid.uuid4().hex[:12]}.{ext}" if ext else f"uploads/{uuid.uuid4().hex[:12]}"
    client.put_object(
        settings.MINIO_BUCKET, key, BytesIO(data), len(data),
        content_type=content_type,
    )
    return key


def get_file_url(key: str) -> str:
    """Get presigned URL for a file (7 day expiry)."""
    from datetime import timedelta
    client = get_client()
    return client.presigned_get_object(settings.MINIO_BUCKET, key, expires=timedelta(days=7))


def get_file_bytes(key: str) -> bytes:
    """Download file bytes from MinIO."""
    client = get_client()
    resp = client.get_object(settings.MINIO_BUCKET, key)
    try:
        return resp.read()
    finally:
        resp.close()
        resp.release_conn()
