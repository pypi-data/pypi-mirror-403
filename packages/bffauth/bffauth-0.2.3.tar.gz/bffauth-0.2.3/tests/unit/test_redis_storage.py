"""
Tests for Redis storage backends.

Uses mock Redis client to test without requiring actual Redis server.
"""

from datetime import timedelta

import pytest
from cryptography.fernet import Fernet

from bffauth.core.models import OAuthProvider, SessionData, TokenRecord, utc_now
from bffauth.core.vault import TokenVault
from bffauth.storage.redis import RedisSessionStorage, RedisVaultStorage


class MockRedisClient:
    """Mock async Redis client for testing."""

    def __init__(self):
        self._data: dict[str, bytes] = {}
        self._ttls: dict[str, int] = {}

    async def get(self, name: str) -> bytes | None:
        return self._data.get(name)

    async def set(self, name: str, value: bytes, ex: int | None = None) -> bool | None:
        self._data[name] = value
        if ex is not None:
            self._ttls[name] = ex
        return True

    async def setex(self, name: str, time: int, value: bytes) -> bool | None:
        self._data[name] = value
        self._ttls[name] = time
        return True

    async def delete(self, *names: str) -> int:
        count = 0
        for name in names:
            if name in self._data:
                del self._data[name]
                self._ttls.pop(name, None)
                count += 1
        return count

    async def exists(self, *names: str) -> int:
        return sum(1 for name in names if name in self._data)

    async def keys(self, pattern: str) -> list[bytes]:
        # Simple pattern matching (only supports prefix*)
        prefix = pattern.rstrip("*")
        return [k.encode() for k in self._data.keys() if k.startswith(prefix)]

    async def ttl(self, name: str) -> int:
        if name not in self._data:
            return -2
        return self._ttls.get(name, -1)


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    return MockRedisClient()


@pytest.fixture
def session_storage(mock_redis):
    """Create Redis session storage with mock client."""
    return RedisSessionStorage(mock_redis, key_prefix="test:session:")


@pytest.fixture
def vault_storage(mock_redis):
    """Create Redis vault storage with mock client."""
    return RedisVaultStorage(mock_redis, key_prefix="test:vault:")


@pytest.fixture
def valid_session():
    """Create a valid session."""
    now = utc_now()
    return SessionData(
        session_id="test-session-id-12345678901234567890",
        csrf_token="csrf-token-12345678901234567890123456",
        created_at=now,
        last_activity=now,
        expires_at=now + timedelta(hours=24),
        user_id="user-123",
        user_info={"email": "test@example.com"},
        metadata={"ip": "127.0.0.1"},
    )


@pytest.fixture
def expired_session():
    """Create an expired session."""
    now = utc_now()
    return SessionData(
        session_id="expired-session-id-123456789012345",
        csrf_token="csrf-token-12345678901234567890123456",
        created_at=now - timedelta(hours=48),
        last_activity=now - timedelta(hours=48),
        expires_at=now - timedelta(hours=24),
        user_id="user-456",
    )


@pytest.fixture
def encryption_key():
    """Generate valid Fernet key."""
    return Fernet.generate_key().decode()


class TestRedisSessionStorage:
    """Tests for RedisSessionStorage."""

    @pytest.mark.asyncio
    async def test_set_and_get_session(self, session_storage, valid_session):
        """Should store and retrieve session."""
        await session_storage.set(valid_session)
        retrieved = await session_storage.get(valid_session.session_id)

        assert retrieved is not None
        assert retrieved.session_id == valid_session.session_id
        assert retrieved.user_id == valid_session.user_id
        assert retrieved.csrf_token == valid_session.csrf_token

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_storage):
        """Should return None for nonexistent session."""
        result = await session_storage.get("nonexistent-session-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_expired_session(self, session_storage, expired_session):
        """Should return None and delete expired session."""
        # Manually store expired session
        await session_storage.set(expired_session)
        result = await session_storage.get(expired_session.session_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_session(self, session_storage, valid_session):
        """Should delete existing session."""
        await session_storage.set(valid_session)
        result = await session_storage.delete(valid_session.session_id)
        assert result is True

        retrieved = await session_storage.get(valid_session.session_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, session_storage):
        """Should return False for nonexistent session."""
        result = await session_storage.delete("nonexistent-session-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_custom_key_prefix(self, mock_redis):
        """Should use custom key prefix."""
        storage = RedisSessionStorage(mock_redis, key_prefix="myapp:sessions:")
        now = utc_now()
        session = SessionData(
            session_id="prefix-test-session-1234567890123",
            csrf_token="csrf-token-12345678901234567890123456",
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=1),
        )
        await storage.set(session)

        # Verify key format
        assert "myapp:sessions:prefix-test-session-1234567890123" in mock_redis._data

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, session_storage, valid_session, mock_redis):
        """Should set TTL based on session expiration."""
        await session_storage.set(valid_session)
        key = f"test:session:{valid_session.session_id}"
        assert key in mock_redis._ttls
        assert mock_redis._ttls[key] > 0

    @pytest.mark.asyncio
    async def test_set_expired_session_not_stored(
        self, session_storage, expired_session, mock_redis
    ):
        """Should not store already-expired session."""
        await session_storage.set(expired_session)
        key = f"test:session:{expired_session.session_id}"
        assert key not in mock_redis._data

    @pytest.mark.asyncio
    async def test_cleanup_expired(
        self, session_storage, valid_session, expired_session
    ):
        """Should clean up expired sessions."""
        # Store both sessions (bypass expiration check for testing)
        session_storage._redis._data[f"test:session:{valid_session.session_id}"] = (
            valid_session.model_dump_json().encode()
        )
        session_storage._redis._data[f"test:session:{expired_session.session_id}"] = (
            expired_session.model_dump_json().encode()
        )

        removed = await session_storage.cleanup_expired()
        assert removed == 1

        # Valid session should remain
        assert await session_storage.get(valid_session.session_id) is not None

    @pytest.mark.asyncio
    async def test_extend_session(self, session_storage, valid_session):
        """Should extend session expiration."""
        await session_storage.set(valid_session)
        original_expires = valid_session.expires_at

        result = await session_storage.extend_session(
            valid_session.session_id,
            timedelta(hours=48),
        )
        assert result is True

        updated = await session_storage.get(valid_session.session_id)
        assert updated is not None
        assert updated.expires_at > original_expires

    @pytest.mark.asyncio
    async def test_extend_nonexistent_session(self, session_storage):
        """Should return False for nonexistent session."""
        result = await session_storage.extend_session(
            "nonexistent-session-id",
            timedelta(hours=1),
        )
        assert result is False


class TestRedisVaultStorage:
    """Tests for RedisVaultStorage."""

    @pytest.mark.asyncio
    async def test_set_and_get_vault(self, vault_storage):
        """Should store and retrieve vault data."""
        session_id = "vault-test-session-12345678901234"
        data = b"encrypted-vault-data-here"

        await vault_storage.set(session_id, data)
        retrieved = await vault_storage.get(session_id)

        assert retrieved == data

    @pytest.mark.asyncio
    async def test_get_nonexistent_vault(self, vault_storage):
        """Should return None for nonexistent vault."""
        result = await vault_storage.get("nonexistent-session-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_vault(self, vault_storage):
        """Should delete existing vault."""
        session_id = "delete-test-session-123456789012"
        await vault_storage.set(session_id, b"data")

        result = await vault_storage.delete(session_id)
        assert result is True

        retrieved = await vault_storage.get(session_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_vault(self, vault_storage):
        """Should return False for nonexistent vault."""
        result = await vault_storage.delete("nonexistent-session-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, vault_storage):
        """Should check vault existence."""
        session_id = "exists-test-session-123456789012"

        assert await vault_storage.exists(session_id) is False

        await vault_storage.set(session_id, b"data")
        assert await vault_storage.exists(session_id) is True

    @pytest.mark.asyncio
    async def test_custom_key_prefix(self, mock_redis):
        """Should use custom key prefix."""
        storage = RedisVaultStorage(mock_redis, key_prefix="myapp:vaults:")
        session_id = "prefix-vault-test-12345678901234"
        await storage.set(session_id, b"data")

        assert f"myapp:vaults:{session_id}" in mock_redis._data

    @pytest.mark.asyncio
    async def test_default_ttl(self, vault_storage, mock_redis):
        """Should set default TTL."""
        session_id = "ttl-test-session-1234567890123456"
        await vault_storage.set(session_id, b"data")

        key = f"test:vault:{session_id}"
        assert mock_redis._ttls.get(key) == 86400  # 24 hours default

    @pytest.mark.asyncio
    async def test_no_ttl(self, mock_redis):
        """Should not set TTL when default_ttl is None."""
        storage = RedisVaultStorage(mock_redis, default_ttl=None)
        session_id = "no-ttl-test-session-12345678901"
        await storage.set(session_id, b"data")

        key = f"bffauth:vault:{session_id}"
        assert key not in mock_redis._ttls

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, vault_storage, mock_redis):
        """Should set custom TTL."""
        session_id = "custom-ttl-session-12345678901"
        await vault_storage.set_with_ttl(session_id, b"data", ttl=3600)

        key = f"test:vault:{session_id}"
        assert mock_redis._ttls.get(key) == 3600

    @pytest.mark.asyncio
    async def test_get_ttl(self, vault_storage, mock_redis):
        """Should get remaining TTL."""
        session_id = "get-ttl-session-1234567890123456"

        # Nonexistent key
        assert await vault_storage.get_ttl(session_id) == -2

        # Key with TTL
        await vault_storage.set(session_id, b"data")
        ttl = await vault_storage.get_ttl(session_id)
        assert ttl == 86400


class TestRedisStorageIntegration:
    """Integration tests using Redis storage with actual components."""

    @pytest.mark.asyncio
    async def test_token_vault_with_redis_storage(self, vault_storage, encryption_key):
        """Should work with TokenVault."""
        vault = TokenVault(encryption_key=encryption_key, storage=vault_storage)

        session_id = "integration-test-session-1234567"
        now = utc_now()
        token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="access-token-12345",
            refresh_token="refresh-token-67890",
            expires_at=now + timedelta(hours=1),
            issued_at=now,
        )

        await vault.store_token(session_id, token)
        retrieved = await vault.get_token(session_id, OAuthProvider.GOOGLE)

        assert retrieved.access_token == token.access_token
        assert retrieved.refresh_token == token.refresh_token

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, session_storage):
        """Should handle multiple sessions correctly."""
        now = utc_now()
        sessions = [
            SessionData(
                session_id=f"multi-session-{i}-12345678901234567",
                csrf_token=f"csrf-{i}-12345678901234567890123456",
                created_at=now,
                last_activity=now,
                expires_at=now + timedelta(hours=24),
                user_id=f"user-{i}",
            )
            for i in range(5)
        ]

        for session in sessions:
            await session_storage.set(session)

        for session in sessions:
            retrieved = await session_storage.get(session.session_id)
            assert retrieved is not None
            assert retrieved.user_id == session.user_id

    @pytest.mark.asyncio
    async def test_session_update(self, session_storage, valid_session):
        """Should update session data correctly."""
        await session_storage.set(valid_session)

        # Update session
        valid_session.user_info["name"] = "Updated Name"
        valid_session.touch()
        await session_storage.set(valid_session)

        retrieved = await session_storage.get(valid_session.session_id)
        assert retrieved is not None
        assert retrieved.user_info.get("name") == "Updated Name"
