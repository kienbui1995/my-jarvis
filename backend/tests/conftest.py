"""Shared test fixtures — fresh DB engine per test, Redis mock, test client."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings

settings.SECRET_KEY = "test-secret"
settings.RATE_LIMIT_ENABLED = False
settings.MULTI_AGENT_ENABLED = True
settings.DEBUG = False


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """In-memory Redis mock with pipeline support."""
    store = {}
    r = AsyncMock()
    r.ping = AsyncMock(return_value=True)
    r.get = AsyncMock(side_effect=lambda k: store.get(k))
    r.close = AsyncMock()

    pipe = MagicMock()
    pipe.incr = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = AsyncMock(return_value=[1, True])
    r.pipeline = MagicMock(return_value=pipe)
    return r


@pytest.fixture
async def client(mock_redis):
    """Async HTTP test client with fresh DB engine per test."""
    # Create a fresh engine on the test event loop
    test_engine = create_async_engine(settings.DATABASE_URL, pool_size=5, max_overflow=0)
    test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    from main import app
    from core.deps import get_db

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.state.redis = mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await test_engine.dispose()
