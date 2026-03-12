"""Context Window Guard — ensure assembled context fits within model's token limit."""
import logging

logger = logging.getLogger(__name__)

MODEL_CONTEXT_LIMITS = {
    "gemini-2.0-flash": 1_000_000,
    "gemini-2.5-flash": 1_000_000,
    "claude-haiku-4.5": 200_000,
    "claude-sonnet-4.6": 200_000,
    "gpt-5.2": 128_000,
    "deepseek-v3.2": 64_000,
    "llama-3.3-70b": 128_000,
    "mixtral-8x22b": 64_000,
    "qwen-2.5-72b": 128_000,
}

# Reserve 20% for model output
OUTPUT_RESERVE_RATIO = 0.20
# Max tokens for a single tool result before truncation
MAX_TOOL_RESULT_TOKENS = 500


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for mixed Vietnamese/English."""
    return len(text) // 4 + 1


def guard_context(messages: list, model: str, tools_description: str = "") -> list:
    """Trim messages to fit within model's context window.

    Strategy:
    1. Truncate verbose tool results
    2. Drop oldest non-system messages if still over budget
    """
    max_tokens = MODEL_CONTEXT_LIMITS.get(model, 128_000)
    available = int(max_tokens * (1 - OUTPUT_RESERVE_RATIO))
    tools_tokens = _estimate_tokens(tools_description)
    available -= tools_tokens

    # Separate system messages from conversation
    system_msgs = [m for m in messages if getattr(m, "type", "") == "system"]
    other_msgs = [m for m in messages if getattr(m, "type", "") != "system"]

    system_tokens = sum(_estimate_tokens(m.content) for m in system_msgs)
    budget = available - system_tokens

    # Pass 1: truncate verbose tool results (create new messages, don't mutate)
    trimmed = []
    for m in other_msgs:
        if getattr(m, "type", "") == "tool":
            content = m.content if isinstance(m.content, str) else str(m.content)
            if _estimate_tokens(content) > MAX_TOOL_RESULT_TOKENS:
                from langchain_core.messages import ToolMessage
                m = ToolMessage(content=content[:2000] + "\n...[truncated]", tool_call_id=getattr(m, "tool_call_id", ""))
        trimmed.append(m)
    other_msgs = trimmed

    # Pass 2: drop oldest messages if over budget
    total = sum(_estimate_tokens(m.content if isinstance(m.content, str) else str(m.content)) for m in other_msgs)
    while total > budget and len(other_msgs) > 2:
        dropped = other_msgs.pop(0)
        total -= _estimate_tokens(dropped.content if isinstance(dropped.content, str) else str(dropped.content))
        logger.debug(f"Context guard: dropped message type={getattr(dropped, 'type', '?')}")

    if total > budget:
        logger.warning(f"Context guard: still over budget after trimming ({total}/{budget} tokens)")

    return system_msgs + other_msgs
