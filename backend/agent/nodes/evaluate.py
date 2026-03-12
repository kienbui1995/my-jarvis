"""Evaluate node — lightweight output validation before sending to user."""
import json
import logging

from langchain_core.messages import AIMessage, HumanMessage

from agent.state import AgentState
from llm.gateway import get_llm

logger = logging.getLogger(__name__)

EVALUATE_PROMPT = """Đánh giá response của AI assistant. Trả về JSON (KHÔNG markdown):
{{"pass": true, "reason": "ok"}} hoặc {{"pass": false, "reason": "lý do"}}

Criteria:
1. Có trả lời đúng câu hỏi không?
2. Có chứa nội dung không phù hợp không?
3. Response có bị cắt giữa chừng không?

User: {user_message}
AI: {ai_response}"""


async def evaluate_node(state: AgentState) -> dict:
    """Validate AI response quality. If fail and retry_count < 1, trigger retry."""
    retry_count = state.get("retry_count", 0)
    if retry_count >= 1 or state.get("complexity", "simple") != "complex":
        return {}  # Only evaluate complex responses to save cost

    messages = state.get("messages", [])
    ai_msgs = [m for m in messages if isinstance(m, AIMessage)]
    human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
    if not ai_msgs or not human_msgs:
        return {}

    ai_response = ai_msgs[-1].content
    user_message = human_msgs[-1].content

    # Skip evaluation for short responses (likely simple acknowledgments)
    if len(ai_response) < 20:
        return {}

    try:
        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(EVALUATE_PROMPT.format(user_message=user_message[:500], ai_response=ai_response[:1000]))
        result = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())

        if not result.get("pass", True):
            logger.warning(f"Evaluate FAIL: {result.get('reason')}")
            return {"retry_count": retry_count + 1}
    except Exception:
        logger.exception("Evaluate node error")

    return {}
