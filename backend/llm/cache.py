"""Prompt cache — inject Anthropic cache_control headers on system prompt + tools."""
from langchain_core.messages import BaseMessage


def with_cache_control(messages: list[BaseMessage], model: str) -> list[BaseMessage]:
    """Inject cache_control for Anthropic models. Marks system prompt as cacheable."""
    if "claude" not in model:
        return messages
    for m in messages:
        if m.type == "system":
            m.additional_kwargs["cache_control"] = {"type": "ephemeral"}
            break
    return messages
