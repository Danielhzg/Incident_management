"""
TDD: Tests for Redis-based optimistic locking (SET NX).
Tests the race condition handling for concurrent incident acknowledgement.
"""
import asyncio
import pytest
import pytest_asyncio
import redis.asyncio as aioredis


@pytest_asyncio.fixture
async def redis_client():
    """Create a test Redis client."""
    client = aioredis.from_url("redis://redis:6379/2", decode_responses=True)
    yield client
    # Cleanup
    await client.flushdb()
    await client.close()


@pytest.mark.asyncio
async def test_set_nx_atomic_lock(redis_client):
    """Test that SET NX provides atomic locking — only one writer wins."""
    lock_key = "incident:lock:test_1"

    # First attempt should succeed
    result1 = await redis_client.set(lock_key, "engineer_a@test.com", nx=True, ex=60)
    assert result1 is True, "First SET NX should succeed"

    # Second attempt should fail (key already exists)
    result2 = await redis_client.set(lock_key, "engineer_b@test.com", nx=True, ex=60)
    assert result2 is None, "Second SET NX should fail (lock already held)"

    # Verify the original holder is preserved
    holder = await redis_client.get(lock_key)
    assert holder == "engineer_a@test.com", "Lock should be held by first engineer"


@pytest.mark.asyncio
async def test_concurrent_acknowledge_race(redis_client):
    """
    Simulate two engineers acknowledging the same incident simultaneously.
    Only one should succeed due to Redis SET NX atomicity.
    """
    lock_key = "incident:lock:test_2"
    results = {}

    async def try_acknowledge(engineer_email: str):
        acquired = await redis_client.set(lock_key, engineer_email, nx=True, ex=60)
        results[engineer_email] = acquired

    # Run both concurrently
    await asyncio.gather(
        try_acknowledge("engineer_a@test.com"),
        try_acknowledge("engineer_b@test.com"),
    )

    # Exactly one should succeed
    successes = [email for email, result in results.items() if result]
    failures = [email for email, result in results.items() if not result]

    assert len(successes) == 1, f"Exactly one engineer should win the lock, got {len(successes)}"
    assert len(failures) == 1, f"Exactly one engineer should fail, got {len(failures)}"

    # Verify the winner holds the lock
    holder = await redis_client.get(lock_key)
    assert holder == successes[0], "Lock holder should match the winner"


@pytest.mark.asyncio
async def test_lock_expiry(redis_client):
    """Test that lock expires after TTL (safety net)."""
    lock_key = "incident:lock:test_3"

    # Set with 1 second TTL
    await redis_client.set(lock_key, "engineer@test.com", nx=True, ex=1)

    # Immediately, lock should exist
    assert await redis_client.get(lock_key) is not None

    # Wait for expiry
    await asyncio.sleep(1.1)

    # Lock should be gone
    assert await redis_client.get(lock_key) is None

    # Another engineer should now be able to acquire
    result = await redis_client.set(lock_key, "engineer2@test.com", nx=True, ex=60)
    assert result is True


@pytest.mark.asyncio
async def test_lock_release_on_resolve(redis_client):
    """Test that lock is cleaned up when incident is resolved."""
    lock_key = "incident:lock:test_4"

    # Acquire lock
    await redis_client.set(lock_key, "engineer@test.com", nx=True, ex=3600)
    assert await redis_client.get(lock_key) is not None

    # Simulate resolve — delete the lock
    await redis_client.delete(lock_key)
    assert await redis_client.get(lock_key) is None


@pytest.mark.asyncio
async def test_multiple_incidents_independent_locks(redis_client):
    """Test that locks for different incidents are independent."""
    lock_key_1 = "incident:lock:test_5"
    lock_key_2 = "incident:lock:test_6"

    # Lock incident 1
    result1 = await redis_client.set(lock_key_1, "engineer_a@test.com", nx=True, ex=60)
    assert result1 is True

    # Lock incident 2 with different engineer — should succeed
    result2 = await redis_client.set(lock_key_2, "engineer_b@test.com", nx=True, ex=60)
    assert result2 is True

    # Try to lock incident 1 again — should fail
    result3 = await redis_client.set(lock_key_1, "engineer_c@test.com", nx=True, ex=60)
    assert result3 is None
