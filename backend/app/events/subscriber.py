"""
Redis Pub/Sub subscriber — listens for events and routes to handlers.
Runs as a background asyncio task during app lifetime.
"""
import asyncio
import json
import structlog
import redis.asyncio as aioredis

from app.config import get_settings
from app.events.contracts import REDIS_CHANNEL, EventType

logger = structlog.get_logger(__name__)

# Event handler registry
_handlers: dict[EventType, list] = {}


def register_handler(event_type: EventType, handler):
    """Register an async handler for an event type."""
    if event_type not in _handlers:
        _handlers[event_type] = []
    _handlers[event_type].append(handler)
    return handler


async def _dispatch_event(raw_data: str):
    """Parse event and dispatch to registered handlers."""
    try:
        data = json.loads(raw_data)
        event_type_str = data.get("event_type")
        if not event_type_str:
            await logger.awarning("Event missing event_type field", data=data)
            return

        try:
            event_type = EventType(event_type_str)
        except ValueError:
            await logger.awarning("Unknown event type", event_type=event_type_str)
            return

        handlers = _handlers.get(event_type, [])
        if not handlers:
            await logger.ainfo("No handlers for event", event_type=event_type_str)
            return

        await logger.ainfo(
            "Dispatching event",
            event_type=event_type_str,
            handler_count=len(handlers),
        )

        # Run all handlers concurrently
        await asyncio.gather(
            *[handler(data) for handler in handlers],
            return_exceptions=True,
        )

    except json.JSONDecodeError as e:
        await logger.aerror("Failed to decode event JSON", error=str(e))
    except Exception as e:
        await logger.aerror("Error dispatching event", error=str(e))


async def start_subscriber():
    """
    Start the Redis Pub/Sub subscriber loop.
    This runs as a background task for the lifetime of the app.
    """
    settings = get_settings()
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = client.pubsub()

    await pubsub.subscribe(REDIS_CHANNEL)
    await logger.ainfo("Subscriber started", channel=REDIS_CHANNEL)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await _dispatch_event(message["data"])
    except asyncio.CancelledError:
        await logger.ainfo("Subscriber cancelled, shutting down")
    except Exception as e:
        await logger.aerror("Subscriber error", error=str(e))
    finally:
        await pubsub.unsubscribe(REDIS_CHANNEL)
        await pubsub.close()
        await client.close()
        await logger.ainfo("Subscriber stopped")
