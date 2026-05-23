import logging
from datetime import date, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.redis import get_redis
from app.dal import HeatmapStatsRepository, get_adapter

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def aggregate_heatmap_stats():
    logger.info("Starting heatmap aggregation...")
    
    adapter = get_adapter()
    repo = HeatmapStatsRepository(adapter)
    redis = await get_redis()
    today = date.today()
    
    try:
        queries = await redis.zrevrange("heatmap:queries:24h", 0, 99, withscores=True)
        for query, count in queries:
            stat = await repo.get_by_type_key_date("query", query, today)
            
            if stat:
                stat.count = int(count)
                await repo.update(stat)
            else:
                from app.models.heatmap import HeatmapStats
                stat = HeatmapStats(
                    stat_type="query",
                    stat_key=query,
                    stat_date=today,
                    count=int(count),
                )
                await repo.create(stat)
        
        docs = await redis.zrevrange("heatmap:documents:24h", 0, 99, withscores=True)
        for doc_id, count in docs:
            stat = await repo.get_by_type_key_date("document", doc_id, today)
            
            if stat:
                stat.count = int(count)
                await repo.update(stat)
            else:
                from app.models.heatmap import HeatmapStats
                stat = HeatmapStats(
                    stat_type="document",
                    stat_key=doc_id,
                    stat_date=today,
                    count=int(count),
                )
                await repo.create(stat)
        
        logger.info("Heatmap aggregation completed")
        
    except Exception as e:
        logger.error(f"Heatmap aggregation failed: {e}")


def start_scheduler():
    from app.config import get_settings
    settings = get_settings()
    
    scheduler.add_job(
        aggregate_heatmap_stats,
        'interval',
        minutes=settings.HEATMAP_AGGREGATE_INTERVAL,
        id='heatmap_aggregator',
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Heatmap scheduler started")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("Heatmap scheduler stopped")
