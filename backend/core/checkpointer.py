"""M7 LangGraph Checkpointing — PostgreSQL-backed state persistence."""
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from core.config import settings

_saver: AsyncPostgresSaver | None = None


async def get_checkpointer() -> AsyncPostgresSaver:
    """Lazy-init singleton AsyncPostgresSaver."""
    global _saver
    if _saver is None:
        # Convert asyncpg URL to psycopg format
        db_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        _saver = AsyncPostgresSaver.from_conn_string(db_url)
        await _saver.setup()
    return _saver
