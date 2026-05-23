import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date
from app.services.heatmap_service import HeatmapService


class TestHeatmapService:
    @pytest.mark.asyncio
    async def test_record_search(self):
        mock_search_repo = AsyncMock()
        mock_stats_repo = AsyncMock()
        
        with patch("app.services.heatmap_service.get_adapter"):
            with patch("app.services.heatmap_service.SearchEventRepository") as mock_search_repo_class:
                mock_search_repo_class.return_value = mock_search_repo
                
                with patch("app.services.heatmap_service.HeatmapStatsRepository") as mock_stats_repo_class:
                    mock_stats_repo_class.return_value = mock_stats_repo
                    
                    with patch("app.services.heatmap_service.get_redis") as mock_redis:
                        mock_redis_client = AsyncMock()
                        mock_redis.return_value = mock_redis_client
                        
                        service = HeatmapService()
                        
                        await service.record_search_event(
                            user_id="user1",
                            query="test query",
                            dept_id="dept1",
                        )
                        
                        assert mock_search_repo.create.called
                        assert mock_redis_client.hincrby.called

    @pytest.mark.asyncio
    async def test_get_daily_stats(self):
        mock_stats_repo = AsyncMock()
        mock_stats_repo.get_by_type_and_date.return_value = [
            MagicMock(stat_key="query1", count=10, unique_users=5, avg_duration_ms=100),
            MagicMock(stat_key="query2", count=5, unique_users=3, avg_duration_ms=150),
        ]
        
        with patch("app.services.heatmap_service.get_adapter"):
            with patch("app.services.heatmap_service.SearchEventRepository"):
                with patch("app.services.heatmap_service.HeatmapStatsRepository") as mock_stats_repo_class:
                    mock_stats_repo_class.return_value = mock_stats_repo
                    
                    with patch("app.services.heatmap_service.get_redis"):
                        service = HeatmapService()
                        
                        result = await service.get_daily_stats(date(2024, 1, 1))
                        
                        assert len(result) == 2
                        assert "query1" in result
                        assert result["query1"]["count"] == 10
                        assert "query2" in result
                        assert result["query2"]["count"] == 5

    @pytest.mark.asyncio
    async def test_aggregate_daily_stats(self):
        mock_stats_repo = AsyncMock()
        mock_stats_repo.get_by_type_key_date.return_value = None
        
        with patch("app.services.heatmap_service.get_adapter"):
            with patch("app.services.heatmap_service.SearchEventRepository"):
                with patch("app.services.heatmap_service.HeatmapStatsRepository") as mock_stats_repo_class:
                    mock_stats_repo_class.return_value = mock_stats_repo
                    
                    with patch("app.services.heatmap_service.get_redis") as mock_redis:
                        mock_redis_client = AsyncMock()
                        mock_redis_client.hgetall.return_value = {"query1": "10", "query2": "5"}
                        mock_redis.return_value = mock_redis_client
                        
                        service = HeatmapService()
                        
                        await service.aggregate_daily_stats()
                        
                        assert mock_stats_repo.create.called
                        assert mock_redis_client.delete.called
