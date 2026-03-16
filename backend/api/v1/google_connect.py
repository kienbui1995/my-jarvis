"""Google OAuth2 connection endpoints — link Google Calendar/Gmail."""
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.deps import get_current_user_id, get_db
from db.models import GoogleOAuthToken
from services.google_oauth import build_auth_url, exchange_code

router = APIRouter()


@router.get("/auth-url")
async def get_google_auth_url(
    request: Request,
    user_id: str = Depends(get_current_user_id),
):
    """Get Google OAuth2 authorization URL for the current user."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(501, "Google OAuth not configured")
    redirect_uri = str(request.base_url).rstrip("/") + "/api/v1/google/callback"
    url = build_auth_url(user_id, redirect_uri)
    return {"url": url}


@router.get("/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(""),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth2 callback — exchange code for tokens."""
    if not state:
        raise HTTPException(400, "Missing state (user_id)")

    redirect_uri = str(request.base_url).rstrip("/") + "/api/v1/google/callback"
    tokens = await exchange_code(code, redirect_uri)
    if not tokens.get("access_token"):
        raise HTTPException(400, "Failed to exchange authorization code")

    user_id = UUID(state)
    # Upsert token
    existing = (await db.execute(
        select(GoogleOAuthToken).where(GoogleOAuthToken.user_id == user_id)
    )).scalar_one_or_none()

    expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))

    if existing:
        existing.access_token = tokens["access_token"]
        existing.refresh_token = tokens.get("refresh_token", existing.refresh_token)
        existing.scopes = tokens.get("scope", "")
        existing.expires_at = expires_at
    else:
        db.add(GoogleOAuthToken(
            user_id=user_id,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            scopes=tokens.get("scope", ""),
            expires_at=expires_at,
        ))
    await db.commit()

    return {"status": "connected", "message": "Google account linked successfully"}


@router.get("/status")
async def google_status(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Check if user has linked Google account."""
    token = (await db.execute(
        select(GoogleOAuthToken).where(GoogleOAuthToken.user_id == UUID(user_id))
    )).scalar_one_or_none()
    return {
        "connected": token is not None,
        "scopes": token.scopes if token else None,
    }


@router.delete("/disconnect")
async def google_disconnect(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Google account."""
    from sqlalchemy import delete
    await db.execute(
        delete(GoogleOAuthToken).where(GoogleOAuthToken.user_id == UUID(user_id))
    )
    await db.commit()
    return {"ok": True}
