"""LLM Gateway — unified interface via LiteLLM Proxy."""
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from core.config import settings

_providers: dict[str, BaseChatModel] = {}

MODEL_PROVIDERS = {
    "gemini-2.0-flash": "gemini/gemini-2.0-flash",
    "gemini-2.5-flash": "gemini/gemini-2.5-flash",
    "claude-haiku-4.5": "anthropic/claude-3-5-haiku-20241022",
    "claude-sonnet-4.6": "anthropic/claude-sonnet-4-20250514",
    "gpt-5.2": "openai/gpt-4o",
    "deepseek-v3.2": "deepseek/deepseek-chat",
    "llama-3.3-70b": "openrouter/meta-llama/llama-3.3-70b-instruct",
    "mixtral-8x22b": "openrouter/mistralai/mixtral-8x22b-instruct",
    "qwen-2.5-72b": "openrouter/qwen/qwen-2.5-72b-instruct",
}


def get_llm(model_alias: str) -> BaseChatModel:
    """Get or create LLM instance by alias — all routed through LiteLLM Proxy."""
    if model_alias not in _providers:
        model_name = MODEL_PROVIDERS.get(model_alias, model_alias)
        _providers[model_alias] = ChatOpenAI(
            model=model_name,
            openai_api_key=settings.LITELLM_API_KEY,
            openai_api_base=settings.LITELLM_BASE_URL,
        )
    return _providers[model_alias]
