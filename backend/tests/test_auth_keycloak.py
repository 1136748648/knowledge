import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.auth_service import AuthService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.get_by_username.return_value = None
    repo.create.return_value = MagicMock(id="user-id-123", username="testuser", roles=["user"], dept_id=None)
    return repo


class TestKeycloakAuthService:
    @pytest.mark.asyncio
    async def test_keycloak_callback_new_user(self, mock_repo):
        service = AuthService(mock_repo)
        result = await service.keycloak_callback("newuser")
        assert "user_id" in result
        assert result["user_id"] == "newuser"
        assert result["roles"] == ["employee"]

    @pytest.mark.asyncio
    async def test_keycloak_callback_existing_user(self, mock_repo):
        mock_user = MagicMock(id="existing-user-id", username="existinguser", roles=["user"], dept_id="dept-1")
        mock_repo.get_by_username.return_value = mock_user
        
        service = AuthService(mock_repo)
        result = await service.keycloak_callback("existinguser")
        assert result["user_id"] == "existing-user-id"
        assert result["roles"] == ["user"]
        assert result["dept_id"] == "dept-1"