"""Google OAuth2 — per-user authorization for Calendar/Gmail scopes."""
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.models.system import GoogleOAuthToken

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

TOKEN_URL = "https://oauth2.googleapis.com/token"


def build_auth_url(user_id: str, redirect_uri: str) -> str:
    """Build Google OAuth2 authorization URL for consent flow."""
    from urllib.parse import urlencode
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": user_id,
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def exchange_code(
    code: str, redirect_uri: str
) -> dict:
    """Exchange authorization code for tokens."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        if resp.status_code != 200:
            logger.error(f"Google token exchange failed: {resp.text}")
            return {}
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Refresh an expired access token."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(TOKEN_URL, data={
            "refresh_token": refresh_token,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
        })
        if resp.status_code != 200:
            logger.error(f"Google token refresh failed: {resp.text}")
            return {}
        return resp.json()


async def get_valid_token(user_id: str, db: AsyncSession) -> str | None:
    """Get a valid Google access token for the user, refreshing if needed."""
    from datetime import datetime, timedelta
    from uuid import UUID

    token_row = (await db.execute(
        select(GoogleOAuthToken).where(GoogleOAuthToken.user_id == UUID(user_id))
    )).scalar_one_or_none()

    if not token_row:
        return None

    # Check if token is still valid (with 5min buffer)
    if token_row.expires_at and token_row.expires_at > datetime.utcnow() + timedelta(minutes=5):
        return token_row.access_token

    # Refresh
    if not token_row.refresh_token:
        return None

    data = await refresh_access_token(token_row.refresh_token)
    if not data.get("access_token"):
        return None

    token_row.access_token = data["access_token"]
    token_row.expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
    await db.commit()
    return token_row.access_token
