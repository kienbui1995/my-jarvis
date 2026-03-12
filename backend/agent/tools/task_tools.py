"""Task management tools — wired to DB, user_id auto-injected."""
from datetime import datetime
from typing import Annotated
from uuid import UUID

from langchain_core.tools import tool, InjectedToolArg
from sqlalchemy import select

from db.models import Task
from db.session import async_session


@tool
async def task_create(
    title: str, due_date: str = "", priority: str = "medium",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Tạo task mới. Args: title, due_date (YYYY-MM-DD, optional), priority (low/medium/high/urgent)."""
    async with async_session() as db:
        t = Task(user_id=UUID(user_id), title=title, priority=priority, created_by_agent=True)
        if due_date:
            t.due_date = datetime.fromisoformat(due_date)
        db.add(t)
        await db.commit()
        return f"✅ Đã tạo task: {title} (id: {t.id})"


@tool
async def task_list(
    status: str = "todo",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Liệt kê tasks. Args: status (todo/in_progress/done/all)."""
    async with async_session() as db:
        q = select(Task).where(Task.user_id == UUID(user_id))
        if status != "all":
            q = q.where(Task.status == status)
        result = await db.execute(q.order_by(Task.due_date.asc().nullslast()).limit(10))
        tasks = result.scalars().all()
        if not tasks:
            return "📋 Không có task nào."
        lines = []
        for t in tasks:
            due = f" (hạn: {t.due_date.strftime('%d/%m')})" if t.due_date else ""
            lines.append(f"- [{t.priority}] {t.title}{due} — {t.status}")
        return "\n".join(lines)


@tool
async def task_update(task_id: str, status: str = "", title: str = "") -> str:
    """Cập nhật task. Args: task_id, status (todo/in_progress/done), title."""
    async with async_session() as db:
        t = await db.get(Task, UUID(task_id))
        if not t:
            return "❌ Không tìm thấy task."
        if status:
            t.status = status
        if title:
            t.title = title
        await db.commit()
        return f"✅ Đã cập nhật task: {t.title} → {t.status}"
