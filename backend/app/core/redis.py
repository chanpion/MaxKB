"""Async Redis client (cache + arq broker/result backend).

Mirrors the legacy django-redis configuration. Sentinel topology is parsed from
MAXKB_REDIS_SENTINEL_* in config.py but, for simplicity, the single-node client
is used here; swap to a Sentinel connection if your deployment requires it.
"""

from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()

redis_client: Redis = Redis.from_url(
    settings.redis_url,
    max_connections=settings.redis_max_connections,
    decode_responses=True,
    health_check_interval=30,
)
