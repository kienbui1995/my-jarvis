"""M44 Export & Portability — full data export."""
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    CalendarEvent,
    Conversation,
    Expense,
    Memory,
    Message,
    Task,
    User,
)
from db.models.preference import UserPreference


async def export_user_data(user_id: str, db: AsyncSession) -> dict:
    """Export all user data as JSON-serializable dict."""
    uid = UUID(user_id)
    user = await db.get(User, uid)
    if not user:
        return {"error": "User not found"}

    # Tasks
    tasks = (await db.execute(
        select(Task).where(Task.user_id == uid)
    )).scalars().all()

    # Calendar
    events = (await db.execute(
        select(CalendarEvent).where(CalendarEvent.user_id == uid)
    )).scalars().all()

    # Expenses
    expenses = (await db.execute(
        select(Expense).where(Expense.user_id == uid)
    )).scalars().all()

    # Memories
    memories = (await db.execute(
        select(Memory).where(Memory.user_id == uid)
    )).scalars().all()

    # Conversations + messages
    convos = (await db.execute(
        select(Conversation).where(Conversation.user_id == uid)
    )).scalars().all()

    conversations = []
    for c in convos:
        msgs = (await db.execute(
            select(Message).where(Message.conversation_id == c.id)
            .order_by(Message.created_at)
        )).scalars().all()
        conversations.append({
            "id": str(c.id),
            "channel": c.channel,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "messages": [
                {"role": m.role, "content": m.content,
                 "created_at": m.created_at.isoformat() if m.created_at else None}
                for m in msgs
            ],
        })

    # Preferences
    pref = (await db.execute(
        select(UserPreference).where(UserPreference.user_id == uid)
    )).scalar_one_or_none()

    return {
        "user": {
            "id": str(user.id), "name": user.name, "email": user.email,
            "timezone": user.timezone, "tier": user.tier,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "tasks": [
            {"title": t.title, "status": t.status, "priority": t.priority,
             "due_date": t.due_date.isoformat() if t.due_date else None}
            for t in tasks
        ],
        "calendar": [
            {"title": e.title,
             "start": e.start_time.isoformat() if e.start_time else None,
             "location": e.location}
            for e in events
        ],
        "expenses": [
            {"amount": e.amount, "category": e.category,
             "description": e.description,
             "date": e.created_at.isoformat() if e.created_at else None}
            for e in expenses
        ],
        "memories": [
            {"type": m.memory_type, "content": m.content}
            for m in memories
        ],
        "conversations": conversations,
        "preferences": {
            "tone": pref.tone if pref else None,
            "verbosity": pref.verbosity if pref else None,
            "interests": pref.interests if pref else None,
        },
        "exported_at": json.loads(json.dumps(
            {"ts": __import__("datetime").datetime.utcnow().isoformat()}
        ))["ts"],
    }
