from fastapi import APIRouter, Query

from app.services.heatmap_service import HeatmapService

router = APIRouter(prefix="/api/heatmap", tags=["heatmap"])


@router.get("/queries")
async def get_hot_queries(
    time_range: str = Query("24h", regex="^(24h|7d|30d)$"),
    limit: int = Query(10, ge=1, le=50),
):
    service = HeatmapService()
    data = await service.get_hot_queries(time_range, limit)
    return {"time_range": time_range, "data": data, "updated_at": "now"}


@router.get("/documents")
async def get_hot_documents(
    time_range: str = Query("24h", regex="^(24h|7d|30d)$"),
    limit: int = Query(10, ge=1, le=50),
):
    service = HeatmapService()
    data = await service.get_hot_documents(time_range, limit)
    return {"time_range": time_range, "data": data}


@router.get("/timeline")
async def get_timeline(
    date: str | None = Query(None),
    granularity: str = Query("hour", regex="^(hour|day)$"),
):
    service = HeatmapService()
    return await service.get_timeline(date, granularity)


@router.get("/navigation")
async def get_navigation_heat():
    service = HeatmapService()
    data = await service.get_navigation_heat()
    return {"data": data}
