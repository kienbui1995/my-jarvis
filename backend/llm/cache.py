"""Prompt cache — inject Anthropic cache_control headers on system prompt + tools."""
import copy

from langchain_core.messages import BaseMessage


def with_cache_control(messages: list[BaseMessage], model: str) -> list[BaseMessage]:
    """Inject cache_control for Anthropic models. Marks system prompt as cacheable.

    Returns a new list with a copied system message to avoid mutating the original.
    """
    if "claude" not in model:
        return messages
    result = []
    for m in messages:
        if m.type == "system":
            m = copy.copy(m)
            m.additional_kwargs = {**m.additional_kwargs, "cache_control": {"type": "ephemeral"}}
        result.append(m)
    return result
