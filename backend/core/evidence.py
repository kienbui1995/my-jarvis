"""M9 Evidence Logging — structured per-action audit trail."""
import logging
import time
from contextlib import asynccontextmanager
from uuid import UUID

from core.config import settings
from db.models.evidence import EvidenceLog
from db.session import async_session

logger = logging.getLogger(__name__)


async def log_evidence(
    user_id: str,
    conversation_id: str,
    node: str,
    event_type: str,
    *,
    tool_name: str = "",
    tool_input: dict | None = None,
    tool_output: str = "",
    model_used: str = "",
    tokens_used: int = 0,
    cost: float = 0.0,
    duration_ms: int = 0,
    error: str = "",
    session_id: str = "",
) -> None:
    """Write a single evidence log entry. Best-effort, never raises."""
    if not settings.EVIDENCE_LOGGING_ENABLED:
        return
    try:
        async with async_session() as db:
            db.add(EvidenceLog(
                user_id=UUID(user_id) if user_id else None,
                conversation_id=UUID(conversation_id) if conversation_id else None,
                session_id=session_id or "",
                node=node,
                event_type=event_type,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output[:2000] if tool_output else "",
                model_used=model_used,
                tokens_used=tokens_used,
                cost=cost,
                duration_ms=duration_ms,
                error=error[:1000] if error else "",
            ))
            await db.commit()
    except Exception:
        logger.debug("Evidence log write failed", exc_info=True)


@asynccontextmanager
async def evidence_timer(user_id: str, conversation_id: str, node: str, event_type: str, **kwargs):
    """Context manager that auto-measures duration_ms."""
    start = time.monotonic()
    error = ""
    try:
        yield
    except Exception as e:
        error = str(e)
        raise
    finally:
        ms = int((time.monotonic() - start) * 1000)
        await log_evidence(user_id, conversation_id, node, event_type, duration_ms=ms, error=error, **kwargs)
