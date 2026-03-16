import logging
from contextlib import asynccontextmanager
from importlib.metadata import version as pkg_version

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

import core.redis as redis_pool
from api.v1 import (
    agent_tasks,
    analytics,
    audit,
    auth,
    billing,
    calendar,
    chat,
    conversations,
    feedback,
    files,
    google_connect,
    marketplace,
    mcp,
    notifications,
    preferences,
    tasks,
    triggers,
    users,
    voice,
    webhooks,
    ws,
)
from api.v1 import settings as settings_api
from core.config import settings
from core.headers import SecurityHeadersMiddleware
from core.rate_limit import RateLimitMiddleware

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)

APP_VERSION = pkg_version("my-jarvis-backend")

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.2,
        environment=settings.APP_ENV,
        release=f"my-jarvis-backend@{APP_VERSION}",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MY JARVIS backend...")

    app.state.redis = await redis_pool.init()
    logger.info("Redis connected")

    from db.session import engine
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    logger.info("PostgreSQL + pgvector ready")

    yield

    await redis_pool.close()
    from db.session import engine as eng
    await eng.dispose()
    logger.info("MY JARVIS backend stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

# --- Middleware ---
app.state._debug = settings.DEBUG
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [f"https://{settings.DOMAIN}"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=not settings.DEBUG,
    max_age=600,
)
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)


@app.middleware("http")
async def add_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-App-Version"] = APP_VERSION
    return response

# --- Routes ---
_v1 = "/api/v1"
app.include_router(webhooks.router, prefix=f"{_v1}/webhooks", tags=["webhooks"])
app.include_router(auth.router, prefix=f"{_v1}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{_v1}/users", tags=["users"])
app.include_router(tasks.router, prefix=f"{_v1}/tasks", tags=["tasks"])
app.include_router(calendar.router, prefix=f"{_v1}/calendar", tags=["calendar"])
app.include_router(analytics.router, prefix=f"{_v1}/analytics", tags=["analytics"])
app.include_router(ws.router, prefix=_v1, tags=["websocket"])
app.include_router(mcp.router, prefix=f"{_v1}/mcp", tags=["mcp"])
app.include_router(notifications.router, prefix=_v1, tags=["notifications"])
app.include_router(conversations.router, prefix=f"{_v1}/conversations", tags=["conversations"])
app.include_router(settings_api.router, prefix=f"{_v1}/settings", tags=["settings"])
app.include_router(audit.router, prefix=f"{_v1}/audit", tags=["audit"])
app.include_router(preferences.router, prefix=f"{_v1}/settings", tags=["preferences"])
app.include_router(feedback.router, prefix=_v1, tags=["feedback"])
app.include_router(voice.router, prefix=f"{_v1}/voice", tags=["voice"])
app.include_router(triggers.router, prefix=f"{_v1}/triggers", tags=["triggers"])
app.include_router(google_connect.router, prefix=f"{_v1}/google", tags=["google"])
app.include_router(chat.router, prefix=_v1, tags=["chat"])
app.include_router(files.router, prefix=f"{_v1}/files", tags=["files"])
app.include_router(billing.router, prefix=f"{_v1}/billing", tags=["billing"])
app.include_router(agent_tasks.router, prefix=f"{_v1}/agent-tasks", tags=["agent-tasks"])
app.include_router(marketplace.router, prefix=f"{_v1}/marketplace", tags=["marketplace"])

# Public API (developer access via API keys)
from api.public.routes import router as public_router

app.include_router(public_router, prefix="/api/public/v1", tags=["public-api"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": APP_VERSION}


@app.get("/health/ready")
async def health_ready():
    """Deep health check — verify all dependencies are reachable."""
    checks = {}
    # PostgreSQL
    try:
        from db.session import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"
    # Redis
    try:
        r = redis_pool.get()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
    # MinIO
    try:
        from services.storage import get_client
        client = get_client()
        client.bucket_exists(settings.MINIO_BUCKET)
        checks["minio"] = "ok"
    except Exception as e:
        checks["minio"] = f"error: {e}"
    # LiteLLM
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{settings.LITELLM_BASE_URL.rstrip('/v1')}/health")
            checks["litellm"] = "ok" if r.status_code == 200 else f"http {r.status_code}"
    except Exception as e:
        checks["litellm"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ready" if all_ok else "degraded", "version": APP_VERSION, "checks": checks}
