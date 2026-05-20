import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MemoryCache:
    """内存缓存（Redis 不可用时的降级方案）"""

    def __init__(self):
        self._store: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str) -> str | None:
        item = self._store.get(key)
        if item is None:
            return None
        value, expire_at = item
        if expire_at and expire_at < __import__("time").time():
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: str, ex: int | None = None):
        expire_at = __import__("time").time() + ex if ex else None
        self._store[key] = (value, expire_at)

    async def delete(self, key: str):
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def ping(self) -> bool:
        return True

    async def close(self):
        pass


class RedisCache:
    """Redis 缓存"""

    def __init__(self, url: str):
        import redis.asyncio as aioredis
        self._redis = aioredis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        await self._redis.set(key, value, ex=ex)

    async def delete(self, key: str):
        await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._redis.exists(key)

    async def ping(self) -> bool:
        try:
            return await self._redis.ping()
        except Exception:
            return False

    async def close(self):
        await self._redis.close()


_cache = None


async def get_cache() -> MemoryCache | RedisCache:
    """获取缓存实例，优先使用 Redis，不可用时降级为内存缓存"""
    global _cache
    if _cache is not None:
        return _cache

    from app.config import get_settings
    settings = get_settings()

    if settings.REDIS_URL:
        try:
            _cache = RedisCache(settings.REDIS_URL)
            if await _cache.ping():
                logger.info("Cache: Redis connected")
                return _cache
            else:
                logger.warning("Redis ping failed, falling back to memory cache")
                await _cache.close()
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}), using memory cache")

    _cache = MemoryCache()
    logger.info("Cache: using in-memory cache")
    return _cache


async def close_cache():
    global _cache
    if _cache:
        await _cache.close()
        _cache = None
