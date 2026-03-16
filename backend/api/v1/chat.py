"""HTTP chat endpoint — synchronous graph invocation for clients without WebSocket.

Used by Zalo Mini App and other environments where WS is not available.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import get_jarvis_graph
from core.deps import get_current_user_id, get_db
from db.models import User
from memory.conversation_memory import build_memory_context, summarize_if_needed
from memory.preference_learning import build_preference_prompt
from services.conversation import get_or_create_conversation, load_history, save_message
from services.event_bus import emit

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    content: str
    conversation_id: str | None = None


@router.post("/chat")
async def http_chat(
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Invoke agent graph synchronously. Returns full response."""
    if not body.content.strip():
        raise HTTPException(400, "Empty message")

    user = await db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(401, "User not found")

    conv = await get_or_create_conversation(db, user.id, "zalo_mini_app")
    await save_message(db, conv.id, "user", body.content)
    history = await load_history(db, conv.id, limit=20)
    convo_ctx = await build_memory_context(conv.id, db)
    pref_ctx = await build_preference_prompt(user_id, db)

    graph = await get_jarvis_graph()
    user_pref = "\n".join(filter(None, [pref_ctx, convo_ctx]))
    config = {"configurable": {"thread_id": str(conv.id)}}

    result = await graph.ainvoke({
        "messages": history + [HumanMessage(content=body.content)],
        "user_id": user_id,
        "user_tier": user.tier,
        "channel": "zalo_mini_app",
        "conversation_id": str(conv.id),
        "user_preferences": user_pref,
    }, config=config)

    response_text = result.get(
        "final_response", "Xin lỗi, tôi không thể xử lý yêu cầu này."
    )

    await save_message(
        db, conv.id, "assistant", response_text,
        model_used=result.get("selected_model", ""),
    )
    await summarize_if_needed(conv.id, db)
    await emit("conversation.ended", user_id, {"conversation_id": str(conv.id)})

    return {
        "response": response_text,
        "conversation_id": str(conv.id),
        "model": result.get("selected_model", ""),
    }
