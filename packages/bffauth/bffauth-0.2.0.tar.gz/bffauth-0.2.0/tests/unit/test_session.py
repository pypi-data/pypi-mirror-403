"""
Unit tests for session management.
"""

from datetime import timedelta

import pytest

from bffauth.core.exceptions import (
    CSRFValidationError,
    SessionNotFoundError,
)
from bffauth.core.session import InMemorySessionStorage, SessionManager


class TestSessionManager:
    """Test SessionManager functionality."""

    @pytest.fixture
    def session_manager(self):
        """Create session manager with short lifetime for testing."""
        return SessionManager(
            session_lifetime=timedelta(hours=1),
            cookie_secure=False,  # Allow non-HTTPS for testing
            cookie_name="test-session",
        )

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Should create session with unique ID and CSRF token."""
        session = await session_manager.create_session()

        assert session.session_id is not None
        assert len(session.session_id) >= 32
        assert session.csrf_token is not None
        assert len(session.csrf_token) >= 32
        assert not session.is_expired()

    @pytest.mark.asyncio
    async def test_get_session(self, session_manager):
        """Should retrieve created session."""
        created = await session_manager.create_session()
        retrieved = await session_manager.get_session(created.session_id)

        assert retrieved.session_id == created.session_id
        assert retrieved.csrf_token == created.csrf_token

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_manager):
        """Should raise SessionNotFoundError for unknown session."""
        with pytest.raises(SessionNotFoundError):
            await session_manager.get_session("nonexistent-session-id")

    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager):
        """Should delete session."""
        session = await session_manager.create_session()
        deleted = await session_manager.delete_session(session.session_id)

        assert deleted is True

        with pytest.raises(SessionNotFoundError):
            await session_manager.get_session(session.session_id)

    @pytest.mark.asyncio
    async def test_delete_session_nonexistent(self, session_manager):
        """Should return False for nonexistent session."""
        deleted = await session_manager.delete_session("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_validate_csrf_success(self, session_manager):
        """Should validate correct CSRF token."""
        session = await session_manager.create_session()
        result = await session_manager.validate_csrf(
            session.session_id,
            session.csrf_token,
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_csrf_failure(self, session_manager):
        """Should reject incorrect CSRF token."""
        session = await session_manager.create_session()

        with pytest.raises(CSRFValidationError):
            await session_manager.validate_csrf(
                session.session_id,
                "wrong-csrf-token",
            )

    @pytest.mark.asyncio
    async def test_rotate_csrf_token(self, session_manager):
        """Should generate new CSRF token."""
        session = await session_manager.create_session()
        old_token = session.csrf_token

        new_token = await session_manager.rotate_csrf_token(session.session_id)

        assert new_token != old_token
        assert len(new_token) >= 32

    @pytest.mark.asyncio
    async def test_refresh_session(self, session_manager):
        """Should extend session expiration."""
        session = await session_manager.create_session()
        old_expiry = session.expires_at

        refreshed = await session_manager.refresh_session(session.session_id)

        assert refreshed.expires_at > old_expiry

    @pytest.mark.asyncio
    async def test_update_session(self, session_manager):
        """Should update session data."""
        session = await session_manager.create_session()
        session.user_id = "test-user"
        session.user_info = {"name": "Test User"}

        await session_manager.update_session(session)

        retrieved = await session_manager.get_session(session.session_id)
        assert retrieved.user_id == "test-user"
        assert retrieved.user_info["name"] == "Test User"

    def test_cookie_options(self, session_manager):
        """Should return correct cookie options."""
        options = session_manager.get_cookie_options()

        assert options["key"] == "test-session"
        assert options["httponly"] is True
        assert options["samesite"] == "strict"

    def test_host_cookie_validation(self):
        """Should enforce __Host- prefix requirements."""
        # Should fail: __Host- with Secure=False
        with pytest.raises(ValueError, match="Secure=True"):
            SessionManager(
                cookie_name="__Host-session",
                cookie_secure=False,
            )

        # Should fail: __Host- with non-root path
        with pytest.raises(ValueError, match="Path=/"):
            SessionManager(
                cookie_name="__Host-session",
                cookie_secure=True,
                cookie_path="/app",
            )

        # Should succeed
        manager = SessionManager(
            cookie_name="__Host-session",
            cookie_secure=True,
            cookie_path="/",
        )
        assert manager.cookie_name == "__Host-session"


class TestInMemorySessionStorage:
    """Test InMemorySessionStorage."""

    @pytest.fixture
    def storage(self):
        """Create storage instance."""
        return InMemorySessionStorage()

    @pytest.mark.asyncio
    async def test_set_and_get(self, storage):
        """Should store and retrieve session."""
        from datetime import datetime, timedelta, timezone

        from bffauth.core.models import SessionData

        session_id = "a" * 32 + "-test-session-id"
        session = SessionData(
            session_id=session_id,
            csrf_token="b" * 32 + "-csrf-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        await storage.set(session)
        retrieved = await storage.get(session_id)

        assert retrieved is not None
        assert retrieved.session_id == session_id

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, storage):
        """Should return None for nonexistent session."""
        result = await storage.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, storage):
        """Should delete session."""
        from datetime import datetime, timedelta, timezone

        from bffauth.core.models import SessionData

        session_id = "c" * 32 + "-delete-test"
        session = SessionData(
            session_id=session_id,
            csrf_token="d" * 32 + "-csrf-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        await storage.set(session)
        deleted = await storage.delete(session_id)

        assert deleted is True
        assert await storage.get(session_id) is None

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, storage):
        """Should remove expired sessions."""
        from datetime import datetime, timedelta, timezone

        from bffauth.core.models import SessionData

        expired_id = "e" * 32 + "-expired-session"
        valid_id = "f" * 32 + "-valid-session"
        csrf = "g" * 32 + "-csrf-token"

        # Create expired session
        expired = SessionData(
            session_id=expired_id,
            csrf_token=csrf,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        # Create valid session
        valid = SessionData(
            session_id=valid_id,
            csrf_token=csrf,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        await storage.set(expired)
        await storage.set(valid)

        count = await storage.cleanup_expired()

        assert count == 1
        assert await storage.get(expired_id) is None
        assert await storage.get(valid_id) is not None
