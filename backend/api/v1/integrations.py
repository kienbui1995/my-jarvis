"""V10: Integrations management — connect/disconnect external services."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.deps import get_current_user_id, get_db
from db.models import UserPreference
from mcp.registry import get_registry

router = APIRouter()

INTEGRATION_KEYS = ["spotify_token", "notion_key", "github_token", "home_assistant_url", "home_assistant_token"]


@router.get("/")
async def list_integrations(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """List all available integrations and their connection status."""
    uid = UUID(user_id)
    prefs = (await db.execute(
        select(UserPreference).where(UserPreference.user_id == uid, UserPreference.key.in_(INTEGRATION_KEYS))
    )).scalars().all()
    connected = {p.key for p in prefs}

    mcp_servers = get_registry()
    return {
        "mcp_servers": mcp_servers,
        "integrations": [
            {"id": "spotify", "name": "Spotify", "connected": "spotify_token" in connected},
            {"id": "notion", "name": "Notion", "connected": "notion_key" in connected},
            {"id": "github", "name": "GitHub", "connected": "github_token" in connected},
            {"id": "home_assistant", "name": "Home Assistant", "connected": "home_assistant_url" in connected},
        ],
    }


class ConnectRequest(BaseModel):
    integration_id: str
    token: str


@router.post("/connect")
async def connect_integration(body: ConnectRequest, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    key = f"{body.integration_id}_token" if body.integration_id != "home_assistant" else "home_assistant_token"

    existing = (await db.execute(
        select(UserPreference).where(UserPreference.user_id == uid, UserPreference.key == key)
    )).scalar_one_or_none()

    if existing:
        existing.value = body.token
    else:
        db.add(UserPreference(user_id=uid, key=key, value=body.token))
    await db.commit()
    return {"ok": True, "integration": body.integration_id}


@router.post("/disconnect/{integration_id}")
async def disconnect_integration(integration_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    key = f"{integration_id}_token" if integration_id != "home_assistant" else "home_assistant_token"
    pref = (await db.execute(
        select(UserPreference).where(UserPreference.user_id == uid, UserPreference.key == key)
    )).scalar_one_or_none()
    if pref:
        await db.delete(pref)
        await db.commit()
    return {"ok": True}
