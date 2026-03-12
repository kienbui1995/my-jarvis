"""Rate limiting — Redis sliding window counter per user."""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from jose import jwt, JWTError
from core.config import settings

TIER_LIMITS = {
    "free": {"rpm": 30, "daily": 50},
    "pro": {"rpm": 120, "daily": 500},
    "pro_plus": {"rpm": 300, "daily": -1},
}

WS_LIMITS = {"free": 20, "pro": 60, "pro_plus": 120}  # messages/min


async def _check_rate(redis, key: str, limit: int, window: int = 60) -> bool:
    """Sliding window counter. Returns True if allowed."""
    if limit < 0:
        return True
    now = int(time.time())
    window_key = f"{key}:{now // window}"
    pipe = redis.pipeline()
    pipe.incr(window_key)
    pipe.expire(window_key, window + 1)
    count, _ = await pipe.execute()
    return count <= limit


def _extract_user(request: Request) -> tuple[str, str]:
    """Extract user_id and tier from JWT in Authorization header."""
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return "", "free"
    try:
        payload = jwt.decode(auth[7:], settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub", ""), payload.get("tier", "free")
    except JWTError:
        return "", "free"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in ("/health", "/docs", "/openapi.json") or request.method == "OPTIONS" or path.startswith(("/api/v1/auth/", "/api/v1/webhooks/", "/api/v1/notifications")):
            return await call_next(request)

        redis = request.app.state.redis
        user_id, tier = _extract_user(request)
        identity = user_id or request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        if not await _check_rate(redis, f"rate:rpm:{identity}", limits["rpm"]):
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        if not await _check_rate(redis, f"rate:daily:{identity}", limits["daily"], window=86400):
            return JSONResponse({"detail": "Daily limit exceeded"}, status_code=429)

        return await call_next(request)


async def check_ws_rate(redis, user_id: str, tier: str = "free") -> bool:
    """Check WebSocket message rate. Returns True if allowed."""
    limit = WS_LIMITS.get(tier, 20)
    return await _check_rate(redis, f"rate:ws:{user_id}", limit)
