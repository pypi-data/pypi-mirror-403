"""
BFF Session Manager.

Implements secure session management with:
- __Host- prefixed cookies (per IETF security requirements)
- CSRF protection
- Session binding to prevent token theft
"""

import hashlib
import secrets
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any

from .exceptions import (
    CSRFValidationError,
    SessionExpiredError,
    SessionNotFoundError,
)
from .models import SessionData, utc_now


class SessionStorageProtocol(ABC):
    """Abstract interface for session storage backends."""

    @abstractmethod
    async def get(self, session_id: str) -> SessionData | None:
        """Retrieve session by ID."""
        pass

    @abstractmethod
    async def set(self, session: SessionData) -> None:
        """Store session."""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete session. Returns True if existed."""
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed."""
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> list[SessionData]:
        """
        Find all sessions for a user.

        Used for back-channel logout to invalidate all user sessions.

        Args:
            user_id: User identifier (typically 'sub' claim from IdP).

        Returns:
            List of sessions for the user.
        """
        pass


class InMemorySessionStorage(SessionStorageProtocol):
    """
    In-memory session storage for development/testing.

    NOT suitable for production multi-instance deployments.
    Use Redis or database storage for production.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}

    async def get(self, session_id: str) -> SessionData | None:
        """Retrieve session by ID."""
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            await self.delete(session_id)
            return None
        return session

    async def set(self, session: SessionData) -> None:
        """Store session."""
        self._sessions[session.session_id] = session

    async def delete(self, session_id: str) -> bool:
        """Delete session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def cleanup_expired(self) -> int:
        """Remove expired sessions."""
        now = utc_now()
        expired = [
            sid for sid, session in self._sessions.items() if session.expires_at <= now
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    async def find_by_user_id(self, user_id: str) -> list[SessionData]:
        """Find all sessions for a user."""
        return [
            session
            for session in self._sessions.values()
            if session.user_id == user_id and not session.is_expired()
        ]


class SessionManager:
    """
    BFF Session Manager.

    Handles session lifecycle with security best practices:
    - Cryptographically random session IDs (256 bits)
    - CSRF tokens per session
    - __Host- cookie prefix enforcement
    - Session expiration and cleanup
    """

    def __init__(
        self,
        storage: SessionStorageProtocol | None = None,
        session_lifetime: timedelta = timedelta(hours=24),
        cookie_name: str = "__Host-session",
        cookie_secure: bool = True,
        cookie_samesite: str = "strict",
        cookie_path: str = "/",
    ):
        """
        Initialize session manager.

        Args:
            storage: Session storage backend. Defaults to in-memory.
            session_lifetime: How long sessions remain valid.
            cookie_name: Cookie name. Should use __Host- prefix.
            cookie_secure: Set Secure flag on cookie.
            cookie_samesite: SameSite cookie attribute.
            cookie_path: Cookie path.
        """
        self.storage = storage or InMemorySessionStorage()
        self.session_lifetime = session_lifetime
        self.cookie_name = cookie_name
        self.cookie_secure = cookie_secure
        self.cookie_samesite = cookie_samesite
        self.cookie_path = cookie_path

        # Validate __Host- prefix requirements
        if cookie_name.startswith("__Host-"):
            if not cookie_secure:
                raise ValueError("__Host- cookies require Secure=True")
            if cookie_path != "/":
                raise ValueError("__Host- cookies require Path=/")

    @staticmethod
    def generate_session_id() -> str:
        """Generate cryptographically secure session ID."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_csrf_token() -> str:
        """Generate cryptographically secure CSRF token."""
        return secrets.token_urlsafe(32)

    def hash_session_id(self, session_id: str) -> str:
        """Hash session ID for storage key (prevents timing attacks)."""
        return hashlib.sha256(session_id.encode()).hexdigest()

    async def create_session(
        self,
        user_id: str | None = None,
        user_info: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionData:
        """
        Create a new session.

        Args:
            user_id: Optional user identifier.
            user_info: Optional user information dict.
            metadata: Optional additional metadata.

        Returns:
            New SessionData with generated IDs.
        """
        now = utc_now()
        session = SessionData(
            session_id=self.generate_session_id(),
            csrf_token=self.generate_csrf_token(),
            created_at=now,
            last_activity=now,
            expires_at=now + self.session_lifetime,
            user_id=user_id,
            user_info=user_info or {},
            metadata=metadata or {},
        )
        await self.storage.set(session)
        return session

    async def get_session(self, session_id: str) -> SessionData:
        """
        Retrieve session by ID.

        Args:
            session_id: Session identifier from cookie.

        Returns:
            SessionData if valid.

        Raises:
            SessionNotFoundError: If session doesn't exist.
            SessionExpiredError: If session has expired.
        """
        session = await self.storage.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        if session.is_expired():
            await self.storage.delete(session_id)
            raise SessionExpiredError()
        return session

    async def update_session(self, session: SessionData) -> None:
        """
        Update session data and touch last activity.

        Args:
            session: Session to update.
        """
        session.touch()
        await self.storage.set(session)

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session to delete.

        Returns:
            True if session existed and was deleted.
        """
        return await self.storage.delete(session_id)

    async def refresh_session(self, session_id: str) -> SessionData:
        """
        Refresh session with new expiration time.

        Useful for sliding session expiration.

        Args:
            session_id: Session to refresh.

        Returns:
            Updated SessionData.

        Raises:
            SessionNotFoundError: If session doesn't exist.
        """
        session = await self.get_session(session_id)
        session.expires_at = utc_now() + self.session_lifetime
        session.touch()
        await self.storage.set(session)
        return session

    async def rotate_csrf_token(self, session_id: str) -> str:
        """
        Generate new CSRF token for session.

        Should be called after sensitive operations.

        Args:
            session_id: Session to update.

        Returns:
            New CSRF token.

        Raises:
            SessionNotFoundError: If session doesn't exist.
        """
        session = await self.get_session(session_id)
        session.csrf_token = self.generate_csrf_token()
        await self.storage.set(session)
        return session.csrf_token

    async def validate_csrf(
        self,
        session_id: str,
        csrf_token: str,
        rotate_on_success: bool = False,
    ) -> bool:
        """
        Validate CSRF token for session.

        Args:
            session_id: Session to validate against.
            csrf_token: Token from request.
            rotate_on_success: Generate new token after validation.

        Returns:
            True if valid.

        Raises:
            SessionNotFoundError: If session doesn't exist.
            CSRFValidationError: If token is invalid.
        """
        session = await self.get_session(session_id)

        # Constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(session.csrf_token, csrf_token):
            raise CSRFValidationError("CSRF token mismatch")

        if rotate_on_success:
            session.csrf_token = self.generate_csrf_token()
            await self.storage.set(session)

        return True

    def get_cookie_options(self) -> dict[str, Any]:
        """
        Get cookie options for setting session cookie.

        Returns:
            Dict of cookie options for framework's set_cookie().
        """
        return {
            "key": self.cookie_name,
            "httponly": True,
            "secure": self.cookie_secure,
            "samesite": self.cookie_samesite,
            "path": self.cookie_path,
        }

    async def cleanup_expired(self) -> int:
        """
        Remove expired sessions from storage.

        Should be called periodically (e.g., via background task).

        Returns:
            Number of sessions removed.
        """
        return await self.storage.cleanup_expired()

    async def find_sessions_by_user(self, user_id: str) -> list[SessionData]:
        """
        Find all sessions for a user.

        Used for back-channel logout to identify sessions to invalidate.

        Args:
            user_id: User identifier (typically 'sub' claim from IdP).

        Returns:
            List of sessions for the user.
        """
        return await self.storage.find_by_user_id(user_id)

    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.

        Used for back-channel logout to invalidate all user sessions.

        Args:
            user_id: User identifier (typically 'sub' claim from IdP).

        Returns:
            Number of sessions deleted.
        """
        sessions = await self.storage.find_by_user_id(user_id)
        deleted = 0
        for session in sessions:
            if await self.storage.delete(session.session_id):
                deleted += 1
        return deleted
