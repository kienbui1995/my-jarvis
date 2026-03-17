"""Router node — LLM-based intent classification, model selection, memory context loading."""
import asyncio
import hashlib
import logging

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from pydantic import BaseModel
from typing import Literal

from agent.state import AgentState
from llm.router import select_model
from llm.budget import get_remaining_budget
from llm.gateway import get_llm
from memory.context_builder import build_context
from llm.embeddings import embed_text
from core import injection
from core.injection import scan_injection
from core.config import settings
from agent.registry import SPECIALIST_KEYWORDS
from db.session import async_session
import core.redis as redis_pool

logger = logging.getLogger(__name__)


# ── LLM Classification Schema ────────────────────────────────

class RouterDecision(BaseModel):
    intent: Literal[
        "general_chat", "task_mgmt", "calendar_mgmt", "research",
        "finance", "memory_query", "planning", "creative",
    ] = "general_chat"
    complexity: Literal["simple", "medium", "complex"] = "simple"
    specialist: Literal["", "task", "calendar", "research", "finance", "memory"] = ""
    needs_planning: bool = False
    reasoning: str = ""


ROUTER_SYSTEM = """Bạn là router phân loại intent cho AI assistant. Trả về JSON.

Fields:
- intent: general_chat|task_mgmt|calendar_mgmt|research|finance|memory_query|planning|creative
- complexity: simple (trả lời ngay) | medium (cần 1 tool) | complex (suy luận sâu hoặc nhiều bước)
- specialist: task|calendar|research|finance|memory hoặc "" nếu không cần
- needs_planning: true nếu yêu cầu cần nhiều bước phối hợp
- reasoning: 1 câu giải thích

Ví dụ:
"Mấy giờ rồi?" → simple, general_chat
"Tạo task review code" → medium, task_mgmt, specialist=task
"Lên kế hoạch đi Đà Nẵng tuần sau" → complex, planning, needs_planning=true
"Phân tích chi tiêu 3 tháng" → complex, finance, specialist=finance
"Nhớ gì về cuộc họp hôm qua?" → medium, memory_query, specialist=memory"""


# ── Keyword fallback (v2 logic) ──────────────────────────────

COMPLEX_KW = {"phân tích", "nghiên cứu", "viết bài", "tóm tắt", "so sánh", "đánh giá", "analyze", "research"}
MEDIUM_KW = {"lịch", "cuộc họp", "nhắc nhở", "task", "việc", "chi tiêu", "ngân sách", "hẹn", "deadline"}
PLANNING_KW = {"kế hoạch", "lên plan", "chuẩn bị", "sắp xếp", "tổ chức"}


def _classify_keyword(text: str) -> RouterDecision:
    """Fallback keyword-based classification."""
    lower = text.lower()
    needs_planning = any(w in lower for w in PLANNING_KW)
    if any(w in lower for w in COMPLEX_KW):
        return RouterDecision(intent="research", complexity="complex", needs_planning=needs_planning)
    if any(w in lower for w in MEDIUM_KW):
        return RouterDecision(intent="task_mgmt", complexity="medium")
    return RouterDecision(intent="general_chat", complexity="simple")


def _detect_specialist_keyword(text: str) -> str:
    if not settings.MULTI_AGENT_ENABLED:
        return ""
    lower = text.lower()
    for specialist, keywords in SPECIALIST_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return specialist
    return ""


# ── LLM Classification ───────────────────────────────────────

async def _classify_llm(text: str) -> RouterDecision:
    """LLM-based intent classification with Redis cache + keyword fallback."""
    cache_key = f"router:{hashlib.md5(text[:100].lower().strip().encode()).hexdigest()}"
    r = redis_pool.get()

    # Check cache
    try:
        cached = await r.get(cache_key)
        if cached:
            return RouterDecision.model_validate_json(cached)
    except Exception:
        pass

    # LLM classify with timeout
    try:
        llm = get_llm("gemini-2.0-flash").with_structured_output(RouterDecision)
        result = await asyncio.wait_for(
            llm.ainvoke([
                SystemMessage(content=ROUTER_SYSTEM),
                HumanMessage(content=text[:500]),
            ]),
            timeout=1.0,
        )
        # Cache for 1 hour
        try:
            await r.setex(cache_key, 3600, result.model_dump_json())
        except Exception:
            pass
        return result
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"LLM router fallback to keywords: {e}")
        return _classify_keyword(text)


# ── Router Node ───────────────────────────────────────────────

async def router_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1].content if state["messages"] else ""
    user_id = state.get("user_id", "")
    user_tier = state.get("user_tier", "free")

    # M1: LLM-based classification (with fallback)
    if settings.SMART_ROUTER_ENABLED:
        decision = await _classify_llm(last_msg)
    else:
        decision = _classify_keyword(last_msg)
        decision.specialist = _detect_specialist_keyword(last_msg)

    budget = await get_remaining_budget(user_id, user_tier) if user_id else 0.10

    # Injection scan — block high-confidence injections
    inj_score, inj_pattern = scan_injection(last_msg)
    if inj_score > 0:
        logger.warning(f"Injection detected: user={user_id} score={inj_score} pattern={inj_pattern}")
    if injection.should_block(inj_score):
        return {
            "injection_score": inj_score,
            "final_response": "Xin lỗi, tôi không thể xử lý yêu cầu này.",
            "messages": [AIMessage(content="Xin lỗi, tôi không thể xử lý yêu cầu này.")],
        }

    model = select_model(decision.complexity, budget)

    # Load hot + cold memory
    hot, cold = "", ""
    if user_id:
        async with async_session() as db:
            query_emb = await embed_text(last_msg) if last_msg else None
            ctx = await build_context(user_id, query_emb, db)
            hot, cold = ctx["hot_memory"], ctx["cold_memory"]

    # V8: Load MCP tools
    mcp_tools = []
    if user_id and settings.MCP_GATEWAY_ENABLED:
        try:
            from mcp.loader import load_mcp_tools
            async with async_session() as mcp_db:
                mcp_tools = await load_mcp_tools(user_id, user_tier, "", mcp_db)
        except Exception:
            logger.exception("Failed to load MCP tools")

    return {
        "intent": decision.intent,
        "complexity": decision.complexity,
        "selected_model": model,
        "budget_remaining": budget,
        "hot_memory": hot,
        "cold_memory": cold,
        "injection_score": inj_score,
        "delegation_target": decision.specialist,
        "needs_planning": decision.needs_planning,
        "mcp_tools": mcp_tools,
    }
