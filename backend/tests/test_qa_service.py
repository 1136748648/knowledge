import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.qa_service import QAService
from app.models.schemas import UserContext


@pytest.fixture
def qa_service():
    return QAService()


@pytest.fixture
def normal_user():
    return UserContext(
        user_id="user-1",
        username="normaluser",
        email="user@test.com",
        roles=["employee"],
        dept_id="dept-1",
    )


class TestQAService:
    @pytest.mark.asyncio
    async def test_ask_question_returns_result(self, qa_service, normal_user):
        mock_result = {
            "answer": "This is the answer",
            "sources": ["source1", "source2"],
            "intent": "wiki_search",
            "confidence": 0.95,
        }
        
        with patch("app.services.qa_service.RouterAgent") as MockRouterAgent:
            mock_agent = AsyncMock()
            mock_agent.route.return_value = mock_result
            MockRouterAgent.return_value = mock_agent
            
            result = await qa_service.ask_question(normal_user, "What is Python?")
            
            MockRouterAgent.assert_called_once_with(normal_user)
            mock_agent.route.assert_called_once_with("What is Python?")
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_ask_question_passes_user_context(self, qa_service, normal_user):
        with patch("app.services.qa_service.RouterAgent") as MockRouterAgent:
            mock_agent = AsyncMock()
            mock_agent.route.return_value = {"answer": "test"}
            MockRouterAgent.return_value = mock_agent
            
            await qa_service.ask_question(normal_user, "test question")
            
            MockRouterAgent.assert_called_once_with(normal_user)

    @pytest.mark.asyncio
    async def test_ask_question_handles_empty_question(self, qa_service, normal_user):
        mock_result = {
            "answer": "Please provide a question.",
            "sources": [],
            "intent": "unknown",
            "confidence": 0.0,
        }
        
        with patch("app.services.qa_service.RouterAgent") as MockRouterAgent:
            mock_agent = AsyncMock()
            mock_agent.route.return_value = mock_result
            MockRouterAgent.return_value = mock_agent
            
            result = await qa_service.ask_question(normal_user, "")
            
            assert result == mock_result