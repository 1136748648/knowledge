import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestHeatmapAPI:
    @pytest.mark.asyncio
    async def test_get_hot_queries(self, client):
        with patch("app.api.heatmap.HeatmapService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.get_hot_queries.return_value = [
                {"rank": 1, "query": "test", "count": 10, "trend": "stable"}
            ]
            mock_service.return_value = mock_instance
            
            response = await client.get("/api/heatmap/queries")
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert len(data["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_hot_documents(self, client):
        with patch("app.api.heatmap.HeatmapService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.get_hot_documents.return_value = [
                {"rank": 1, "doc_id": "doc1", "doc_title": "Document doc1", "doc_type": "wiki", "hit_count": 20, "avg_score": 0.9}
            ]
            mock_service.return_value = mock_instance
            
            response = await client.get("/api/heatmap/documents")
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert len(data["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_timeline(self, client):
        with patch("app.api.heatmap.HeatmapService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.get_timeline.return_value = {
                "date": "2026-05-23",
                "granularity": "hour",
                "data": [],
                "peak_hour": 0,
                "total_count": 0,
            }
            mock_service.return_value = mock_instance
            
            response = await client.get("/api/heatmap/timeline")
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data

    @pytest.mark.asyncio
    async def test_get_navigation_heat(self, client):
        with patch("app.api.heatmap.HeatmapService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.get_navigation_heat.return_value = [
                {"node_id": "nav1", "node_name": "Node nav1", "path": "/nav1", "hit_count": 100, "hot_level": "hot"}
            ]
            mock_service.return_value = mock_instance
            
            response = await client.get("/api/heatmap/navigation")
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert len(data["data"]) == 1
