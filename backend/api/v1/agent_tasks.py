"""Agent tasks API — create, list, get, cancel long-running tasks."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.deps import get_current_user_id
from services.agent_tasks import _get_task, cancel_task, create_task, list_tasks

router = APIRouter()


class AgentTaskCreate(BaseModel):
    prompt: str
    max_duration_minutes: int = 30


@router.post("/")
async def create(
    body: AgentTaskCreate,
    user_id: str = Depends(get_current_user_id),
):
    if not body.prompt.strip():
        raise HTTPException(400, "Empty prompt")
    task = await create_task(user_id, body.prompt, body.max_duration_minutes)
    return task


@router.get("/")
async def list_all(user_id: str = Depends(get_current_user_id)):
    return list_tasks(user_id)


@router.get("/{task_id}")
async def get_one(task_id: str, user_id: str = Depends(get_current_user_id)):
    task = _get_task(task_id)
    if not task or task["user_id"] != user_id:
        raise HTTPException(404, "Task not found")
    return {k: v for k, v in task.items() if k != "asyncio_task"}


@router.delete("/{task_id}")
async def cancel(task_id: str, user_id: str = Depends(get_current_user_id)):
    ok = await cancel_task(task_id, user_id)
    if not ok:
        raise HTTPException(404, "Task not found")
    return {"ok": True}
