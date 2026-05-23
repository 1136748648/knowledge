import pytest
from app.config import Settings


@pytest.fixture
def settings():
    return Settings(
        DATABASE_URL="postgresql+asyncpg://knowledge:knowledge123@localhost:5432/knowledge_test",
        REDIS_URL="redis://localhost:6379/1",
        LLM_API_KEY="test-key",
    )


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
