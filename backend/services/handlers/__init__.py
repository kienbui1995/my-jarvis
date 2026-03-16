"""Auto-import all trigger handlers to register them."""
from services.handlers import (  # noqa: F401
    budget,
    calendar_conflict,
    deadline,
    memory_insight,
    morning_briefing,
    scheduled_agent,
)
