"""Post-turn memory extraction — runs async after response is sent."""
import json
import logging

from langchain_core.messages import BaseMessage

from llm.gateway import get_llm
from llm.embeddings import embed_text
from memory.service import save_memory
from memory.consolidation import consolidate_fact
from db.session import async_session

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Phân tích đoạn hội thoại sau và trích xuất thông tin cần ghi nhớ về user.

Trả về JSON (KHÔNG markdown):
{{"facts": ["fact1", "fact2"], "episode": "tóm tắt ngắn"}}

Nếu không có gì đáng nhớ: {{"facts": [], "episode": ""}}

Hội thoại:
{conversation}"""


async def extract_memories(messages: list[BaseMessage], user_id: str = "") -> dict:
    """Extract and persist memories from conversation turn."""
    if len(messages) < 2 or not user_id:
        return {}

    conversation = "\n".join(f"{m.type}: {m.content}" for m in messages[-6:])
    llm = get_llm("gemini-2.0-flash")

    try:
        resp = await llm.ainvoke(EXTRACTION_PROMPT.format(conversation=conversation))
        data = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())

        async with async_session() as db:
            for fact in data.get("facts", []):
                if fact:
                    await consolidate_fact(user_id, fact, db)

            episode = data.get("episode", "")
            if episode:
                emb = await embed_text(episode)
                await save_memory(user_id, episode, "episodic", emb, db, importance=0.5)

        return data
    except Exception:
        logger.exception("Memory extraction failed")
        return {}
