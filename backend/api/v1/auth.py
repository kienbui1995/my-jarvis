"""Auth endpoints — register, login, Google OAuth, refresh."""
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.deps import get_db
from core.security import hash_password, verify_password, create_access_token, create_refresh_token
from db.models import User, ProactiveTrigger

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    credential: str  # Google ID token from GSI


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


async def _ensure_proactive_trigger(db: AsyncSession, user_id):
    db.add(ProactiveTrigger(user_id=user_id, trigger_type="morning_briefing", schedule="0 8 * * *", enabled=True))


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=req.email, hashed_password=hash_password(req.password), name=req.name)
    db.add(user)
    await db.flush()
    await _ensure_proactive_trigger(db, user.id)
    await db.commit()
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.tier),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.tier),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/google", response_model=TokenResponse)
async def google_auth(req: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Verify Google ID token → find or create user → return JWT."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google login not configured")

    # Verify token with Google
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}")
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    info = r.json()
    if info.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Token audience mismatch")

    email = info.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="No email in Google token")

    # Find or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email=email, name=info.get("name", ""))
        db.add(user)
        await db.flush()
        await _ensure_proactive_trigger(db, user.id)
        await db.commit()
        await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for new access + refresh tokens (one-time use)."""
    from jose import jwt as jose_jwt, JWTError
    import core.redis as redis_pool

    try:
        payload = jose_jwt.decode(req.refresh_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
        user_id = payload.get("sub")
        jti = payload.get("jti", "")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check if token was already used (rotation)
    if jti:
        redis = redis_pool.get()
        used_key = f"rt:used:{jti}"
        if await redis.get(used_key):
            raise HTTPException(status_code=401, detail="Refresh token already used")
        await redis.set(used_key, "1", ex=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    from uuid import UUID
    try:
        uid = UUID(user_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid user ID")
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.tier),
        refresh_token=create_refresh_token(str(user.id)),
    )


# --- Zalo Mini App auth ---

class ZaloMiniAppAuthRequest(BaseModel):
    code: str  # ZMP access token from getAccessToken()


@router.post("/zalo-miniapp", response_model=TokenResponse)
async def zalo_miniapp_auth(
    req: ZaloMiniAppAuthRequest, db: AsyncSession = Depends(get_db),
):
    """Exchange Zalo Mini App access token for JWT."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://graph.zalo.me/v2.0/me",
            params={"fields": "id,name,picture"},
            headers={"access_token": req.code},
        )
    if r.status_code != 200:
        raise HTTPException(401, "Invalid Zalo token")

    info = r.json()
    zalo_id = info.get("id", "")
    if not zalo_id:
        raise HTTPException(401, "No Zalo user ID")

    name = info.get("name", "")

    result = await db.execute(select(User).where(User.zalo_id == zalo_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(zalo_id=zalo_id, name=name)
        db.add(user)
        await db.flush()
        await _ensure_proactive_trigger(db, user.id)
        await db.commit()
        await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.tier),
        refresh_token=create_refresh_token(str(user.id)),
    )
