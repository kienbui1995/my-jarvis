"""WebSocket chat endpoint — real-time streaming for web dashboard."""
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from agent.graph import get_jarvis_graph
from core.config import settings
from db.models import User
from db.session import async_session
from services.conversation import get_or_create_conversation, save_message, load_history
from memory.conversation_memory import summarize_if_needed, build_memory_context
from memory.preference_learning import build_preference_prompt
from core.rate_limit import check_ws_rate
from core.supervision import SessionSupervisor

logger = logging.getLogger(__name__)
router = APIRouter()

STREAM_NODES = {"agent_loop", "delegate", "executor", "synthesize"}


async def _authenticate_ws(ws: WebSocket) -> str | None:
    """Wait for first message with auth token instead of URL param."""
    try:
        data = await ws.receive_json()
        token = data.get("token", "")
        if not token:
            return None
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except (JWTError, Exception):
        return None


async def _run_graph(graph, input_data, config, ws):
    """Run graph with HITL interrupt handling. Returns full response text."""
    full_response = ""

    while True:
        interrupted = False
        async for event in graph.astream_events(input_data, config=config, version="v2"):
            if event.get("event") == "on_chat_model_stream":
                node = event.get("metadata", {}).get("langgraph_node", "")
                if node not in STREAM_NODES:
                    continue
                chunk = event["data"].get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                    full_response += text
                    await ws.send_json({"type": "stream", "content": text})

        # Check if graph was interrupted (M8 HITL)
        state = await graph.aget_state(config)
        if state.next:
            # Graph is paused at interrupt — get interrupt value
            tasks = state.tasks
            if tasks and hasattr(tasks[0], "interrupts") and tasks[0].interrupts:
                interrupt_data = tasks[0].interrupts[0].value
                await ws.send_json({"type": "approval_request", **interrupt_data})

                # Wait for user approval
                approval_msg = await ws.receive_json()
                approved = approval_msg.get("approved", False)

                # Resume graph with approval result
                input_data = Command(resume={"approved": approved})
                interrupted = True

        if not interrupted:
            break

    return full_response


@router.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()

    user_id = await _authenticate_ws(ws)
    if not user_id:
        await ws.send_json({"type": "error", "content": "Unauthorized"})
        await ws.close(1008)
        return

    async with async_session() as db:
        user = await db.get(User, UUID(user_id))
        if not user:
            await ws.close(1008)
            return
        conv = await get_or_create_conversation(db, user.id, "web")
        user_tier = user.tier
        conv_id = conv.id

    supervisor = SessionSupervisor(user_id, str(conv_id))
    try:
        graph = await get_jarvis_graph()
        await supervisor.start()

        while True:
            # M10: Check session timeout
            if supervisor.check_timeout():
                await ws.send_json({"type": "error", "content": "Phiên đã hết thời gian (5 phút). Vui lòng gửi lại."})
                break

            data = await ws.receive_json()
            content = data.get("content", "")
            if not content:
                continue

            if not await check_ws_rate(ws.app.state.redis, user_id, user_tier):
                await ws.send_json({"type": "error", "content": "Rate limit exceeded"})
                continue

            async with async_session() as db:
                await save_message(db, conv_id, "user", content)
                history = await load_history(db, conv_id, limit=20)
                convo_ctx = await build_memory_context(conv_id, db)
                pref_ctx = await build_preference_prompt(user_id, db)

            config = {"configurable": {"thread_id": str(conv_id)}}
            user_pref_combined = "\n".join(filter(None, [pref_ctx, convo_ctx]))
            input_data = {
                "messages": history + [HumanMessage(content=content)],
                "user_id": user_id, "user_tier": user_tier, "channel": "web",
                "conversation_id": str(conv_id), "user_preferences": user_pref_combined,
            }

            full_response = await _run_graph(graph, input_data, config, ws)

            await ws.send_json({"type": "done", "content": full_response})
            async with async_session() as db:
                await save_message(db, conv_id, "assistant", full_response)
                await summarize_if_needed(conv_id, db)

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: {user_id}")
    except Exception:
        logger.exception(f"WS error: {user_id}")
        await ws.close(1011)
    finally:
        await supervisor.stop()
