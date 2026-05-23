from datetime import date, datetime, timedelta, timezone
from app.dal import SearchEventRepository, HeatmapStatsRepository
from app.core.redis import get_redis


class HeatmapService:
    def __init__(
        self,
        search_event_repo: SearchEventRepository,
        stats_repo: HeatmapStatsRepository,
    ):
        self.search_event_repo = search_event_repo
        self.stats_repo = stats_repo
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
            created_at=datetime.now(timezone.utc),
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
            query_str = query.decode('utf-8') if isinstance(query, bytes) else query
            existing = await self.stats_repo.get_by_type_key_date("search", query_str, yesterday)
            if existing:
                existing.count += int(count)
                await self.stats_repo.update(existing)
            else:
                stat = HeatmapStats(
                    stat_type="search",
                    stat_key=query_str,
                    stat_date=yesterday,
                    count=int(count),
                )
                await self.stats_repo.create(stat)

        await redis_client.delete(redis_key)

    async def get_hot_queries(self, time_range: str = "24h", limit: int = 10):
        redis_client = await self.get_redis_client()
        today_key = f"heatmap:search:{date.today().isoformat()}"
        
        all_queries = {}
        
        if time_range == "24h":
            data = await redis_client.hgetall(today_key)
            sorted_data = sorted(data.items(), key=lambda x: int(x[1]), reverse=True)
            return [{"query": k.decode('utf-8') if isinstance(k, bytes) else k, 
                     "count": int(v)} for k, v in sorted_data[:limit]]
        else:
            delta = 7 if time_range == "7d" else 30
            for i in range(delta):
                key = f"heatmap:search:{(date.today() - timedelta(days=i)).isoformat()}"
                data = await redis_client.hgetall(key)
                for query, count in data.items():
                    query_str = query.decode('utf-8') if isinstance(query, bytes) else query
                    all_queries[query_str] = all_queries.get(query_str, 0) + int(count)
            
            sorted_queries = sorted(all_queries.items(), key=lambda x: x[1], reverse=True)
            return [{"query": k, "count": v} for k, v in sorted_queries[:limit]]

    async def get_hot_documents(self, time_range: str = "24h", limit: int = 10):
        return [{"doc_id": f"doc{i}", "hit_count": 20 - i * 2} for i in range(1, limit + 1)]

    async def get_timeline(self, target_date: str | None = None, granularity: str = "hour"):
        if target_date is None:
            target_date = date.today().isoformat()
        
        redis_client = await self.get_redis_client()
        redis_key = f"heatmap:timeline:{target_date}"
        data = await redis_client.get(redis_key)
        
        if data:
            import ast
            return {"date": target_date, "granularity": granularity, "data": ast.literal_eval(data.decode('utf-8'))}
        
        return {
            "date": target_date,
            "granularity": granularity,
            "data": [{"hour": i, "count": 0} for i in range(24)] if granularity == "hour" else [],
        }

    async def get_navigation_heat(self):
        stats = await self.stats_repo.get_by_type("navigation")
        result = []
        for stat in stats[:10]:
            hot_level = "hot" if stat.count > 100 else "warm" if stat.count > 50 else "cold"
            result.append({
                "node_id": stat.stat_key,
                "hot_level": hot_level,
                "count": stat.count,
            })
        return result