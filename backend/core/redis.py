"""Single shared Redis connection pool."""
import redis.asyncio as aioredis
from core.config import settings

pool: aioredis.Redis | None = None


async def init() -> aioredis.Redis:
    global pool
    pool = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await pool.ping()
    return pool


async def close():
    global pool
    if pool:
        await pool.close()
        pool = None


def get() -> aioredis.Redis:
    """Get the shared Redis instance. Auto-inits if not yet initialized (for workers)."""
    global pool
    if pool is None:
        pool = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return pool
