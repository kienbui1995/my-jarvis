from datetime import datetime, timedelta, timezone
import secrets

import bcrypt
from jose import jwt

from core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode()[:72], hashed.encode())


def create_access_token(sub: str, tier: str = "free") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": sub, "exp": expire, "tier": tier}, settings.SECRET_KEY, settings.JWT_ALGORITHM)


def create_refresh_token(sub: str) -> str:
    jti = secrets.token_hex(16)
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": sub, "exp": expire, "type": "refresh", "jti": jti}, settings.SECRET_KEY, settings.JWT_ALGORITHM
    )
