"""Edition detection — Pro (full intelligence) vs Community (basic framework).

Pro: all agent nodes, memory intelligence, proactive handlers
Community: basic routing, no memory consolidation, no skills learning
"""
import logging

logger = logging.getLogger(__name__)


def _detect_edition() -> str:
    try:
        from agent.nodes.router import router_node  # noqa: F401
        from memory.consolidation import consolidate_fact  # noqa: F401
        return "pro"
    except ImportError:
        return "community"


EDITION = _detect_edition()
IS_PRO = EDITION == "pro"

if not IS_PRO:
    logger.warning("Running MY JARVIS Community Edition — intelligence modules not available")
