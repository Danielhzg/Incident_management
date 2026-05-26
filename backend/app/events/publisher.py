"""
Redis Pub/Sub publisher — publishes events to the event bus.
"""
import structlog
import redis.asyncio as aioredis

from app.config import get_settings
from app.events.contracts import BaseEvent, REDIS_CHANNEL

logger = structlog.get_logger(__name__)

_redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """Get or create the Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


async def publish_event(event: BaseEvent) -> int:
    """
    Publish an event to the Redis Pub/Sub channel.
    Returns the number of subscribers that received the message.
    """
    client = await get_redis_client()
    payload = event.model_dump_json()

    subscribers = await client.publish(REDIS_CHANNEL, payload)
    await logger.ainfo(
        "Event published",
        event_type=event.event_type.value,
        channel=REDIS_CHANNEL,
        subscribers=subscribers,
    )
    return subscribers


async def close_publisher():
    """Close the Redis publisher connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
