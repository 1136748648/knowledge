import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.heatmap_service import HeatmapService


class TestHeatmapService:
    @pytest.mark.asyncio
    async def test_record_search(self):
        mock_db = AsyncMock()
        service = HeatmapService(mock_db)
        
        with patch("app.services.heatmap_service.get_redis") as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            await service.record_search(
                query_text="test query",
                query_embedding=[0.1, 0.2],
                user_id="user1",
                dept_id="dept1",
                hit_docs=[{"id": "doc1", "score": 0.9}],
                filter_conditions={},
                duration_ms=100,
            )
            
            assert mock_db.add.called
            assert mock_db.commit.called
            assert mock_redis_client.zincrby.called

    @pytest.mark.asyncio
    async def test_get_hot_queries(self):
        mock_db = AsyncMock()
        service = HeatmapService(mock_db)
        
        with patch("app.services.heatmap_service.get_redis") as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.zrevrange.return_value = [("query1", 10), ("query2", 5)]
            mock_redis.return_value = mock_redis_client
            
            result = await service.get_hot_queries("24h", 10)
            
            assert len(result) == 2
            assert result[0]["query"] == "query1"
            assert result[0]["count"] == 10

    @pytest.mark.asyncio
    async def test_get_hot_documents(self):
        mock_db = AsyncMock()
        service = HeatmapService(mock_db)
        
        with patch("app.services.heatmap_service.get_redis") as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.zrevrange.return_value = [("doc1", 15), ("doc2", 8)]
            mock_redis.return_value = mock_redis_client
            
            result = await service.get_hot_documents("24h", 10)
            
            assert len(result) == 2
            assert result[0]["doc_id"] == "doc1"
            assert result[0]["hit_count"] == 15

    @pytest.mark.asyncio
    async def test_get_timeline(self):
        mock_db = AsyncMock()
        service = HeatmapService(mock_db)
        
        with patch("app.services.heatmap_service.get_redis") as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.get.return_value = "5"
            mock_redis.return_value = mock_redis_client
            
            result = await service.get_timeline("2026-05-23", "hour")
            
            assert result["date"] == "2026-05-23"
            assert result["granularity"] == "hour"
            assert len(result["data"]) == 24

    @pytest.mark.asyncio
    async def test_get_navigation_heat(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            MagicMock(stat_key="nav1", total_count=150),
            MagicMock(stat_key="nav2", total_count=80),
        ]
        mock_db.execute.return_value = mock_result
        
        service = HeatmapService(mock_db)
        result = await service.get_navigation_heat()
        
        assert len(result) == 2
        assert result[0]["node_id"] == "nav1"
        assert result[0]["hot_level"] == "hot"
