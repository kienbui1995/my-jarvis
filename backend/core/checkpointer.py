"""M7 LangGraph Checkpointing — PostgreSQL-backed state persistence."""
import asyncio

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from core.config import settings

_saver: AsyncPostgresSaver | None = None
_cm = None
_lock = asyncio.Lock()


async def get_checkpointer() -> AsyncPostgresSaver:
    """Lazy-init AsyncPostgresSaver, reconnect if connection lost."""
    global _saver, _cm
    async with _lock:
        db_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")

        if _saver is not None:
            try:
                # Test if connection is still alive
                async with _saver.conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                return _saver
            except Exception:
                # Connection dead, cleanup and recreate
                try:
                    await _cm.__aexit__(None, None, None)
                except Exception:
                    pass
                _saver = None
                _cm = None

        _cm = AsyncPostgresSaver.from_conn_string(db_url)
        _saver = await _cm.__aenter__()
        await _saver.setup()
        return _saver
