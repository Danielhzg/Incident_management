"""
TDD: Tests for the Redis Pub/Sub event flow.
Tests event publishing, subscribing, and handler dispatch.
"""
import asyncio
import json
import pytest
import pytest_asyncio
import redis.asyncio as aioredis

from app.events.contracts import (
    REDIS_CHANNEL,
    IncidentCreatedEvent,
    IncidentAcknowledgedEvent,
    IncidentResolvedEvent,
    IncidentEscalatedEvent,
)


@pytest_asyncio.fixture
async def redis_client():
    """Create a test Redis client."""
    client = aioredis.from_url("redis://redis:6379/2", decode_responses=True)
    yield client
    await client.flushdb()
    await client.close()


@pytest.mark.asyncio
async def test_event_serialization():
    """Test that events serialize to valid JSON."""
    event = IncidentCreatedEvent(
        incident_id=1,
        title="Test Incident",
        severity="P1",
        status="open",
        source="manual",
    )

    json_str = event.model_dump_json()
    parsed = json.loads(json_str)

    assert parsed["event_type"] == "incident.created"
    assert parsed["incident_id"] == 1
    assert parsed["title"] == "Test Incident"
    assert parsed["severity"] == "P1"
    assert "timestamp" in parsed


@pytest.mark.asyncio
async def test_all_event_types_serialize():
    """Test that all event types can be serialized."""
    events = [
        IncidentCreatedEvent(incident_id=1, title="Test", severity="P1", status="open", source="manual"),
        IncidentAcknowledgedEvent(incident_id=1, engineer_id=1, engineer_email="a@b.com", engineer_name="A"),
        IncidentResolvedEvent(incident_id=1, resolver_id=1, resolver_email="a@b.com", resolver_name="A", resolution_notes="Fixed"),
        IncidentEscalatedEvent(incident_id=1, title="Test", severity="P1", from_tier=1, to_tier=2),
    ]

    for event in events:
        json_str = event.model_dump_json()
        parsed = json.loads(json_str)
        assert "event_type" in parsed
        assert "timestamp" in parsed
        assert "incident_id" in parsed


@pytest.mark.asyncio
async def test_pubsub_publish_receive(redis_client):
    """Test that published events are received by subscribers."""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL)

    # Publish an event
    event = IncidentCreatedEvent(
        incident_id=42,
        title="DB Connection Pool Exhausted",
        severity="P1",
        status="open",
        source="monitoring",
    )
    await redis_client.publish(REDIS_CHANNEL, event.model_dump_json())

    # Receive messages
    received = None
    for _ in range(10):  # Try up to 10 messages (first is subscribe confirmation)
        msg = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0), timeout=2.0)
        if msg and msg["type"] == "message":
            received = json.loads(msg["data"])
            break

    await pubsub.unsubscribe(REDIS_CHANNEL)
    await pubsub.close()

    assert received is not None, "Should have received the published event"
    assert received["incident_id"] == 42
    assert received["event_type"] == "incident.created"
    assert received["severity"] == "P1"


@pytest.mark.asyncio
async def test_event_channel_isolation(redis_client):
    """Test that events on different channels don't interfere."""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("events:other")

    # Publish to the incident channel (not subscribed)
    await redis_client.publish(REDIS_CHANNEL, '{"event_type": "incident.created", "incident_id": 1}')

    # Should NOT receive anything on the other channel
    msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
    assert msg is None, "Should not receive events from a different channel"

    await pubsub.unsubscribe("events:other")
    await pubsub.close()
