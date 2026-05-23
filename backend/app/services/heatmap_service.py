from datetime import date, datetime, timedelta

from app.dal import SearchEventRepository, HeatmapStatsRepository, get_adapter
from app.core.redis import get_redis


class HeatmapService:
    def __init__(self):
        adapter = get_adapter()
        self.search_event_repo = SearchEventRepository(adapter)
        self.stats_repo = HeatmapStatsRepository(adapter)
        self._redis_client = None
    
    async def get_redis_client(self):
        if self._redis_client is None:
            self._redis_client = await get_redis()
        return self._redis_client

    async def record_search_event(self, user_id: str, query: str, dept_id: str = None):
        from app.models.heatmap import SearchEvent

        event = SearchEvent(
            query_text=query,
            user_id=user_id,
            dept_id=dept_id,
            created_at=datetime.utcnow(),
        )
        await self.search_event_repo.create(event)

        redis_client = await self.get_redis_client()
        redis_key = f"heatmap:search:{date.today().isoformat()}"
        await redis_client.hincrby(redis_key, query, 1)
        await redis_client.expire(redis_key, 86400)

    async def get_daily_stats(self, stat_date: date) -> dict:
        stats = await self.stats_repo.get_by_type_and_date("search", stat_date)
        result = {}
        for stat in stats:
            result[stat.stat_key] = {
                "count": stat.count,
                "unique_users": stat.unique_users,
                "avg_duration_ms": stat.avg_duration_ms,
            }
        return result

    async def aggregate_daily_stats(self):
        yesterday = date.today() - timedelta(days=1)
        redis_key = f"heatmap:search:{yesterday.isoformat()}"

        redis_client = await self.get_redis_client()
        search_counts = await redis_client.hgetall(redis_key)
        if not search_counts:
            return

        from app.models.heatmap import HeatmapStats

        for query, count in search_counts.items():
            existing = await self.stats_repo.get_by_type_key_date("search", query, yesterday)
            if existing:
                existing.count += int(count)
                await self.stats_repo.update(existing)
            else:
                stat = HeatmapStats(
                    stat_type="search",
                    stat_key=query,
                    stat_date=yesterday,
                    count=int(count),
                )
                await self.stats_repo.create(stat)

        await redis_client.delete(redis_key)
