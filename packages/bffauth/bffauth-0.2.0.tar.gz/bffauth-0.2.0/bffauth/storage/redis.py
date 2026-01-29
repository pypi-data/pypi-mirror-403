"""
Redis Storage Backends.

Production-ready Redis implementations for session and vault storage.
Supports both sync and async Redis clients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from ..core.models import SessionData, utc_now
from ..core.session import SessionStorageProtocol
from ..core.vault import TokenVaultStorageProtocol

if TYPE_CHECKING:
    from datetime import timedelta


class AsyncRedisProtocol(Protocol):
    """Protocol for async Redis client compatibility."""

    async def get(self, name: str) -> bytes | None: ...
    async def set(
        self, name: str, value: bytes, ex: int | None = None
    ) -> bool | None: ...
    async def setex(self, name: str, time: int, value: bytes) -> bool | None: ...
    async def delete(self, *names: str) -> int: ...
    async def exists(self, *names: str) -> int: ...
    async def keys(self, pattern: str) -> list[bytes]: ...
    async def ttl(self, name: str) -> int: ...


class RedisSessionStorage(SessionStorageProtocol):
    """
    Redis-backed session storage.

    Features:
    - Automatic TTL-based expiration
    - Atomic operations
    - Horizontal scaling support
    - Optional key prefix for multi-tenant deployments

    Usage:
        import redis.asyncio as redis

        client = redis.Redis(host="localhost", port=6379, db=0)
        storage = RedisSessionStorage(client, key_prefix="myapp:")
        session_manager = SessionManager(storage=storage)
    """

    def __init__(
        self,
        redis_client: Any,
        key_prefix: str = "bffauth:session:",
    ):
        """
        Initialize Redis session storage.

        Args:
            redis_client: Async Redis client (redis.asyncio.Redis).
            key_prefix: Prefix for all session keys.
        """
        self._redis: AsyncRedisProtocol = redis_client
        self._prefix = key_prefix

    def _key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"{self._prefix}{session_id}"

    async def get(self, session_id: str) -> SessionData | None:
        """
        Retrieve session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            SessionData if found and not expired, None otherwise.
        """
        data = await self._redis.get(self._key(session_id))
        if data is None:
            return None

        session = SessionData.model_validate_json(data)

        # Double-check expiration (Redis TTL is a backup)
        if session.is_expired():
            await self.delete(session_id)
            return None

        return session

    async def set(self, session: SessionData) -> None:
        """
        Store session with automatic TTL.

        Args:
            session: Session data to store.
        """
        ttl = int((session.expires_at - utc_now()).total_seconds())
        if ttl <= 0:
            # Don't store already-expired sessions
            return

        await self._redis.setex(
            self._key(session.session_id),
            ttl,
            session.model_dump_json().encode("utf-8"),
        )

    async def delete(self, session_id: str) -> bool:
        """
        Delete session.

        Args:
            session_id: Session to delete.

        Returns:
            True if session existed and was deleted.
        """
        result = await self._redis.delete(self._key(session_id))
        return result > 0

    async def cleanup_expired(self) -> int:
        """
        Remove expired sessions.

        Note: Redis TTL handles expiration automatically. This method
        performs a scan for any sessions that might have stale data
        due to clock skew or other issues.

        Returns:
            Number of sessions removed.
        """
        # Redis TTL handles this automatically, but we scan for edge cases
        pattern = f"{self._prefix}*"
        keys = await self._redis.keys(pattern)
        removed = 0

        for key in keys:
            key_str = key.decode("utf-8") if isinstance(key, bytes) else key
            data = await self._redis.get(key_str)

            if data is not None:
                try:
                    session = SessionData.model_validate_json(data)
                    if session.is_expired():
                        await self._redis.delete(key_str)
                        removed += 1
                except Exception:
                    # Invalid session data, remove it
                    await self._redis.delete(key_str)
                    removed += 1

        return removed

    async def extend_session(self, session_id: str, additional_time: timedelta) -> bool:
        """
        Extend session expiration (sliding expiration).

        Args:
            session_id: Session to extend.
            additional_time: Time to add to current expiration.

        Returns:
            True if session was extended, False if not found.
        """
        session = await self.get(session_id)
        if session is None:
            return False

        session.expires_at = utc_now() + additional_time
        session.touch()
        await self.set(session)
        return True

    async def get_ttl(self, session_id: str) -> int:
        """
        Get remaining TTL for session.

        Args:
            session_id: Session identifier.

        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist.
        """
        return await self._redis.ttl(self._key(session_id))

    async def find_by_user_id(self, user_id: str) -> list[SessionData]:
        """
        Find all sessions for a user.

        Used for back-channel logout to invalidate all user sessions.

        Note: This performs a scan of all session keys. For high-volume
        deployments, consider adding a secondary index (user_id -> session_ids).

        Args:
            user_id: User identifier (typically 'sub' claim from IdP).

        Returns:
            List of sessions for the user.
        """
        pattern = f"{self._prefix}*"
        keys = await self._redis.keys(pattern)
        sessions: list[SessionData] = []

        for key in keys:
            key_str = key.decode("utf-8") if isinstance(key, bytes) else key
            data = await self._redis.get(key_str)

            if data is not None:
                try:
                    session = SessionData.model_validate_json(data)
                    if session.user_id == user_id and not session.is_expired():
                        sessions.append(session)
                except Exception:
                    # Invalid session data, skip it
                    pass

        return sessions


class RedisVaultStorage(TokenVaultStorageProtocol):
    """
    Redis-backed token vault storage.

    Stores encrypted token vault data with optional TTL.

    Features:
    - Encrypted data storage (encryption handled by TokenVault)
    - Optional TTL for automatic cleanup
    - Atomic operations
    - Key prefix support

    Usage:
        import redis.asyncio as redis

        client = redis.Redis(host="localhost", port=6379, db=0)
        storage = RedisVaultStorage(client, key_prefix="myapp:")
        vault = TokenVault(encryption_key=key, storage=storage)
    """

    def __init__(
        self,
        redis_client: Any,
        key_prefix: str = "bffauth:vault:",
        default_ttl: int | None = 86400,  # 24 hours default
    ):
        """
        Initialize Redis vault storage.

        Args:
            redis_client: Async Redis client (redis.asyncio.Redis).
            key_prefix: Prefix for all vault keys.
            default_ttl: Default TTL in seconds (None for no expiration).
        """
        self._redis: AsyncRedisProtocol = redis_client
        self._prefix = key_prefix
        self._default_ttl = default_ttl

    def _key(self, session_id: str) -> str:
        """Generate Redis key for vault."""
        return f"{self._prefix}{session_id}"

    async def get(self, session_id: str) -> bytes | None:
        """
        Retrieve encrypted vault data by session ID.

        Args:
            session_id: Session identifier.

        Returns:
            Encrypted vault data, or None if not found.
        """
        return await self._redis.get(self._key(session_id))

    async def set(self, session_id: str, data: bytes) -> None:
        """
        Store encrypted vault data.

        Args:
            session_id: Session identifier.
            data: Encrypted vault data.
        """
        if self._default_ttl is not None:
            await self._redis.setex(
                self._key(session_id),
                self._default_ttl,
                data,
            )
        else:
            await self._redis.set(self._key(session_id), data)

    async def delete(self, session_id: str) -> bool:
        """
        Delete vault data.

        Args:
            session_id: Session identifier.

        Returns:
            True if vault existed and was deleted.
        """
        result = await self._redis.delete(self._key(session_id))
        return result > 0

    async def exists(self, session_id: str) -> bool:
        """
        Check if vault exists for session.

        Args:
            session_id: Session identifier.

        Returns:
            True if vault exists.
        """
        result = await self._redis.exists(self._key(session_id))
        return result > 0

    async def set_with_ttl(self, session_id: str, data: bytes, ttl: int) -> None:
        """
        Store encrypted vault data with custom TTL.

        Args:
            session_id: Session identifier.
            data: Encrypted vault data.
            ttl: Time to live in seconds.
        """
        await self._redis.setex(self._key(session_id), ttl, data)

    async def get_ttl(self, session_id: str) -> int:
        """
        Get remaining TTL for vault.

        Args:
            session_id: Session identifier.

        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist.
        """
        return await self._redis.ttl(self._key(session_id))
