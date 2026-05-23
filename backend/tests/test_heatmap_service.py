import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date
from app.services.heatmap_service import HeatmapService


class TestHeatmapService:
    @pytest.mark.asyncio
    async def test_record_search(self):
        mock_search_repo = AsyncMock()
        mock_stats_repo = AsyncMock()
        
        with patch("app.services.heatmap_service.get_redis") as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            service = HeatmapService(mock_search_repo, mock_stats_repo)
            
            await service.record_search_event(
                user_id="user1",
                query="test query",
                dept_id="dept1",
            )
            
            assert mock_search_repo.create.called
            assert mock_redis_client.hincrby.called

    @pytest.mark.asyncio
    async def test_get_hot_queries(self):
        mock_search_repo = AsyncMock()
        mock_stats_repo = AsyncMock()
        
        with patch("app.services.heatmap_service.get_redis") as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.hgetall.return_value = {b"query1": b"10", b"query2": b"5"}
            mock_redis.return_value = mock_redis_client
            
            service = HeatmapService(mock_search_repo, mock_stats_repo)
            
            result = await service.get_hot_queries(time_range="24h", limit=10)
            
            assert len(result) == 2
            assert result[0]["query"] == "query1"
            assert result[0]["count"] == 10
            assert result[1]["query"] == "query2"
            assert result[1]["count"] == 5

    @pytest.mark.asyncio
    async def test_aggregate_daily_stats(self):
        mock_search_repo = AsyncMock()
        mock_stats_repo = AsyncMock()
        mock_stats_repo.get_by_type_key_date.return_value = None
        
        with patch("app.services.heatmap_service.get_redis") as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.hgetall.return_value = {b"query1": b"10", b"query2": b"5"}
            mock_redis.return_value = mock_redis_client
            
            service = HeatmapService(mock_search_repo, mock_stats_repo)
            
            await service.aggregate_daily_stats()
            
            assert mock_stats_repo.create.called
            assert mock_redis_client.delete.called