"""M47 Skills Learning Loop — agent learns reusable patterns from complex tasks.

After plan-and-execute completes (≥3 steps), LLM analyzes if the pattern is reusable.
If yes → creates a Skill. On future similar requests → matches skill → faster execution.
Skills self-improve: track success rate, adjust steps based on feedback.
"""
import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.models import Skill, SkillExecution
from llm.gateway import get_llm

logger = logging.getLogger(__name__)

EXTRACT_SKILL_PROMPT = """Bạn là skill extractor. Phân tích task vừa hoàn thành và quyết định có nên tạo skill tái sử dụng không.

Task: {task_description}
Steps thực hiện: {steps}
Kết quả: {result}

Trả về JSON (KHÔNG markdown):
{{"should_create": true/false, "name": "tên skill ngắn gọn (tiếng Việt)", "description": "mô tả 1 câu", "trigger_keywords": ["keyword1", "keyword2"], "steps_template": ["bước 1 template", "bước 2 template"], "reason": "lý do"}}

Rules:
- should_create=true NẾU: task có pattern lặp lại được (research, planning, report...)
- should_create=false NẾU: task quá cụ thể, one-off, hoặc đã có skill tương tự
- trigger_keywords: từ khóa user có thể dùng để trigger skill này
- steps_template: các bước tổng quát hóa (thay giá trị cụ thể bằng {{placeholder}})"""

MATCH_SKILL_PROMPT = """So sánh yêu cầu user với các skills có sẵn.

Yêu cầu: "{user_request}"

Skills:
{skills_list}

Trả về JSON (KHÔNG markdown):
{{"matched_skill_id": "uuid hoặc rỗng nếu không match", "confidence": 0.0-1.0, "adapted_steps": ["bước 1 đã adapt", "bước 2 đã adapt"]}}

Rules:
- confidence >= 0.7 mới match
- adapted_steps: điều chỉnh steps_template cho phù hợp yêu cầu cụ thể"""


async def extract_skill_from_task(
    user_id: str,
    task_description: str,
    steps: list[str],
    result: str,
    db: AsyncSession,
) -> Skill | None:
    """After a complex task, analyze if it should become a reusable skill."""
    if not settings.SKILL_LEARNING_ENABLED or len(steps) < 3:
        return None

    uid = UUID(user_id)

    # Check if similar skill already exists
    existing = (await db.execute(
        select(Skill).where(Skill.user_id == uid, Skill.enabled.is_(True))
    )).scalars().all()

    try:
        llm = get_llm("gemini-2.0-flash")
        existing_names = ", ".join(s.name for s in existing) if existing else "chưa có"
        resp = await llm.ainvoke(EXTRACT_SKILL_PROMPT.format(
            task_description=task_description,
            steps=json.dumps(steps, ensure_ascii=False),
            result=result[:500],
        ) + f"\n\nSkills đã có của user: {existing_names}")
        data = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
    except Exception:
        logger.debug("Skill extraction LLM failed", exc_info=True)
        return None

    if not data.get("should_create"):
        return None

    # Check name collision
    name = data.get("name", "")
    if any(s.name == name for s in existing):
        logger.info(f"Skill '{name}' already exists for user={user_id}")
        return None

    skill = Skill(
        user_id=uid,
        name=name,
        description=data.get("description", ""),
        trigger_keywords=data.get("trigger_keywords", []),
        steps_template=data.get("steps_template", steps),
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    logger.info(f"Created skill '{name}' for user={user_id}")
    return skill


async def match_skill(user_id: str, user_request: str, db: AsyncSession) -> dict | None:
    """Try to match user request to an existing skill. Returns adapted steps or None."""
    if not settings.SKILL_LEARNING_ENABLED:
        return None

    uid = UUID(user_id)
    skills = (await db.execute(
        select(Skill).where(Skill.user_id == uid, Skill.enabled.is_(True))
    )).scalars().all()

    if not skills:
        return None

    # Quick keyword check first
    request_lower = user_request.lower()
    keyword_matches = [s for s in skills if any(kw in request_lower for kw in s.trigger_keywords)]

    candidates = keyword_matches or skills[:10]
    if not candidates:
        return None

    skills_str = "\n".join(
        f"- [{s.id}] {s.name}: {s.description} (keywords: {s.trigger_keywords}, "
        f"used {s.usage_count}x, success {s.success_count}/{s.usage_count})"
        for s in candidates
    )

    try:
        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(MATCH_SKILL_PROMPT.format(
            user_request=user_request, skills_list=skills_str,
        ))
        data = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
    except Exception:
        logger.debug("Skill matching LLM failed", exc_info=True)
        return None

    confidence = data.get("confidence", 0)
    skill_id = data.get("matched_skill_id", "")

    if confidence < 0.7 or not skill_id:
        return None

    try:
        skill_uuid = UUID(skill_id)
    except (ValueError, AttributeError):
        return None

    skill = await db.get(Skill, skill_uuid)
    if not skill or skill.user_id != uid:
        return None

    return {
        "skill_id": str(skill.id),
        "skill_name": skill.name,
        "confidence": confidence,
        "adapted_steps": data.get("adapted_steps", skill.steps_template),
    }


async def record_skill_execution(
    skill_id: str, user_id: str, input_summary: str,
    output_summary: str, steps: list, success: bool,
    duration: float | None, db: AsyncSession,
) -> None:
    """Record a skill execution and update skill stats."""
    sid = UUID(skill_id)
    uid = UUID(user_id)

    db.add(SkillExecution(
        skill_id=sid, user_id=uid, input_summary=input_summary,
        output_summary=output_summary, steps_executed=steps,
        success=success, duration_seconds=duration,
    ))

    skill = await db.get(Skill, sid)
    if skill:
        skill.usage_count += 1
        if success:
            skill.success_count += 1

    await db.commit()
