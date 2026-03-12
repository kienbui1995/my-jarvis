"""M5 User Preference Learning — explicit extraction + behavioral patterns.

Level 1: Extract preferences from each conversation (tone, topics, etc.)
Level 2: Periodic behavioral pattern learning (weekly, via background job)
"""
import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.models.preference import UserPreference, UserPromptRule
from llm.gateway import get_llm

logger = logging.getLogger(__name__)

EXTRACT_PREF_PROMPT = """Phân tích hội thoại và trích xuất preferences của user.

Trả về JSON (KHÔNG markdown):
{{"tone": "formal|casual|mixed|null", "language": "vi|en|mixed|null", "verbosity": "concise|detailed|null", "interests": ["topic1"], "rules": ["rule nếu user yêu cầu cụ thể"]}}

Chỉ trả về field có giá trị mới phát hiện, null nếu không rõ.

Hội thoại:
{conversation}"""


async def extract_preferences(messages: list, user_id: str, db: AsyncSession) -> None:
    """Level 1: Extract explicit preferences from conversation turn."""
    if not settings.PREFERENCE_LEARNING_ENABLED or len(messages) < 2:
        return

    uid = UUID(user_id)
    convo = "\n".join(f"{m.type}: {m.content}" for m in messages[-6:])

    try:
        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(EXTRACT_PREF_PROMPT.format(conversation=convo))
        data = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
    except Exception:
        logger.debug("Preference extraction failed", exc_info=True)
        return

    # Upsert preferences
    pref = (await db.execute(
        select(UserPreference).where(UserPreference.user_id == uid)
    )).scalar_one_or_none()

    if not pref:
        pref = UserPreference(user_id=uid)
        db.add(pref)

    if data.get("tone"):
        pref.tone = data["tone"]
    if data.get("language"):
        pref.language = data["language"]
    if data.get("verbosity"):
        pref.verbosity = data["verbosity"]
    if data.get("interests"):
        existing = pref.interests or []
        pref.interests = list(set(existing + data["interests"]))[:20]

    # Save explicit rules (dedup by content)
    if data.get("rules"):
        existing_rules = {r.rule for r in (await db.execute(
            select(UserPromptRule).where(UserPromptRule.user_id == uid)
        )).scalars().all()}
        for rule_text in data["rules"]:
            if rule_text and rule_text not in existing_rules:
                db.add(UserPromptRule(user_id=uid, rule=rule_text, confidence=0.8, source="explicit"))

    await db.commit()


async def build_preference_prompt(user_id: str, db: AsyncSession) -> str:
    """Build preference context string for system prompt injection."""
    uid = UUID(user_id)
    pref = (await db.execute(
        select(UserPreference).where(UserPreference.user_id == uid)
    )).scalar_one_or_none()

    if not pref:
        return ""

    parts = []
    if pref.tone:
        parts.append(f"Tone: {pref.tone}")
    if pref.verbosity:
        parts.append(f"Verbosity: {pref.verbosity}")
    if pref.language:
        parts.append(f"Language: {pref.language}")
    if pref.interests:
        parts.append(f"Interests: {', '.join(pref.interests[:5])}")

    # Load active rules
    rules = (await db.execute(
        select(UserPromptRule).where(UserPromptRule.user_id == uid).order_by(UserPromptRule.confidence.desc()).limit(5)
    )).scalars().all()
    for r in rules:
        parts.append(f"Rule: {r.rule}")

    return "[User Preferences] " + " | ".join(parts) if parts else ""
