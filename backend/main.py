import logging
from contextlib import asynccontextmanager
from importlib.metadata import version as pkg_version

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

import core.redis as redis_pool
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

# --- Routes (auto-discovered) ---
def _register_routes(app: FastAPI):
    """Auto-discover and register all API v1 routers.

    Convention: each file in api/v1/ exports `router = APIRouter()`.
    Route prefix derived from filename: tasks.py → /api/v1/tasks.
    Special cases handled via ROUTE_OVERRIDES.
    """
    import importlib
    import pkgutil
    from pathlib import Path

    ROUTE_OVERRIDES = {
        "ws": {"prefix": "/api/v1", "tags": ["websocket"]},
        "webhooks": {"prefix": "/api/v1/webhooks", "tags": ["webhooks"]},
        "google_connect": {"prefix": "/api/v1/google", "tags": ["google"]},
        "settings": {"prefix": "/api/v1/settings", "tags": ["settings"]},
        "preferences": {"prefix": "/api/v1/settings", "tags": ["preferences"]},
        "chat": {"prefix": "/api/v1", "tags": ["chat"]},
        "feedback": {"prefix": "/api/v1", "tags": ["feedback"]},
        "notifications": {"prefix": "/api/v1", "tags": ["notifications"]},
        "engagement": {"prefix": "/api/v1", "tags": ["engagement"]},
        "agent_tasks": {"prefix": "/api/v1/agent-tasks", "tags": ["agent-tasks"]},
    }

    v1_dir = Path(__file__).parent / "api" / "v1"
    count = 0
    for mod_info in pkgutil.iter_modules([str(v1_dir)]):
        if mod_info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"api.v1.{mod_info.name}")
            r = getattr(mod, "router", None)
            if r is None:
                continue
            overrides = ROUTE_OVERRIDES.get(mod_info.name, {})
            prefix = overrides.get("prefix", f"/api/v1/{mod_info.name.replace('_', '-')}")
            tags = overrides.get("tags", [mod_info.name.replace("_", "-")])
            app.include_router(r, prefix=prefix, tags=tags)
            count += 1
        except Exception:
            logger.exception(f"Failed to load API module: api.v1.{mod_info.name}")

    # Public API (developer access via API keys)
    try:
        from api.public.routes import router as public_router
        app.include_router(public_router, prefix="/api/public/v1", tags=["public-api"])
        count += 1
    except Exception:
        logger.warning("Public API routes not loaded")

    logger.info(f"Registered {count} API routers")


_register_routes(app)


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
