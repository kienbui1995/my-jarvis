"""Long-running agent tasks — background execution with progress tracking."""
import asyncio
import logging
import time
from uuid import UUID, uuid4

from langchain_core.messages import HumanMessage

from db.models import Notification
from db.session import async_session
from services.event_bus import emit

logger = logging.getLogger(__name__)

# In-memory task registry (per-worker process)
_tasks: dict[str, dict] = {}
MAX_DURATION_S = 1800  # 30 minutes


def _get_task(task_id: str) -> dict | None:
    return _tasks.get(task_id)


def list_tasks(user_id: str) -> list[dict]:
    return [
        {k: v for k, v in t.items() if k != "asyncio_task"}
        for t in _tasks.values()
        if t["user_id"] == user_id
    ]


async def create_task(
    user_id: str, prompt: str, max_duration_minutes: int = 30,
) -> dict:
    """Create and start a long-running agent task."""
    task_id = uuid4().hex[:12]
    max_dur = min(max_duration_minutes * 60, MAX_DURATION_S)

    task_info = {
        "id": task_id,
        "user_id": user_id,
        "prompt": prompt,
        "status": "running",
        "progress": [],
        "result": "",
        "created_at": time.time(),
        "max_duration_s": max_dur,
    }
    _tasks[task_id] = task_info

    # Start background execution
    asyncio_task = asyncio.create_task(_execute_task(task_id))
    _tasks[task_id]["asyncio_task"] = asyncio_task
    return {k: v for k, v in task_info.items() if k != "asyncio_task"}


async def cancel_task(task_id: str, user_id: str) -> bool:
    task = _tasks.get(task_id)
    if not task or task["user_id"] != user_id:
        return False
    at = task.get("asyncio_task")
    if at and not at.done():
        at.cancel()
    task["status"] = "cancelled"
    return True


async def _execute_task(task_id: str) -> None:
    """Run agent graph for the task prompt, with timeout."""
    task = _tasks.get(task_id)
    if not task:
        return

    user_id = task["user_id"]
    prompt = task["prompt"]
    max_dur = task["max_duration_s"]

    try:
        from agent.graph import get_jarvis_graph
        graph = await get_jarvis_graph()
        config = {"configurable": {"thread_id": f"agent-task-{task_id}"}}

        task["progress"].append("Bắt đầu xử lý...")

        result = await asyncio.wait_for(
            graph.ainvoke({
                "messages": [HumanMessage(content=prompt)],
                "user_id": user_id,
                "user_tier": "pro",
                "channel": "background",
                "conversation_id": "",
            }, config=config),
            timeout=max_dur,
        )

        response = result.get("final_response", "Không có kết quả.")
        task["result"] = response
        task["status"] = "completed"
        task["progress"].append("Hoàn thành!")

        # Notify user
        async with async_session() as db:
            db.add(Notification(
                user_id=UUID(user_id), type="agent_task",
                content=f"📋 Task hoàn thành: {prompt[:50]}...\n\n{response[:500]}",
            ))
            await db.commit()
        await emit("agent_task.completed", user_id, {"task_id": task_id})

    except asyncio.TimeoutError:
        task["status"] = "timeout"
        task["progress"].append(f"Quá thời gian ({max_dur // 60} phút)")
    except asyncio.CancelledError:
        task["status"] = "cancelled"
    except Exception as e:
        task["status"] = "error"
        task["progress"].append(f"Lỗi: {e}")
        logger.exception(f"Agent task {task_id} failed")
