"""Public API auth — API key validation."""
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_db
from db.models.system import APIKey

_header = APIKeyHeader(name="X-API-Key")


async def get_api_key_user(
    key: str = Security(_header),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Validate API key and return user_id."""
    row = (await db.execute(
        select(APIKey).where(APIKey.key == key, APIKey.active.is_(True))
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(401, "Invalid API key")

    # Increment usage counter
    row.request_count = (row.request_count or 0) + 1
    await db.commit()
    return str(row.user_id)
