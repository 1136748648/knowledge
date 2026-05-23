import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from app.services.wiki_service import WikiService
from app.models.schemas import UserContext, WikiPageCreate, WikiPageUpdate


@pytest.fixture
def mock_page_repo():
    return AsyncMock()


@pytest.fixture
def mock_version_repo():
    return AsyncMock()


@pytest.fixture
def wiki_service(mock_page_repo, mock_version_repo):
    return WikiService(mock_page_repo, mock_version_repo)


@pytest.fixture
def admin_user():
    return UserContext(
        user_id="admin-1",
        username="admin",
        email="admin@test.com",
        roles=["admin"],
        dept_id="dept-1",
    )


@pytest.fixture
def normal_user():
    return UserContext(
        user_id="user-1",
        username="normaluser",
        email="user@test.com",
        roles=["employee"],
        dept_id="dept-1",
    )


class TestWikiServiceListPages:
    @pytest.mark.asyncio
    async def test_list_pages_returns_empty_without_permission(self, wiki_service, normal_user):
        with patch("app.services.wiki_service.check_permission", return_value=False):
            result = await wiki_service.list_pages(normal_user)
            assert result == []

    @pytest.mark.asyncio
    async def test_list_pages_filters_by_parent_id(self, wiki_service, admin_user):
        parent_id = uuid.uuid4()
        mock_page = MagicMock()
        mock_page.sensitivity = "public"
        
        with patch("app.services.wiki_service.check_permission", return_value=True):
            wiki_service.page_repo.list_by_parent.return_value = [mock_page]
            result = await wiki_service.list_pages(admin_user, parent_id=parent_id)
            wiki_service.page_repo.list_by_parent.assert_called_once()
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_pages_filters_by_sensitivity(self, wiki_service, admin_user):
        mock_page = MagicMock()
        mock_page.sensitivity = "public"
        
        with patch("app.services.wiki_service.check_permission", return_value=True):
            wiki_service.page_repo.list_by_sensitivity.return_value = [mock_page]
            result = await wiki_service.list_pages(admin_user, sensitivity="public")
            wiki_service.page_repo.list_by_sensitivity.assert_called_once()
            assert len(result) == 1


class TestWikiServiceGetPage:
    @pytest.mark.asyncio
    async def test_get_page_returns_none_without_permission(self, wiki_service, normal_user):
        page_id = uuid.uuid4()
        with patch("app.services.wiki_service.check_permission", return_value=False):
            result = await wiki_service.get_page(normal_user, page_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_page_returns_page_for_admin(self, wiki_service, admin_user):
        page_id = uuid.uuid4()
        mock_page = MagicMock()
        mock_page.sensitivity = "secret"
        
        with patch("app.services.wiki_service.check_permission", return_value=True):
            wiki_service.page_repo.get_by_id.return_value = mock_page
            result = await wiki_service.get_page(admin_user, page_id)
            assert result == mock_page


class TestWikiServiceCreatePage:
    @pytest.mark.asyncio
    async def test_create_page_raises_error_without_permission(self, wiki_service, normal_user):
        data = WikiPageCreate(
            title="Test Page",
            content="Test content",
            slug="test-page",
        )
        with patch("app.services.wiki_service.check_permission", return_value=False):
            with pytest.raises(PermissionError):
                await wiki_service.create_page(normal_user, data)

    @pytest.mark.asyncio
    async def test_create_page_creates_page_and_version(self, wiki_service, admin_user):
        data = WikiPageCreate(
            title="Test Page",
            content="Test content",
            slug="test-page",
        )
        mock_page = MagicMock()
        mock_page.id = uuid.uuid4()
        
        with patch("app.services.wiki_service.check_permission", return_value=True):
            wiki_service.page_repo.create.return_value = mock_page
            wiki_service.version_repo.create.return_value = MagicMock()
            
            result = await wiki_service.create_page(admin_user, data)
            
            wiki_service.page_repo.create.assert_called_once()
            wiki_service.version_repo.create.assert_called_once()
            assert result == mock_page


class TestWikiServiceUpdatePage:
    @pytest.mark.asyncio
    async def test_update_page_returns_none_without_permission(self, wiki_service, normal_user):
        page_id = uuid.uuid4()
        data = WikiPageUpdate(title="Updated")
        
        with patch("app.services.wiki_service.check_permission", return_value=False):
            result = await wiki_service.update_page(normal_user, page_id, data)
            assert result is None

    @pytest.mark.asyncio
    async def test_update_page_returns_none_if_page_not_found(self, wiki_service, admin_user):
        page_id = uuid.uuid4()
        data = WikiPageUpdate(title="Updated")
        
        with patch("app.services.wiki_service.check_permission", return_value=True):
            wiki_service.page_repo.get_by_id.return_value = None
            result = await wiki_service.update_page(admin_user, page_id, data)
            assert result is None


class TestWikiServiceDeletePage:
    @pytest.mark.asyncio
    async def test_delete_page_returns_false_without_permission(self, wiki_service, normal_user):
        page_id = uuid.uuid4()
        
        with patch("app.services.wiki_service.check_permission", return_value=False):
            result = await wiki_service.delete_page(normal_user, page_id)
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_page_deletes_existing_page(self, wiki_service, admin_user):
        page_id = uuid.uuid4()
        mock_page = MagicMock()
        
        with patch("app.services.wiki_service.check_permission", return_value=True):
            wiki_service.page_repo.get_by_id.return_value = mock_page
            wiki_service.page_repo.delete.return_value = True
            
            result = await wiki_service.delete_page(admin_user, page_id)
            
            wiki_service.page_repo.delete.assert_called_once_with(page_id)
            assert result is True


class TestWikiServiceSensitivity:
    @pytest.mark.asyncio
    async def test_admin_can_access_secret_pages(self, wiki_service, admin_user):
        with patch("app.services.wiki_service.check_permission", return_value=True):
            allowed = await wiki_service._allowed_sensitivities(admin_user)
            assert "secret" in allowed
            assert "confidential" in allowed
            assert "internal" in allowed
            assert "public" in allowed

    @pytest.mark.asyncio
    async def test_normal_user_can_only_access_public(self, wiki_service, normal_user):
        with patch("app.services.wiki_service.check_permission", return_value=True):
            allowed = await wiki_service._allowed_sensitivities(normal_user)
            assert allowed == ["public"]