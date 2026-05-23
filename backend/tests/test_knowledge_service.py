import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from app.services.knowledge_service import KnowledgeService
from app.models.schemas import UserContext, NavNodeCreate, NavNodeUpdate


@pytest.fixture
def mock_nav_repo():
    return AsyncMock()


@pytest.fixture
def mock_link_repo():
    return AsyncMock()


@pytest.fixture
def knowledge_service(mock_nav_repo, mock_link_repo):
    return KnowledgeService(mock_nav_repo, mock_link_repo)


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


class TestKnowledgeServiceGetTree:
    @pytest.mark.asyncio
    async def test_get_tree_returns_filtered_nodes(self, knowledge_service, normal_user):
        mock_node = MagicMock()
        mock_node.visibility_roles = None
        
        mock_restricted_node = MagicMock()
        mock_restricted_node.visibility_roles = ["admin"]
        
        knowledge_service.nav_repo.get_root_nodes.return_value = [mock_node, mock_restricted_node]
        
        result = await knowledge_service.get_tree(normal_user)
        
        assert len(result) == 1
        assert result[0] == mock_node

    @pytest.mark.asyncio
    async def test_get_tree_admin_sees_all_nodes(self, knowledge_service, admin_user):
        mock_node = MagicMock()
        mock_node.visibility_roles = None
        
        mock_restricted_node = MagicMock()
        mock_restricted_node.visibility_roles = ["admin"]
        
        knowledge_service.nav_repo.get_root_nodes.return_value = [mock_node, mock_restricted_node]
        
        result = await knowledge_service.get_tree(admin_user)
        
        assert len(result) == 2


class TestKnowledgeServiceGetNode:
    @pytest.mark.asyncio
    async def test_get_node_returns_node(self, knowledge_service):
        node_id = uuid.uuid4()
        mock_node = MagicMock()
        
        knowledge_service.nav_repo.get_by_id.return_value = mock_node
        
        result = await knowledge_service.get_node(node_id)
        
        knowledge_service.nav_repo.get_by_id.assert_called_once_with(node_id)
        assert result == mock_node


class TestKnowledgeServiceCreateNode:
    @pytest.mark.asyncio
    async def test_create_node_without_parent(self, knowledge_service, admin_user):
        data = NavNodeCreate(
            name="Test Node",
            icon="folder",
            description="Test description",
        )
        mock_node = MagicMock()
        
        knowledge_service.nav_repo.create.return_value = mock_node
        
        result = await knowledge_service.create_node(admin_user, data)
        
        knowledge_service.nav_repo.create.assert_called_once()
        assert result == mock_node

    @pytest.mark.asyncio
    async def test_create_node_with_parent(self, knowledge_service, admin_user):
        parent_id = uuid.uuid4()
        data = NavNodeCreate(
            name="Child Node",
            parent_id=parent_id,
            icon="file",
        )
        
        mock_parent = MagicMock()
        mock_parent.path = "parent"
        mock_node = MagicMock()
        
        knowledge_service.nav_repo.get_by_id.return_value = mock_parent
        knowledge_service.nav_repo.create.return_value = mock_node
        
        result = await knowledge_service.create_node(admin_user, data)
        
        knowledge_service.nav_repo.get_by_id.assert_called_once_with(parent_id)
        knowledge_service.nav_repo.create.assert_called_once()


class TestKnowledgeServiceUpdateNode:
    @pytest.mark.asyncio
    async def test_update_node_returns_none_if_not_found(self, knowledge_service, admin_user):
        node_id = uuid.uuid4()
        data = NavNodeUpdate(name="Updated")
        
        knowledge_service.nav_repo.get_by_id.return_value = None
        
        result = await knowledge_service.update_node(admin_user, node_id, data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_node_updates_fields(self, knowledge_service, admin_user):
        node_id = uuid.uuid4()
        data = NavNodeUpdate(name="Updated Name", icon="new-icon")
        
        mock_node = MagicMock()
        mock_node.name = "Old Name"
        mock_node.icon = "old-icon"
        
        knowledge_service.nav_repo.get_by_id.return_value = mock_node
        knowledge_service.nav_repo.update.return_value = mock_node
        
        result = await knowledge_service.update_node(admin_user, node_id, data)
        
        assert mock_node.name == "Updated Name"
        assert mock_node.icon == "new-icon"
        knowledge_service.nav_repo.update.assert_called_once()


class TestKnowledgeServiceDeleteNode:
    @pytest.mark.asyncio
    async def test_delete_node_returns_false_if_not_found(self, knowledge_service, admin_user):
        node_id = uuid.uuid4()
        
        knowledge_service.nav_repo.get_by_id.return_value = None
        
        result = await knowledge_service.delete_node(admin_user, node_id)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_node_deletes_existing_node(self, knowledge_service, admin_user):
        node_id = uuid.uuid4()
        mock_node = MagicMock()
        
        knowledge_service.nav_repo.get_by_id.return_value = mock_node
        knowledge_service.nav_repo.delete.return_value = True
        
        result = await knowledge_service.delete_node(admin_user, node_id)
        
        knowledge_service.nav_repo.delete.assert_called_once_with(node_id)
        assert result is True


class TestKnowledgeServiceLinkContent:
    @pytest.mark.asyncio
    async def test_link_content_creates_link(self, knowledge_service, admin_user):
        node_id = uuid.uuid4()
        mock_link = MagicMock()
        
        knowledge_service.link_repo.create.return_value = mock_link
        
        result = await knowledge_service.link_content(admin_user, node_id, "wiki", "doc-123")
        
        knowledge_service.link_repo.create.assert_called_once()
        assert result == mock_link


class TestKnowledgeServiceCanViewNode:
    @pytest.mark.asyncio
    async def test_can_view_node_without_visibility_roles(self, knowledge_service, normal_user):
        mock_node = MagicMock()
        mock_node.visibility_roles = None
        
        result = knowledge_service._can_view_node(normal_user, mock_node)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_can_view_node_admin_sees_all(self, knowledge_service, admin_user):
        mock_node = MagicMock()
        mock_node.visibility_roles = ["hr", "manager"]
        
        result = knowledge_service._can_view_node(admin_user, mock_node)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_can_view_node_role_match(self, knowledge_service, normal_user):
        mock_node = MagicMock()
        mock_node.visibility_roles = ["employee", "hr"]
        
        result = knowledge_service._can_view_node(normal_user, mock_node)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_can_view_node_role_mismatch(self, knowledge_service, normal_user):
        mock_node = MagicMock()
        mock_node.visibility_roles = ["admin", "hr"]
        
        result = knowledge_service._can_view_node(normal_user, mock_node)
        
        assert result is False