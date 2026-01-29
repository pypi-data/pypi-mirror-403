"""
Integration tests for Redis storage backends.

These tests run against a real Redis server to validate that:
1. The Redis storage implementations work correctly with real Redis
2. The mock Redis client in unit tests behaves consistently with real Redis

Requires: docker run -d --name bffauth-redis -p 6379:6379 redis:7-alpine
"""

from datetime import timedelta

import pytest
from cryptography.fernet import Fernet

from bffauth.core.models import OAuthProvider, SessionData, TokenRecord, utc_now
from bffauth.core.session import SessionManager
from bffauth.core.vault import TokenVault
from bffauth.storage.redis import RedisSessionStorage, RedisVaultStorage

from .conftest import requires_redis


@requires_redis
class TestRedisSessionStorageIntegration:
    """Integration tests for RedisSessionStorage with real Redis."""

    @pytest.mark.asyncio
    async def test_session_lifecycle(self, redis_client):
        """Test complete session lifecycle: create, get, update, delete."""
        storage = RedisSessionStorage(redis_client, key_prefix="test:session:")
        manager = SessionManager(storage=storage, session_lifetime=timedelta(hours=1))

        # Create session
        session = await manager.create_session(
            user_id="user-123",
            user_info={"email": "test@example.com", "name": "Test User"},
            metadata={"ip": "192.168.1.1"},
        )
        assert session.session_id is not None
        assert session.user_id == "user-123"

        # Get session
        retrieved = await manager.get_session(session.session_id)
        assert retrieved.user_id == session.user_id
        assert retrieved.user_info["email"] == "test@example.com"

        # Update session
        session.user_info["verified"] = True
        await manager.update_session(session)
        updated = await manager.get_session(session.session_id)
        assert updated.user_info.get("verified") is True

        # Delete session
        result = await manager.delete_session(session.session_id)
        assert result is True

        # Verify deleted
        with pytest.raises(Exception):  # SessionNotFoundError
            await manager.get_session(session.session_id)

    @pytest.mark.asyncio
    async def test_session_expiration_with_ttl(self, redis_client):
        """Test that Redis TTL is set correctly based on session expiration."""
        storage = RedisSessionStorage(redis_client, key_prefix="test:session:")

        now = utc_now()
        session = SessionData(
            session_id="ttl-test-session-123456789012345",
            csrf_token="csrf-token-12345678901234567890123456",
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=1),
            user_id="user-ttl",
        )

        await storage.set(session)

        # Check TTL is set in Redis
        ttl = await storage.get_ttl(session.session_id)
        # TTL should be approximately 3600 seconds (1 hour), allow some margin
        assert 3500 < ttl <= 3600

    @pytest.mark.asyncio
    async def test_csrf_validation(self, redis_client):
        """Test CSRF token validation with real Redis."""
        storage = RedisSessionStorage(redis_client, key_prefix="test:session:")
        manager = SessionManager(storage=storage)

        session = await manager.create_session(user_id="csrf-test-user")
        csrf_token = session.csrf_token

        # Valid token
        result = await manager.validate_csrf(session.session_id, csrf_token)
        assert result is True

        # Invalid token
        with pytest.raises(Exception):  # CSRFValidationError
            await manager.validate_csrf(session.session_id, "wrong-token")

    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(self, redis_client):
        """Test handling multiple sessions concurrently."""
        storage = RedisSessionStorage(redis_client, key_prefix="test:session:")
        manager = SessionManager(storage=storage)

        # Create multiple sessions
        sessions = []
        for i in range(10):
            session = await manager.create_session(
                user_id=f"user-{i}",
                metadata={"session_number": i},
            )
            sessions.append(session)

        # Verify all sessions are retrievable
        for i, session in enumerate(sessions):
            retrieved = await manager.get_session(session.session_id)
            assert retrieved.user_id == f"user-{i}"
            assert retrieved.metadata["session_number"] == i

        # Delete all sessions
        for session in sessions:
            await manager.delete_session(session.session_id)

    @pytest.mark.asyncio
    async def test_extend_session(self, redis_client):
        """Test sliding session expiration."""
        storage = RedisSessionStorage(redis_client, key_prefix="test:session:")

        now = utc_now()
        session = SessionData(
            session_id="extend-test-session-1234567890123",
            csrf_token="csrf-token-12345678901234567890123456",
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=1),
            user_id="extend-user",
        )

        await storage.set(session)

        # Extend by 2 hours
        result = await storage.extend_session(session.session_id, timedelta(hours=2))
        assert result is True

        # Verify new TTL
        ttl = await storage.get_ttl(session.session_id)
        # Should be approximately 7200 seconds (2 hours)
        assert 7100 < ttl <= 7200


@requires_redis
class TestRedisVaultStorageIntegration:
    """Integration tests for RedisVaultStorage with real Redis."""

    @pytest.mark.asyncio
    async def test_token_lifecycle(self, redis_client, encryption_key):
        """Test complete token lifecycle: store, get, update, delete."""
        storage = RedisVaultStorage(redis_client, key_prefix="test:vault:")
        vault = TokenVault(encryption_key=encryption_key, storage=storage)

        session_id = "vault-test-session-123456789012"
        now = utc_now()

        # Store token
        token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="access-token-12345",
            refresh_token="refresh-token-67890",
            expires_at=now + timedelta(hours=1),
            issued_at=now,
            scope="openid profile email",
        )
        await vault.store_token(session_id, token)

        # Get token
        retrieved = await vault.get_token(session_id, OAuthProvider.GOOGLE)
        assert retrieved.access_token == "access-token-12345"
        assert retrieved.refresh_token == "refresh-token-67890"
        assert retrieved.scope == "openid profile email"

        # Update token
        updated_token = await vault.update_token(
            session_id,
            OAuthProvider.GOOGLE,
            access_token="new-access-token",
            refresh_token="new-refresh-token",
        )
        assert updated_token.access_token == "new-access-token"

        # Verify update persisted
        retrieved_updated = await vault.get_token(session_id, OAuthProvider.GOOGLE)
        assert retrieved_updated.access_token == "new-access-token"

        # Delete token
        result = await vault.delete_token(session_id, OAuthProvider.GOOGLE)
        assert result is True

        # Verify deleted
        with pytest.raises(Exception):  # TokenNotFoundError
            await vault.get_token(session_id, OAuthProvider.GOOGLE)

    @pytest.mark.asyncio
    async def test_multi_provider_tokens(self, redis_client, encryption_key):
        """Test storing tokens for multiple providers in same session."""
        storage = RedisVaultStorage(redis_client, key_prefix="test:vault:")
        vault = TokenVault(encryption_key=encryption_key, storage=storage)

        session_id = "multi-provider-session-12345678"
        now = utc_now()

        # Store tokens for multiple providers
        providers_data = [
            (OAuthProvider.GOOGLE, "google-access-token"),
            (OAuthProvider.AZURE, "azure-access-token"),
            (OAuthProvider.GITHUB, "github-access-token"),
        ]

        for provider, access_token in providers_data:
            token = TokenRecord(
                provider=provider,
                access_token=access_token,
                issued_at=now,
            )
            await vault.store_token(session_id, token)

        # Verify all providers
        providers = await vault.list_providers(session_id)
        assert len(providers) == 3
        assert set(providers) == {
            OAuthProvider.GOOGLE,
            OAuthProvider.AZURE,
            OAuthProvider.GITHUB,
        }

        # Verify individual tokens
        for provider, expected_token in providers_data:
            token = await vault.get_token(session_id, provider)
            assert token.access_token == expected_token

    @pytest.mark.asyncio
    async def test_encryption_isolation(self, redis_client):
        """Test that different encryption keys can't read each other's data."""
        storage = RedisVaultStorage(redis_client, key_prefix="test:vault:")

        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        vault1 = TokenVault(encryption_key=key1, storage=storage)
        vault2 = TokenVault(encryption_key=key2, storage=storage)

        session_id = "encryption-isolation-test-12345"
        now = utc_now()

        # Store with vault1
        token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="secret-token",
            issued_at=now,
        )
        await vault1.store_token(session_id, token)

        # vault1 can read it
        retrieved = await vault1.get_token(session_id, OAuthProvider.GOOGLE)
        assert retrieved.access_token == "secret-token"

        # vault2 with different key gets decryption error
        with pytest.raises(Exception):  # DecryptionError
            await vault2.get_token(session_id, OAuthProvider.GOOGLE)

    @pytest.mark.asyncio
    async def test_vault_ttl(self, redis_client, encryption_key):
        """Test that vault data has TTL set."""
        storage = RedisVaultStorage(
            redis_client, key_prefix="test:vault:", default_ttl=3600
        )
        vault = TokenVault(encryption_key=encryption_key, storage=storage)

        session_id = "ttl-vault-test-123456789012345"
        token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="token-with-ttl",
            issued_at=utc_now(),
        )
        await vault.store_token(session_id, token)

        # Check TTL
        ttl = await storage.get_ttl(session_id)
        assert 3500 < ttl <= 3600


@requires_redis
class TestMockConsistency:
    """Tests to verify mock Redis behavior matches real Redis."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, redis_client):
        """Verify get returns None for nonexistent keys."""
        result = await redis_client.get("nonexistent-key-12345")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, redis_client):
        """Verify delete returns 0 for nonexistent keys."""
        result = await redis_client.delete("nonexistent-key-12345")
        assert result == 0

    @pytest.mark.asyncio
    async def test_exists_behavior(self, redis_client):
        """Verify exists returns correct counts."""
        # Nonexistent
        result = await redis_client.exists("nonexistent-1", "nonexistent-2")
        assert result == 0

        # Set one key
        await redis_client.set("exists-test-key", b"value")
        result = await redis_client.exists("exists-test-key", "nonexistent-2")
        assert result == 1

    @pytest.mark.asyncio
    async def test_setex_behavior(self, redis_client):
        """Verify setex sets TTL correctly."""
        await redis_client.setex("setex-test-key", 100, b"value")

        # Key exists
        value = await redis_client.get("setex-test-key")
        assert value == b"value"

        # TTL is set
        ttl = await redis_client.ttl("setex-test-key")
        assert 95 <= ttl <= 100

    @pytest.mark.asyncio
    async def test_ttl_nonexistent_key(self, redis_client):
        """Verify TTL returns -2 for nonexistent keys."""
        ttl = await redis_client.ttl("nonexistent-ttl-key")
        assert ttl == -2

    @pytest.mark.asyncio
    async def test_keys_pattern(self, redis_client):
        """Verify keys pattern matching."""
        # Set some keys
        await redis_client.set("pattern:a", b"1")
        await redis_client.set("pattern:b", b"2")
        await redis_client.set("other:c", b"3")

        # Match pattern
        keys = await redis_client.keys("pattern:*")
        key_strs = {k.decode() for k in keys}
        assert key_strs == {"pattern:a", "pattern:b"}
