import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from app.services.chunking_service import ChunkingService
from app.models.wiki_storage import ChunkingRule


@pytest.fixture
def mock_rule_repo():
    return AsyncMock()


@pytest.fixture
def chunking_service(mock_rule_repo):
    return ChunkingService(mock_rule_repo)


class TestChunkingServiceListRules:
    @pytest.mark.asyncio
    async def test_list_rules_empty(self, chunking_service, mock_rule_repo):
        mock_rule_repo.get_all.return_value = []
        
        result = await chunking_service.list_rules()
        
        assert result == []
        mock_rule_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_rules_with_data(self, chunking_service, mock_rule_repo):
        mock_rule = MagicMock(spec=ChunkingRule)
        mock_rule.id = uuid.uuid4()
        mock_rule.name = "Heading Rule"
        mock_rule.description = "Split by headings"
        mock_rule.rule_type = "heading"
        mock_rule.rule_config = {"levels": [1, 2]}
        mock_rule.is_active = True
        mock_rule.sort_order = 1
        mock_rule.created_at = None
        mock_rule.updated_at = None
        
        mock_rule_repo.get_all.return_value = [mock_rule]
        
        result = await chunking_service.list_rules()
        
        assert len(result) == 1
        assert result[0]["name"] == "Heading Rule"
        assert result[0]["rule_type"] == "heading"


class TestChunkingServiceGetActiveRules:
    @pytest.mark.asyncio
    async def test_get_active_rules_empty(self, chunking_service, mock_rule_repo):
        mock_rule_repo.get_active_rules.return_value = []
        
        result = await chunking_service.get_active_rules()
        
        assert result == []
        mock_rule_repo.get_active_rules.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_rules_with_data(self, chunking_service, mock_rule_repo):
        mock_rule = MagicMock(spec=ChunkingRule)
        mock_rule.id = uuid.uuid4()
        mock_rule.name = "Active Rule"
        mock_rule.description = "An active rule"
        mock_rule.rule_type = "length"
        mock_rule.rule_config = {"max_length": 100}
        mock_rule.is_active = True
        mock_rule.sort_order = 1
        mock_rule.created_at = None
        mock_rule.updated_at = None
        
        mock_rule_repo.get_active_rules.return_value = [mock_rule]
        
        result = await chunking_service.get_active_rules()
        
        assert len(result) == 1
        assert result[0]["is_active"] is True


class TestChunkingServiceCreateRule:
    @pytest.mark.asyncio
    async def test_create_rule_success(self, chunking_service, mock_rule_repo):
        name = "New Rule"
        description = "A new chunking rule"
        rule_type = "heading"
        rule_config = {"levels": [1, 2, 3]}
        sort_order = 1
        created_by = "admin"
        
        mock_rule_repo.create.return_value = MagicMock(spec=ChunkingRule, id=uuid.uuid4())
        
        result = await chunking_service.create_rule(name, description, rule_type, rule_config, sort_order, created_by)
        
        assert result is not None
        mock_rule_repo.create.assert_called_once()


class TestChunkingServiceUpdateRule:
    @pytest.mark.asyncio
    async def test_update_rule_success(self, chunking_service, mock_rule_repo):
        rule_id = uuid.uuid4()
        mock_rule = MagicMock(spec=ChunkingRule)
        mock_rule.id = rule_id
        mock_rule.name = "Old Name"
        
        mock_rule_repo.get_by_id.return_value = mock_rule
        mock_rule_repo.update.return_value = mock_rule
        
        result = await chunking_service.update_rule(
            rule_id, "New Name", "Updated", "length", {"max_length": 200}, True
        )
        
        assert result is not None
        mock_rule_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_rule_not_found(self, chunking_service, mock_rule_repo):
        mock_rule_repo.get_by_id.return_value = None
        
        result = await chunking_service.update_rule(
            uuid.uuid4(), "Name", "", "heading", {}, True
        )
        
        assert result is None


class TestChunkingServiceDeleteRule:
    @pytest.mark.asyncio
    async def test_delete_rule_success(self, chunking_service, mock_rule_repo):
        rule_id = uuid.uuid4()
        mock_rule_repo.delete.return_value = True
        
        result = await chunking_service.delete_rule(rule_id)
        
        assert result is True
        mock_rule_repo.delete.assert_called_once_with(rule_id)

    @pytest.mark.asyncio
    async def test_delete_rule_failure(self, chunking_service, mock_rule_repo):
        mock_rule_repo.delete.return_value = False
        
        result = await chunking_service.delete_rule(uuid.uuid4())
        
        assert result is False


class TestChunkingServiceReorderRules:
    @pytest.mark.asyncio
    async def test_reorder_rules_success(self, chunking_service, mock_rule_repo):
        rule_orders = [
            {"id": str(uuid.uuid4()), "sort_order": 1},
            {"id": str(uuid.uuid4()), "sort_order": 2},
        ]
        
        result = await chunking_service.reorder_rules(rule_orders)
        
        assert result is True
        mock_rule_repo.update_order.assert_called_once_with(rule_orders)
