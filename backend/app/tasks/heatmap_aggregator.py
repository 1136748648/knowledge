import logging
from datetime import date, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import AsyncSessionLocal
from app.models.heatmap import SearchEvent, HeatmapStats

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def aggregate_heatmap_stats():
    logger.info("Starting heatmap aggregation...")
    
    async with AsyncSessionLocal() as db:
        redis = await get_redis()
        today = date.today()
        
        try:
            queries = await redis.zrevrange("heatmap:queries:24h", 0, 99, withscores=True)
            for query, count in queries:
                stmt = select(HeatmapStats).where(
                    HeatmapStats.stat_type == "query",
                    HeatmapStats.stat_key == query,
                    HeatmapStats.stat_date == today,
                )
                result = await db.execute(stmt)
                stat = result.scalar_one_or_none()
                
                if stat:
                    stat.count = int(count)
                else:
                    stat = HeatmapStats(
                        stat_type="query",
                        stat_key=query,
                        stat_date=today,
                        count=int(count),
                    )
                    db.add(stat)
            
            docs = await redis.zrevrange("heatmap:documents:24h", 0, 99, withscores=True)
            for doc_id, count in docs:
                stmt = select(HeatmapStats).where(
                    HeatmapStats.stat_type == "document",
                    HeatmapStats.stat_key == doc_id,
                    HeatmapStats.stat_date == today,
                )
                result = await db.execute(stmt)
                stat = result.scalar_one_or_none()
                
                if stat:
                    stat.count = int(count)
                else:
                    stat = HeatmapStats(
                        stat_type="document",
                        stat_key=doc_id,
                        stat_date=today,
                        count=int(count),
                    )
                    db.add(stat)
            
            await db.commit()
            logger.info("Heatmap aggregation completed")
            
        except Exception as e:
            logger.error(f"Heatmap aggregation failed: {e}")
            await db.rollback()


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
