import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

import core.redis as redis_pool
from core.config import settings
from core.headers import SecurityHeadersMiddleware
from core.rate_limit import RateLimitMiddleware
from api.v1 import webhooks, auth, users, tasks, calendar, analytics, ws, mcp, notifications, conversations
from api.v1 import settings as settings_api
from api.v1 import audit
from api.v1 import preferences
from api.v1 import feedback
from api.v1 import voice
from api.v1 import triggers

from importlib.metadata import version as pkg_version

import sentry_sdk

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


@app.get("/health")
async def health():
    return {"status": "ok", "version": APP_VERSION}
