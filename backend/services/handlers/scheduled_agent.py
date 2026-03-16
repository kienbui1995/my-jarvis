"""Scheduled agent trigger — run user-defined prompts on cron schedule."""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ProactiveTrigger
from services.trigger_engine import TriggerHandler, register_handler

logger = logging.getLogger(__name__)


@register_handler
class ScheduledAgentHandler(TriggerHandler):
    TRIGGER_TYPE = "scheduled_agent"
    LISTENS_TO = ["cron.scheduled_agent"]

    async def should_fire(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> bool:
        return bool((trigger.config or {}).get("prompt"))

    async def build_message(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> str:
        """Execute the agent with the configured prompt and return result."""
        prompt = (trigger.config or {}).get("prompt", "")
        if not prompt:
            return ""

        try:
            from langchain_core.messages import HumanMessage

            from agent.graph import get_jarvis_graph

            graph = await get_jarvis_graph()
            config = {"configurable": {"thread_id": f"scheduled-{trigger.id}"}}
            result = await graph.ainvoke({
                "messages": [HumanMessage(content=prompt)],
                "user_id": str(trigger.user_id),
                "user_tier": "pro",
                "channel": "scheduled",
                "conversation_id": "",
            }, config=config)
            response = result.get("final_response", "")
            return f"🤖 Scheduled: {response}" if response else ""
        except Exception:
            logger.exception(f"Scheduled agent failed for trigger {trigger.id}")
            return ""
