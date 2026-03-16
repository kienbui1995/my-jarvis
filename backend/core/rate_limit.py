"""Rate limiting — split read/write, Redis sliding window."""
import time

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config import settings

# Read (GET) = cheap, high limit. Write (POST/PUT/DELETE) = expensive, stricter.
TIER_LIMITS = {
    "free":     {"read_rpm": 120, "write_rpm": 30, "daily_write": 100},
    "pro":      {"read_rpm": 300, "write_rpm": 60, "daily_write": 1000},
    "pro_plus": {"read_rpm": 600, "write_rpm": 120, "daily_write": -1},
}

WS_LIMITS = {"free": 20, "pro": 60, "pro_plus": 120}

SKIP_PATHS = ("/health", "/health/ready", "/docs", "/openapi.json")
SKIP_PREFIXES = ("/api/v1/auth/", "/api/v1/webhooks/")

# Stricter per-endpoint RPM limits for expensive operations
ENDPOINT_LIMITS = {
    "/api/v1/voice/transcribe": 5,
    "/api/v1/voice/speak": 10,
    "/api/v1/files/upload": 10,
    "/api/public/v1/chat": 10,
    "/api/public/v1/tools": 30,
    "/api/v1/chat": 20,
}


async def _check_rate(redis, key: str, limit: int, window: int = 60) -> bool:
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
        if path in SKIP_PATHS or request.method == "OPTIONS" or any(path.startswith(p) for p in SKIP_PREFIXES):
            return await call_next(request)

        redis = request.app.state.redis
        user_id, tier = _extract_user(request)
        identity = user_id or request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        is_write = request.method in ("POST", "PUT", "DELETE", "PATCH")

        # Per-endpoint stricter limits for expensive operations
        endpoint_limit = ENDPOINT_LIMITS.get(path)
        if endpoint_limit and not await _check_rate(
            redis, f"rate:ep:{path}:{identity}", endpoint_limit
        ):
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        # Read vs write RPM
        rpm_key = f"rate:{'w' if is_write else 'r'}:{identity}"
        rpm_limit = limits["write_rpm"] if is_write else limits["read_rpm"]
        if not await _check_rate(redis, rpm_key, rpm_limit):
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        # Daily limit only for writes (expensive operations)
        if is_write and not await _check_rate(redis, f"rate:daily_w:{identity}", limits["daily_write"], window=86400):
            return JSONResponse({"detail": "Daily limit exceeded"}, status_code=429)

        return await call_next(request)


async def check_ws_rate(redis, user_id: str, tier: str = "free") -> bool:
    limit = WS_LIMITS.get(tier, 20)
    return await _check_rate(redis, f"rate:ws:{user_id}", limit)
