"""Per-user budget tracking via Redis."""
from datetime import date

import core.redis as redis_pool


def _budget_key(user_id: str) -> str:
    return f"budget:{user_id}:{date.today().isoformat()}"


async def get_redis():
    """Backward-compat alias used by users.py link code."""
    return redis_pool.get()


async def get_remaining_budget(user_id: str, tier: str = "free") -> float:
    from core.config import settings
    limits = {
        "free": settings.LLM_DAILY_BUDGET_FREE,
        "pro": settings.LLM_DAILY_BUDGET_PRO,
        "pro_plus": settings.LLM_DAILY_BUDGET_PRO_PLUS,
    }
    daily_limit = limits.get(tier, limits["free"])
    r = redis_pool.get()
    spent = await r.get(_budget_key(user_id))
    return daily_limit - float(spent or 0)


async def record_spend(user_id: str, cost: float) -> None:
    r = redis_pool.get()
    key = _budget_key(user_id)
    await r.incrbyfloat(key, cost)
    await r.expire(key, 86400 * 2)
