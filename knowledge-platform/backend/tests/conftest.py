import pytest
from app.config import Settings


@pytest.fixture
def settings():
    return Settings(
        DATABASE_URL="postgresql+asyncpg://knowledge:knowledge123@localhost:5432/knowledge_test",
        REDIS_URL="redis://localhost:6379/1",
        LLM_API_KEY="test-key",
    )
