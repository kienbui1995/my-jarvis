"""V12: Autonomy triggers — weekly digest, decision review."""
from datetime import date, datetime

from services.trigger_engine import TriggerHandler, register_handler


@register_handler
class WeeklyDigestHandler(TriggerHandler):
    TRIGGER_TYPE = "weekly_digest"
    LISTENS_TO = ["cron.weekly_sunday"]

    async def should_fire(self, trigger, event, db) -> bool:
        return True

    async def build_message(self, trigger, event, db) -> str:
        from agent.reasoning.cross_domain import cross_domain_insights
        from services.pattern_detector import detect_patterns

        uid = str(trigger.user_id)
        insights = await cross_domain_insights(uid, db)
        patterns = await detect_patterns(uid, db)

        lines = ["📋 **Weekly Digest**"]
        for i in insights:
            lines.append(f"  {i}")
        for p in patterns:
            lines.append(f"  {p}")
        return "\n".join(lines) if len(lines) > 1 else "📋 Tuần này chưa có đủ dữ liệu."


@register_handler
class DecisionReviewHandler(TriggerHandler):
    TRIGGER_TYPE = "decision_review"
    LISTENS_TO = ["cron.morning_briefing"]

    async def should_fire(self, trigger, event, db) -> bool:
        from sqlalchemy import select
        from db.models import Decision
        self._decisions = (await db.execute(
            select(Decision).where(
                Decision.user_id == trigger.user_id,
                Decision.review_date == date.today(),
                Decision.outcome.is_(None),
            )
        )).scalars().all()
        return len(self._decisions) > 0

    async def build_message(self, trigger, event, db) -> str:
        lines = ["🔍 Đến lúc review quyết định:"]
        for d in self._decisions:
            lines.append(f"  • {d.title} (quyết định: {d.chosen})")
            lines.append(f"    Kết quả thế nào? Đánh giá 1-5 sao.")
        return "\n".join(lines)
