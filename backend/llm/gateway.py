"""LLM Gateway — unified interface to multiple LLM providers."""
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from core.config import settings

# Provider registry — lazy init
_providers: dict[str, BaseChatModel] = {}

MODEL_PROVIDERS = {
    "gemini-2.0-flash": ("google", "gemini-2.0-flash"),
    "gemini-2.5-flash": ("google", "gemini-2.5-flash"),
    "claude-haiku-4.5": ("anthropic", "claude-3-5-haiku-20241022"),
    "claude-sonnet-4.6": ("anthropic", "claude-sonnet-4-20250514"),
    "gpt-5.2": ("openai", "gpt-4o"),
    "deepseek-v3.2": ("openai", "deepseek-chat"),  # OpenAI-compatible API
    # OpenRouter models
    "llama-3.3-70b": ("openrouter", "meta-llama/llama-3.3-70b-instruct"),
    "mixtral-8x22b": ("openrouter", "mistralai/mixtral-8x22b-instruct"),
    "qwen-2.5-72b": ("openrouter", "qwen/qwen-2.5-72b-instruct"),
}


def _init_provider(alias: str) -> BaseChatModel:
    provider, model_name = MODEL_PROVIDERS[alias]
    if provider == "google":
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=settings.GOOGLE_API_KEY)
    elif provider == "anthropic":
        return ChatAnthropic(model=model_name, anthropic_api_key=settings.ANTHROPIC_API_KEY)
    elif provider == "openai":
        kwargs = {"model": model_name, "openai_api_key": settings.OPENAI_API_KEY}
        if "deepseek" in alias:
            kwargs["openai_api_base"] = "https://api.deepseek.com/v1"
            kwargs["openai_api_key"] = settings.DEEPSEEK_API_KEY
        return ChatOpenAI(**kwargs)
    elif provider == "openrouter":
        return ChatOpenAI(
            model=model_name,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
        )
    raise ValueError(f"Unknown provider: {provider}")


def get_llm(model_alias: str) -> BaseChatModel:
    """Get or create LLM instance by alias."""
    if model_alias not in _providers:
        _providers[model_alias] = _init_provider(model_alias)
    return _providers[model_alias]
