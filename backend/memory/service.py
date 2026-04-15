"""Memory service — dual-layer (hot + cold) memory management."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Memory, User, Task, CalendarEvent

import core.redis as redis_pool


# ── Hot Path (always in prompt) ──────────────────────────────

async def load_hot_memory(user_id: str, db: AsyncSession) -> str:
    """Load hot memory: user profile summary + active tasks + today's calendar.
    Target: ~500 tokens.
    """
    r = redis_pool.get()
    cache_key = f"hot_mem:{user_id}"
    cached = await r.get(cache_key)
    if cached:
        return cached

    uid = UUID(user_id)

    # User profile
    user = await db.get(User, uid)
    profile = f"Tên: {user.name or 'Chưa đặt'}, Tier: {user.tier}" if user else ""

    # Active tasks (top 5)
    tasks_q = await db.execute(
        select(Task).where(Task.user_id == uid, Task.status != "done").order_by(Task.due_date).limit(5)
    )
    tasks = tasks_q.scalars().all()
    tasks_str = "\n".join(f"- [{t.priority}] {t.title}" + (f" (hạn: {t.due_date.strftime('%d/%m')})" if t.due_date else "") for t in tasks)

    # Today's events
    today = datetime.utcnow().date()
    events_q = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.user_id == uid,
            CalendarEvent.start_time >= datetime.combine(today, datetime.min.time()),
            CalendarEvent.start_time < datetime.combine(today, datetime.max.time()),
        )
    )
    events = events_q.scalars().all()
    events_str = "\n".join(f"- {e.start_time.strftime('%H:%M')} {e.title}" for e in events)

    hot = f"""[User] {profile}
[Tasks] {tasks_str or 'Không có task'}
[Lịch hôm nay] {events_str or 'Trống'}"""

    await r.setex(cache_key, 300, hot)  # cache 5 min
    return hot


# ── Cold Path (on-demand vector retrieval) ───────────────────

async def search_cold_memory(user_id: str, query_embedding: list[float], db: AsyncSession, limit: int = 5) -> list[dict]:
    """Search cold memory via pgvector semantic similarity."""
    uid = UUID(user_id)
    results = await db.execute(
        select(Memory)
        .where(Memory.user_id == uid)
        .order_by(Memory.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    memories = results.scalars().all()

    # Update last_accessed + access_count
    for m in memories:
        await db.execute(
            update(Memory).where(Memory.id == m.id)
            .values(last_accessed=datetime.utcnow(), access_count=Memory.access_count + 1)
        )
    await db.commit()

    return [{"type": m.memory_type, "content": m.content, "importance": m.importance} for m in memories]


async def save_memory(user_id: str, content: str, memory_type: str, embedding: list[float], db: AsyncSession, importance: float = 0.5) -> None:
    """Save a new memory entry."""
    mem = Memory(
        user_id=UUID(user_id),
        memory_type=memory_type,
        content=content,
        embedding=embedding,
        importance=importance,
    )
    db.add(mem)
    await db.commit()
