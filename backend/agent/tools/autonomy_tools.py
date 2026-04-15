"""V12: Autonomy tools — goals, decisions, weekly digest, digital twin, scheduling."""
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedToolArg


@tool
async def update_goal_progress(goal_title: str, value: float, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Cập nhật tiến độ goal/OKR. Args: goal_title, value (giá trị mới)."""
    from db.session import async_session
    from db.models import Goal
    from sqlalchemy import select
    from uuid import UUID

    async with async_session() as db:
        goal = (await db.execute(
            select(Goal).where(Goal.user_id == UUID(user_id), Goal.title.ilike(f"%{goal_title}%"), Goal.status == "active")
        )).scalar_one_or_none()
        if not goal:
            return f"Không tìm thấy goal '{goal_title}'."
        goal.current_value = value
        if goal.target_value and value >= goal.target_value:
            goal.status = "completed"
        await db.commit()

    pct = f" ({value/goal.target_value*100:.0f}%)" if goal.target_value else ""
    status = " 🎉 HOÀN THÀNH!" if goal.status == "completed" else ""
    return f"✅ {goal.title}: {value}{f'/{goal.target_value}' if goal.target_value else ''}{pct}{status}"


@tool
async def log_decision(title: str, context: str, options: str, chosen: str, reasoning: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Ghi nhật ký quyết định. Args: title, context, options (comma-separated), chosen, reasoning."""
    from db.session import async_session
    from db.models import Decision
    from datetime import date, timedelta
    from uuid import UUID

    opts = [{"option": o.strip()} for o in options.split(",")]
    async with async_session() as db:
        db.add(Decision(
            user_id=UUID(user_id), title=title, context=context,
            options=opts, chosen=chosen, reasoning=reasoning,
            review_date=date.today() + timedelta(days=30),
        ))
        await db.commit()
    return f"📝 Đã ghi quyết định: {title}. Review sau 30 ngày."


@tool
async def generate_weekly_digest(user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Tạo báo cáo tuần tổng hợp: tasks, chi tiêu, sức khỏe, goals."""
    from db.session import async_session
    from services.context_engine import get_user_context
    from agent.reasoning.cross_domain import cross_domain_insights
    from services.pattern_detector import detect_patterns

    async with async_session() as db:
        ctx = await get_user_context(user_id, db)
        insights = await cross_domain_insights(user_id, db)
        patterns = await detect_patterns(user_id, db)

    sections = ["📋 **Weekly Digest**\n"]
    if insights:
        sections.append("**Insights:**\n" + "\n".join(f"  {i}" for i in insights))
    if patterns:
        sections.append("**Alerts:**\n" + "\n".join(f"  {p}" for p in patterns))
    if not insights and not patterns:
        sections.append("Tuần này chưa có đủ dữ liệu để phân tích.")
    return "\n\n".join(sections)


@tool
async def digital_twin_respond(message: str, sender: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Digital twin — đại diện user trả lời email/tin nhắn routine. Args: message, sender."""
    from llm.gateway import get_llm
    from services.context_engine import get_user_context
    from db.session import async_session

    async with async_session() as db:
        ctx = await get_user_context(user_id, db)

    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(
        f"Bạn là digital twin của user. Context hiện tại: {ctx}\n\n"
        f"Tin nhắn từ {sender}:\n{message}\n\n"
        "Soạn reply ngắn gọn, lịch sự, đúng phong cách người Việt. "
        "Nếu cần quyết định quan trọng, nói 'Để tôi hỏi lại [user] nhé'."
    )
    return f"✉️ Draft reply cho {sender}:\n\n{resp.content}"


@tool
async def suggest_schedule(task_description: str, duration_minutes: int = 60, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Gợi ý thời gian tốt nhất để làm task dựa trên calendar + patterns. Args: task_description, duration_minutes."""
    from db.session import async_session
    from db.models import CalendarEvent
    from sqlalchemy import select
    from datetime import datetime, timedelta
    from uuid import UUID

    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    async with async_session() as db:
        events = (await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.user_id == UUID(user_id),
                CalendarEvent.start_time.between(now, tomorrow),
            ).order_by(CalendarEvent.start_time)
        )).scalars().all()

    # Find gaps
    busy = [(e.start_time, e.end_time) for e in events]
    slots = []
    cursor = now.replace(minute=0, second=0) + timedelta(hours=1)
    while cursor < tomorrow:
        end = cursor + timedelta(minutes=duration_minutes)
        conflict = any(s < end and e > cursor for s, e in busy)
        if not conflict and 8 <= cursor.hour <= 21:
            slots.append(cursor)
        cursor += timedelta(hours=1)
        if len(slots) >= 3:
            break

    if not slots:
        return "Không tìm được slot trống trong 24h tới."
    return f"📅 Gợi ý thời gian cho '{task_description}' ({duration_minutes}p):\n" + "\n".join(
        f"  • {s.strftime('%H:%M %d/%m')}" for s in slots
    )
