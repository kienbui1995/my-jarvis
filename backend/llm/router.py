"""Smart model router — classify complexity and select optimal model."""
from core.config import settings

# Models that require specific API keys
_MODEL_KEYS = {
    "claude-haiku-4.5": settings.ANTHROPIC_API_KEY,
    "claude-sonnet-4.6": settings.ANTHROPIC_API_KEY,
    "gpt-5.2": settings.OPENAI_API_KEY,
    "deepseek-v3.2": settings.DEEPSEEK_API_KEY,
    "llama-3.3-70b": settings.OPENROUTER_API_KEY,
    "mixtral-8x22b": settings.OPENROUTER_API_KEY,
    "qwen-2.5-72b": settings.OPENROUTER_API_KEY,
}


def _is_available(model: str) -> bool:
    key = _MODEL_KEYS.get(model)
    return key is None or bool(key)  # None = Google (always available if GOOGLE_API_KEY set)

# Cost per 1M tokens (input) — used for budget estimation
MODEL_COSTS = {
    "gemini-2.0-flash": 0.10,
    "gemini-2.5-flash": 0.15,
    "claude-haiku-4.5": 1.00,
    "claude-sonnet-4.6": 3.00,
    "gpt-5.2": 5.00,
    "deepseek-v3.2": 0.27,
    "llama-3.3-70b": 0.40,
    "mixtral-8x22b": 0.65,
    "qwen-2.5-72b": 0.35,
}

TIER_MODELS = {
    "simple": ["gemini-2.0-flash", "deepseek-v3.2", "llama-3.3-70b"],
    "medium": ["claude-haiku-4.5", "gemini-2.5-flash", "mixtral-8x22b"],
    "complex": ["claude-sonnet-4.6", "gpt-5.2", "qwen-2.5-72b"],
}

# Fallback chain per tier
FALLBACK = {
    "gemini-2.0-flash": "deepseek-v3.2",
    "claude-haiku-4.5": "gemini-2.5-flash",
    "claude-sonnet-4.6": "gpt-5.2",
}


def select_model(complexity: str, budget_remaining: float) -> str:
    """Pick the best model for given complexity within budget."""
    candidates = TIER_MODELS.get(complexity, TIER_MODELS["simple"])
    for model in candidates:
        if not _is_available(model):
            continue
        est_cost = MODEL_COSTS.get(model, 1.0) * 0.001
        if est_cost <= budget_remaining or budget_remaining <= 0:
            return model
    # Fallback to cheapest
    return "gemini-2.0-flash"


