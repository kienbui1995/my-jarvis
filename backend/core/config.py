from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "MY JARVIS"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"
    DOMAIN: str = "localhost"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://jarvis:jarvis@postgres:5432/jarvis"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # LiteLLM Proxy
    LITELLM_BASE_URL: str = "http://litellm:4000/v1"
    LITELLM_API_KEY: str = ""

    # LLM (fallback nếu không dùng proxy)
    GOOGLE_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    LLM_DEFAULT_MODEL: str = "gemini-2.0-flash"
    LLM_DAILY_BUDGET_FREE: float = 0.02
    LLM_DAILY_BUDGET_PRO: float = 0.10
    LLM_DAILY_BUDGET_PRO_PLUS: float = 0.25

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    # Zalo
    ZALO_OA_ACCESS_TOKEN: str = ""
    ZALO_OA_SECRET_KEY: str = ""
    ZALO_OA_ID: str = ""
    ZALO_BOT_TOKEN: str = ""
    ZALO_BOT_SECRET_TOKEN: str = ""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "jarvis"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Sentry
    SENTRY_DSN: str = ""

    # Feature flags
    RATE_LIMIT_ENABLED: bool = True
    MULTI_AGENT_ENABLED: bool = True
    SMART_ROUTER_ENABLED: bool = True
    PLANNING_ENABLED: bool = True
    CONVO_MEMORY_ENABLED: bool = True
    MEMORY_CONSOLIDATION_ENABLED: bool = True
    PREFERENCE_LEARNING_ENABLED: bool = True
    CONTEXT_GUARD_ENABLED: bool = True
    CHECKPOINTING_ENABLED: bool = True
    HITL_ENABLED: bool = True
    EVIDENCE_LOGGING_ENABLED: bool = True
    SUPERVISION_ENABLED: bool = True
    TOOL_PERMISSIONS_ENABLED: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}

    def validate_production(self) -> None:
        """Raise if critical secrets are insecure in production."""
        if self.APP_ENV == "production" or not self.DEBUG:
            assert self.SECRET_KEY not in ("change-me", "dev-secret-key-change-in-production-64chars-minimum-random", ""), \
                "SECRET_KEY must be set to a strong random value in production"
            assert len(self.SECRET_KEY) >= 32, "SECRET_KEY must be at least 32 characters"


settings = Settings()
settings.validate_production()
