"""Agent Memory v2 — auto-maintained user profile + goal tracking."""
import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.preference import UserPreference
from llm.gateway import get_llm

logger = logging.getLogger(__name__)

PROFILE_UPDATE_PROMPT = """Cập nhật user profile dựa trên hội thoại.

Profile hiện tại:
{current_profile}

Hội thoại mới:
{conversation}

Trả về JSON profile cập nhật (KHÔNG markdown):
{{"job": "", "location": "", "family": "", "hobbies": [],
  "daily_routine": "", "communication_style": "",
  "active_goals": ["goal 1", "goal 2"],
  "recent_topics": ["topic 1"]}}

Rules:
- Giữ nguyên field cũ nếu không có info mới
- Chỉ thêm/sửa field khi có evidence rõ ràng từ hội thoại
- active_goals: track mục tiêu user đang theo đuổi
- recent_topics: 5 chủ đề gần nhất"""


async def update_profile(
    user_id: str, messages: list, db: AsyncSession,
) -> None:
    """Update user profile based on recent conversation."""
    uid = UUID(user_id)
    pref = (await db.execute(
        select(UserPreference).where(UserPreference.user_id == uid)
    )).scalar_one_or_none()

    if not pref:
        return

    current = json.dumps(pref.interests or {}, ensure_ascii=False)
    convo = "\n".join(
        f"{m.type}: {m.content[:200]}" for m in messages[-6:]
    )

    try:
        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(
            PROFILE_UPDATE_PROMPT.format(
                current_profile=current, conversation=convo,
            )
        )
        data = json.loads(
            resp.content.strip()
            .removeprefix("```json").removesuffix("```").strip()
        )

        # Merge into preferences
        profile = pref.interests or {}
        for key in ("job", "location", "family", "daily_routine",
                     "communication_style"):
            if data.get(key):
                profile[key] = data[key]
        if data.get("hobbies"):
            existing = profile.get("hobbies", [])
            profile["hobbies"] = list(set(existing + data["hobbies"]))[:10]
        if data.get("active_goals"):
            profile["active_goals"] = data["active_goals"][:5]
        if data.get("recent_topics"):
            profile["recent_topics"] = data["recent_topics"][:5]

        pref.interests = profile
        await db.commit()
    except Exception:
        logger.debug("Profile update failed", exc_info=True)


def build_profile_context(profile: dict | None) -> str:
    """Build profile context string for system prompt."""
    if not profile:
        return ""
    parts = []
    if profile.get("job"):
        parts.append(f"Nghề nghiệp: {profile['job']}")
    if profile.get("location"):
        parts.append(f"Ở: {profile['location']}")
    if profile.get("active_goals"):
        parts.append(f"Mục tiêu: {', '.join(profile['active_goals'])}")
    if profile.get("hobbies"):
        parts.append(f"Sở thích: {', '.join(profile['hobbies'][:5])}")
    if profile.get("communication_style"):
        parts.append(f"Style: {profile['communication_style']}")
    return "[User Profile] " + " | ".join(parts) if parts else ""
