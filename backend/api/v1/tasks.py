"""Task CRUD endpoints for web dashboard."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy import update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models import Task
from services.event_bus import emit

router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: str | None = None


@router.get("/")
async def list_tasks(status: str = "all", user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    q = select(Task).where(Task.user_id == UUID(user_id))
    if status != "all":
        q = q.where(Task.status == status)
    result = await db.execute(q.order_by(Task.created_at.desc()).limit(50))
    return [{"id": str(t.id), "title": t.title, "status": t.status, "priority": t.priority, "due_date": str(t.due_date) if t.due_date else None} for t in result.scalars()]


@router.post("/")
async def create_task(req: TaskCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    task = Task(user_id=UUID(user_id), title=req.title, description=req.description, priority=req.priority)
    db.add(task)
    await db.commit()
    await emit("task.created", user_id, {"task_id": str(task.id), "title": task.title})
    return {"id": str(task.id), "title": task.title}


class TaskUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: str | None = None


@router.patch("/{task_id}")
async def update_task(task_id: str, body: TaskUpdate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(sql_update(Task).where(Task.id == UUID(task_id), Task.user_id == UUID(user_id)).values(**body.model_dump(exclude_none=True)).returning(Task.id))
    if not result.first():
        raise HTTPException(404, "Task not found")
    await db.commit()
    await emit("task.updated", user_id, {"task_id": task_id})
    return {"ok": True}


@router.delete("/{task_id}")
async def delete_task(task_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await db.execute(sql_delete(Task).where(Task.id == UUID(task_id), Task.user_id == UUID(user_id)))
    await db.commit()
    return {"ok": True}
