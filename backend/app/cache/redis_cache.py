"""
Redis caching layer for read-heavy endpoints.
Supports TTL-based caching with event-driven invalidation.
"""
import json
import hashlib
from typing import Any

import structlog
import redis.asyncio as aioredis

from app.config import get_settings
from app.events.contracts import EventType
from app.events.subscriber import register_handler

logger = structlog.get_logger(__name__)
settings = get_settings()

_cache_client: aioredis.Redis | None = None

CACHE_PREFIX = "cache:"
DEFAULT_TTL = 300  # 5 minutes


async def get_cache_client() -> aioredis.Redis:
    """Get or create the Redis cache client."""
    global _cache_client
    if _cache_client is None:
        _cache_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            db=1,  # Use db 1 for cache (db 0 for pub/sub + locks)
        )
    return _cache_client


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a deterministic cache key from function arguments."""
    key_data = f"{prefix}:{json.dumps(args, default=str)}:{json.dumps(kwargs, default=str, sort_keys=True)}"
    key_hash = hashlib.md5(key_data.encode()).hexdigest()
    return f"{CACHE_PREFIX}{prefix}:{key_hash}"


async def cache_get(key: str) -> Any | None:
    """Get a value from cache."""
    client = await get_cache_client()
    data = await client.get(key)
    if data:
        await logger.adebug("Cache hit", key=key)
        return json.loads(data)
    await logger.adebug("Cache miss", key=key)
    return None


async def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL):
    """Set a value in cache with TTL."""
    client = await get_cache_client()
    await client.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(key: str):
    """Delete a specific cache key."""
    client = await get_cache_client()
    await client.delete(key)


async def cache_invalidate_pattern(pattern: str):
    """Invalidate all cache keys matching a pattern."""
    client = await get_cache_client()
    cursor = 0
    deleted = 0
    while True:
        cursor, keys = await client.scan(cursor, match=f"{CACHE_PREFIX}{pattern}*", count=100)
        if keys:
            await client.delete(*keys)
            deleted += len(keys)
        if cursor == 0:
            break

    if deleted > 0:
        await logger.ainfo("Cache invalidated", pattern=pattern, keys_deleted=deleted)


# === Event-driven cache invalidation ===

async def handle_incident_change(data: dict):
    """Invalidate incident-related caches when incidents change."""
    await cache_invalidate_pattern("incidents")
    await cache_invalidate_pattern("stats")
    await cache_invalidate_pattern("analytics")


def register_cache_handlers():
    """Register cache invalidation handlers."""
    register_handler(EventType.INCIDENT_CREATED, handle_incident_change)
    register_handler(EventType.INCIDENT_ACKNOWLEDGED, handle_incident_change)
    register_handler(EventType.INCIDENT_RESOLVED, handle_incident_change)
    register_handler(EventType.INCIDENT_ESCALATED, handle_incident_change)
    register_handler(EventType.INCIDENT_UPDATED, handle_incident_change)
    logger.info("Cache invalidation handlers registered")


async def close_cache():
    """Close the cache client connection."""
    global _cache_client
    if _cache_client:
        await _cache_client.close()
        _cache_client = None
