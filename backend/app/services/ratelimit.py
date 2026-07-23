"""Rate-limit: фейк-аккаунт, brute-force және API-абьюз тосқауылы.

Fixed-window алгоритмі: терезе ішіндегі сұраныс саны лимиттен асса - 429.
- InMemoryLimiter: dev, бір процесс ішінде (Redis керек емес)
- RedisLimiter: прод, барлық worker бір санауышты бөліседі
- NoopLimiter: тест-орта (тесттер бір-бірін лимиттемейді)
"""

import time
from functools import lru_cache

from app.core.config import get_settings

MAX_TRACKED_BUCKETS = 10_000


class NoopLimiter:
    async def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, tuple[int, int]] = {}

    async def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        window_id = int(time.time() // window_seconds)
        previous_window, count = self._buckets.get(key, (window_id, 0))
        if previous_window != window_id:
            count = 0
        count += 1
        if len(self._buckets) > MAX_TRACKED_BUCKETS:
            self._buckets.clear()
        self._buckets[key] = (window_id, count)
        return count <= limit


class RedisLimiter:
    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as redis

        self._redis = redis.from_url(redis_url)

    async def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        redis_key = f"ratelimit:{key}"
        count = await self._redis.incr(redis_key)
        if count == 1:
            await self._redis.expire(redis_key, window_seconds)
        return count <= limit


Limiter = NoopLimiter | InMemoryLimiter | RedisLimiter


@lru_cache
def get_limiter() -> Limiter:
    settings = get_settings()
    if settings.environment == "test":
        return NoopLimiter()
    if settings.rate_limit_backend == "redis":
        return RedisLimiter(settings.redis_url)
    return InMemoryLimiter()
