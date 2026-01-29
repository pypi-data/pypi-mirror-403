"""
Pytest fixtures for integration tests.

These tests require a running Redis server on localhost:6379.
Start with: docker run -d --name bffauth-redis -p 6379:6379 redis:7-alpine
"""

import os

import pytest

# Try to import redis - it's an optional dependency
try:
    import redis.asyncio as aioredis

    REDIS_INSTALLED = True
except ImportError:
    aioredis = None  # type: ignore[assignment]
    REDIS_INSTALLED = False

# Skip all integration tests if Redis is not available
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


def is_redis_available() -> bool:
    """Check if Redis server is available (module installed and server running)."""
    if not REDIS_INSTALLED:
        return False

    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 6379))
        sock.close()
        return result == 0
    except Exception:
        return False


# Mark to skip if Redis not available
requires_redis = pytest.mark.skipif(
    not is_redis_available(),
    reason="Redis not available (module not installed or server not running)",
)


@pytest.fixture
async def redis_client():
    """Create async Redis client for tests."""
    if not REDIS_INSTALLED or aioredis is None:
        pytest.skip("redis module not installed")
    client = aioredis.Redis.from_url(REDIS_URL, decode_responses=False)
    yield client
    # Cleanup: flush test keys
    await client.flushdb()
    await client.aclose()


@pytest.fixture
def encryption_key():
    """Generate valid Fernet key."""
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode()
