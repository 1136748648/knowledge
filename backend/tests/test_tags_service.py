import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from app.services.tags_service import TagsService
from app.models.wiki_storage import WikiTag


@pytest.fixture
def mock_tag_repo():
    return AsyncMock()


@pytest.fixture
def mock_page_repo():
    return AsyncMock()


@pytest.fixture
def tags_service(mock_tag_repo, mock_page_repo):
    return TagsService(mock_tag_repo, mock_page_repo)


class TestTagsServiceListTags:
    @pytest.mark.asyncio
    async def test_list_tags_empty(self, tags_service, mock_tag_repo):
        mock_tag_repo.get_all_with_children.return_value = []
        
        result = await tags_service.list_tags()
        
        assert result == []
        mock_tag_repo.get_all_with_children.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tags_with_data(self, tags_service, mock_tag_repo):
        mock_tag = MagicMock(spec=WikiTag)
        mock_tag.id = uuid.uuid4()
        mock_tag.name = "Test Tag"
        mock_tag.color = "#FF5733"
        mock_tag.description = "Test description"
        mock_tag.parent_id = None
        mock_tag.created_by = "admin"
        mock_tag.created_at = None
        
        mock_tag_repo.get_all_with_children.return_value = [mock_tag]
        
        result = await tags_service.list_tags()
        
        assert len(result) == 1
        assert result[0]["name"] == "Test Tag"


class TestTagsServiceGetTagTree:
    @pytest.mark.asyncio
    async def test_get_tag_tree_empty(self, tags_service, mock_tag_repo):
        mock_tag_repo.get_root_tags.return_value = []
        
        result = await tags_service.get_tag_tree()
        
        assert result == []
        mock_tag_repo.get_root_tags.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tag_tree_with_children(self, tags_service, mock_tag_repo):
        parent_id = uuid.uuid4()
        child_id = uuid.uuid4()
        
        parent_tag = MagicMock(spec=WikiTag)
        parent_tag.id = parent_id
        parent_tag.name = "Parent"
        parent_tag.color = "#FF0000"
        parent_tag.description = "Parent tag"
        
        child_tag = MagicMock(spec=WikiTag)
        child_tag.id = child_id
        child_tag.name = "Child"
        child_tag.color = "#00FF00"
        child_tag.description = "Child tag"
        
        mock_tag_repo.get_root_tags.return_value = [parent_tag]
        mock_tag_repo.get_children.side_effect = lambda tag_id: [child_tag] if tag_id == parent_id else []
        
        result = await tags_service.get_tag_tree()
        
        assert len(result) == 1
        assert result[0]["name"] == "Parent"
        assert len(result[0]["children"]) == 1
        assert result[0]["children"][0]["name"] == "Child"


class TestTagsServiceCreateTag:
    @pytest.mark.asyncio
    async def test_create_tag_success(self, tags_service, mock_tag_repo):
        name = "New Tag"
        color = "#FF5733"
        description = "A new tag"
        parent_id = None
        created_by = "admin"
        
        mock_tag_repo.get_by_name.return_value = None
        mock_tag_repo.create.return_value = MagicMock(spec=WikiTag, id=uuid.uuid4())
        
        result = await tags_service.create_tag(name, color, description, parent_id, created_by)
        
        assert result is not None
        mock_tag_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tag_duplicate_name(self, tags_service, mock_tag_repo):
        mock_tag_repo.get_by_name.return_value = MagicMock(spec=WikiTag)
        
        with pytest.raises(ValueError) as exc_info:
            await tags_service.create_tag("Existing Tag", "#FF0000", "", None, "admin")
        
        assert "already exists" in str(exc_info.value)


class TestTagsServiceUpdateTag:
    @pytest.mark.asyncio
    async def test_update_tag_success(self, tags_service, mock_tag_repo):
        tag_id = uuid.uuid4()
        mock_tag = MagicMock(spec=WikiTag)
        mock_tag.id = tag_id
        mock_tag.name = "Old Name"
        
        mock_tag_repo.get_by_id.return_value = mock_tag
        mock_tag_repo.update.return_value = mock_tag
        
        result = await tags_service.update_tag(tag_id, "New Name", "#00FF00", "Updated", None)
        
        assert result is not None
        mock_tag_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tag_not_found(self, tags_service, mock_tag_repo):
        mock_tag_repo.get_by_id.return_value = None
        
        result = await tags_service.update_tag(uuid.uuid4(), "Name", "#FF0000", "", None)
        
        assert result is None


class TestTagsServiceDeleteTag:
    @pytest.mark.asyncio
    async def test_delete_tag_success(self, tags_service, mock_tag_repo):
        tag_id = uuid.uuid4()
        mock_tag_repo.delete.return_value = True
        
        result = await tags_service.delete_tag(tag_id)
        
        assert result is True
        mock_tag_repo.delete.assert_called_once_with(tag_id)

    @pytest.mark.asyncio
    async def test_delete_tag_failure(self, tags_service, mock_tag_repo):
        mock_tag_repo.delete.return_value = False
        
        result = await tags_service.delete_tag(uuid.uuid4())
        
        assert result is False


class TestTagsServicePageTagging:
    @pytest.mark.asyncio
    async def test_add_tag_to_page_success(self, tags_service, mock_tag_repo, mock_page_repo):
        page_id = uuid.uuid4()
        tag_id = uuid.uuid4()
        
        mock_page = MagicMock()
        mock_page.tags = []
        mock_tag = MagicMock()
        
        mock_page_repo.get_by_id.return_value = mock_page
        mock_tag_repo.get_by_id.return_value = mock_tag
        
        result = await tags_service.add_tag_to_page(page_id, tag_id)
        
        assert result is True
        mock_page_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_tag_to_page_page_not_found(self, tags_service, mock_tag_repo, mock_page_repo):
        mock_page_repo.get_by_id.return_value = None
        
        result = await tags_service.add_tag_to_page(uuid.uuid4(), uuid.uuid4())
        
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_tag_from_page_success(self, tags_service, mock_tag_repo, mock_page_repo):
        page_id = uuid.uuid4()
        tag_id = uuid.uuid4()
        
        mock_tag = MagicMock()
        mock_page = MagicMock()
        mock_page.tags = [mock_tag]
        
        mock_page_repo.get_by_id.return_value = mock_page
        mock_tag_repo.get_by_id.return_value = mock_tag
        
        result = await tags_service.remove_tag_from_page(page_id, tag_id)
        
        assert result is True
        mock_page_repo.update.assert_called_once()
