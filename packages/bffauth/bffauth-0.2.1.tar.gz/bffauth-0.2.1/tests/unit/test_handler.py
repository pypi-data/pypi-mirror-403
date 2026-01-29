"""
Unit tests for BFF OAuth Handler.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from bffauth.core.exceptions import (
    AuthorizationError,
    CSRFValidationError,
    LogoutTokenError,
    ProviderNotConfiguredError,
    SessionNotFoundError,
    StateValidationError,
    TokenExpiredError,
    TokenNotFoundError,
)
from bffauth.core.models import (
    AuthorizationResult,
    OAuthProvider,
    OAuthState,
    ProviderConfig,
    TokenRecord,
)
from bffauth.handler import BFFOAuthHandler


class TestBFFOAuthHandler:
    """Test BFFOAuthHandler functionality."""

    @pytest.fixture
    def provider_config(self):
        """Create test provider configuration."""
        return ProviderConfig(
            provider=OAuthProvider.GOOGLE,
            client_id="test-client-id",
            client_secret="test-client-secret",
            authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
            scope="openid email profile",
        )

    @pytest.fixture
    def handler(self, encryption_key):
        """Create handler with test configuration."""
        return BFFOAuthHandler(
            encryption_key=encryption_key,
            redirect_base_uri="https://app.example.com",
            callback_path="/auth/callback",
            cookie_secure=False,  # Allow non-HTTPS for testing
            cookie_name="test-session",
        )

    @pytest.fixture
    def handler_with_provider(self, handler, provider_config):
        """Create handler with registered provider."""
        handler.register_provider(provider_config)
        return handler

    def test_initialization(self, encryption_key):
        """Should initialize with default configuration."""
        handler = BFFOAuthHandler(
            encryption_key=encryption_key,
            redirect_base_uri="https://app.example.com",
        )

        assert handler.redirect_base_uri == "https://app.example.com"
        assert handler.callback_path == "/auth/callback"
        assert handler.token_refresh_buffer == 300

    def test_initialization_strips_trailing_slash(self, encryption_key):
        """Should strip trailing slash from redirect URI."""
        handler = BFFOAuthHandler(
            encryption_key=encryption_key,
            redirect_base_uri="https://app.example.com/",
        )

        assert handler.redirect_base_uri == "https://app.example.com"

    def test_register_provider(self, handler, provider_config):
        """Should register provider configuration."""
        handler.register_provider(provider_config)

        assert OAuthProvider.GOOGLE.value in handler._providers
        assert OAuthProvider.GOOGLE.value in handler._backends

    def test_get_provider_success(self, handler_with_provider):
        """Should return registered provider configuration."""
        config = handler_with_provider.get_provider(OAuthProvider.GOOGLE)

        assert config.provider == OAuthProvider.GOOGLE
        assert config.client_id == "test-client-id"

    def test_get_provider_not_configured(self, handler):
        """Should raise ProviderNotConfiguredError for unregistered provider."""
        with pytest.raises(ProviderNotConfiguredError):
            handler.get_provider(OAuthProvider.GOOGLE)

    def test_get_backend_success(self, handler_with_provider):
        """Should return backend for registered provider."""
        backend = handler_with_provider.get_backend(OAuthProvider.GOOGLE)

        assert backend is not None

    def test_get_backend_not_configured(self, handler):
        """Should raise ProviderNotConfiguredError for unregistered provider."""
        with pytest.raises(ProviderNotConfiguredError):
            handler.get_backend(OAuthProvider.GOOGLE)

    def test_get_redirect_uri(self, handler_with_provider):
        """Should construct correct redirect URI."""
        uri = handler_with_provider.get_redirect_uri(OAuthProvider.GOOGLE)

        assert uri == "https://app.example.com/auth/callback/google"

    @pytest.mark.asyncio
    async def test_start_authorization(self, handler_with_provider):
        """Should create session and return authorization URL."""
        with patch.object(
            handler_with_provider._backends["google"],
            "create_authorization_url",
        ) as mock_create_url:
            mock_state = OAuthState(
                state="a" * 32,
                provider=OAuthProvider.GOOGLE,
                code_verifier="b" * 50,
                redirect_uri="https://app.example.com/auth/callback/google",
            )
            mock_create_url.return_value = (
                "https://accounts.google.com/o/oauth2/v2/auth?...",
                mock_state,
            )

            auth_url, session = await handler_with_provider.start_authorization(
                provider=OAuthProvider.GOOGLE,
            )

            assert auth_url.startswith("https://accounts.google.com")
            assert session.session_id is not None
            assert len(session.csrf_token) >= 32
            # OAuth state is now stored in session metadata
            assert "oauth_state" in session.metadata
            assert session.metadata["oauth_state"]["state"] == mock_state.state

    @pytest.mark.asyncio
    async def test_start_authorization_with_existing_session(
        self, handler_with_provider
    ):
        """Should use existing session when provided."""
        existing_session = await handler_with_provider.session_manager.create_session()

        with patch.object(
            handler_with_provider._backends["google"],
            "create_authorization_url",
        ) as mock_create_url:
            mock_state = OAuthState(
                state="c" * 32,
                provider=OAuthProvider.GOOGLE,
                code_verifier="d" * 50,
                redirect_uri="https://app.example.com/auth/callback/google",
            )
            mock_create_url.return_value = (
                "https://accounts.google.com/o/oauth2/v2/auth?...",
                mock_state,
            )

            auth_url, session = await handler_with_provider.start_authorization(
                provider=OAuthProvider.GOOGLE,
                existing_session=existing_session,
            )

            assert session.session_id == existing_session.session_id

    @pytest.mark.asyncio
    async def test_handle_callback_success(self, handler_with_provider):
        """Should exchange code for tokens and store them."""
        # Create session first
        session = await handler_with_provider.session_manager.create_session()

        # Create mock state and store in session metadata
        mock_state = OAuthState(
            state="e" * 32,
            provider=OAuthProvider.GOOGLE,
            code_verifier="f" * 50,
            redirect_uri="https://app.example.com/auth/callback/google",
        )
        session.metadata["oauth_state"] = {
            "state": mock_state.state,
            "provider": mock_state.provider.value,
            "code_verifier": mock_state.code_verifier,
            "nonce": mock_state.nonce,
            "redirect_uri": mock_state.redirect_uri,
            "created_at": mock_state.created_at.isoformat(),
            "expires_at": mock_state.expires_at.isoformat(),
        }
        await handler_with_provider.session_manager.update_session(session)

        # Mock the backend exchange
        mock_token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        mock_result = AuthorizationResult(
            token=mock_token,
            id_token_claims={"sub": "user-123", "email": "test@example.com"},
        )

        with patch.object(
            handler_with_provider._backends["google"],
            "exchange_code",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await handler_with_provider.handle_callback(
                session_id=session.session_id,
                code="test-auth-code",
                state=mock_state.state,
            )

            assert result.token.access_token == "test-access-token"
            assert result.id_token_claims["sub"] == "user-123"

            # Verify token was stored
            stored_token = await handler_with_provider.token_vault.get_token(
                session.session_id,
                OAuthProvider.GOOGLE,
            )
            assert stored_token.access_token == "test-access-token"

            # Verify session was updated
            updated_session = await handler_with_provider.session_manager.get_session(
                session.session_id
            )
            assert OAuthProvider.GOOGLE.value in updated_session.authenticated_providers
            assert updated_session.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_handle_callback_error_response(self, handler_with_provider):
        """Should raise AuthorizationError for error response."""
        session = await handler_with_provider.session_manager.create_session()

        with pytest.raises(AuthorizationError) as exc_info:
            await handler_with_provider.handle_callback(
                session_id=session.session_id,
                error="access_denied",
                error_description="User denied access",
            )

        assert "access_denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_callback_missing_params(self, handler_with_provider):
        """Should raise AuthorizationError for missing parameters."""
        session = await handler_with_provider.session_manager.create_session()

        with pytest.raises(AuthorizationError):
            await handler_with_provider.handle_callback(
                session_id=session.session_id,
                code=None,
                state=None,
            )

    @pytest.mark.asyncio
    async def test_handle_callback_invalid_state(self, handler_with_provider):
        """Should raise StateValidationError for state mismatch."""
        session = await handler_with_provider.session_manager.create_session()

        # Store a state in session
        session.metadata["oauth_state"] = {
            "state": "expected-state" + "x" * 20,
            "provider": "google",
            "code_verifier": "v" * 50,
            "nonce": None,
            "redirect_uri": "https://app.example.com/auth/callback/google",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=10)
            ).isoformat(),
        }
        await handler_with_provider.session_manager.update_session(session)

        with pytest.raises(StateValidationError, match="mismatch"):
            await handler_with_provider.handle_callback(
                session_id=session.session_id,
                code="test-code",
                state="wrong-state" + "x" * 22,
            )

    @pytest.mark.asyncio
    async def test_handle_callback_no_pending_state(self, handler_with_provider):
        """Should raise StateValidationError when no OAuth state in session."""
        session = await handler_with_provider.session_manager.create_session()

        with pytest.raises(StateValidationError, match="No pending"):
            await handler_with_provider.handle_callback(
                session_id=session.session_id,
                code="test-code",
                state="any-state" + "x" * 23,
            )

    @pytest.mark.asyncio
    async def test_handle_callback_expired_state(self, handler_with_provider):
        """Should raise StateValidationError for expired state."""
        session = await handler_with_provider.session_manager.create_session()

        # Store expired state in session metadata
        expired_state = OAuthState(
            state="g" * 32,
            provider=OAuthProvider.GOOGLE,
            code_verifier="h" * 50,
            redirect_uri="https://app.example.com/auth/callback/google",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        session.metadata["oauth_state"] = {
            "state": expired_state.state,
            "provider": expired_state.provider.value,
            "code_verifier": expired_state.code_verifier,
            "nonce": expired_state.nonce,
            "redirect_uri": expired_state.redirect_uri,
            "created_at": expired_state.created_at.isoformat(),
            "expires_at": expired_state.expires_at.isoformat(),
        }
        await handler_with_provider.session_manager.update_session(session)

        with pytest.raises(StateValidationError, match="expired"):
            await handler_with_provider.handle_callback(
                session_id=session.session_id,
                code="test-code",
                state=expired_state.state,
            )

    @pytest.mark.asyncio
    async def test_get_access_token_valid(self, handler_with_provider):
        """Should return valid access token."""
        session = await handler_with_provider.session_manager.create_session()

        # Store a valid token
        token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="valid-access-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        await handler_with_provider.token_vault.store_token(session.session_id, token)

        access_token = await handler_with_provider.get_access_token(
            session.session_id,
            OAuthProvider.GOOGLE,
        )

        assert access_token == "valid-access-token"

    @pytest.mark.asyncio
    async def test_get_access_token_auto_refresh(self, handler_with_provider):
        """Should auto-refresh expired token."""
        session = await handler_with_provider.session_manager.create_session()

        # Store an expired token with refresh token
        expired_token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="expired-access-token",
            refresh_token="valid-refresh-token",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        await handler_with_provider.token_vault.store_token(
            session.session_id,
            expired_token,
        )

        # Mock refresh
        new_token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        with patch.object(
            handler_with_provider._backends["google"],
            "refresh_token",
            new_callable=AsyncMock,
            return_value=new_token,
        ):
            access_token = await handler_with_provider.get_access_token(
                session.session_id,
                OAuthProvider.GOOGLE,
            )

            assert access_token == "new-access-token"

    @pytest.mark.asyncio
    async def test_get_access_token_expired_no_refresh(self, handler_with_provider):
        """Should raise TokenExpiredError when no refresh token available."""
        session = await handler_with_provider.session_manager.create_session()

        # Store an expired token without refresh token
        expired_token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="expired-access-token",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        await handler_with_provider.token_vault.store_token(
            session.session_id,
            expired_token,
        )

        with pytest.raises(TokenExpiredError):
            await handler_with_provider.get_access_token(
                session.session_id,
                OAuthProvider.GOOGLE,
            )

    @pytest.mark.asyncio
    async def test_logout_single_provider(self, handler_with_provider):
        """Should logout from single provider."""
        session = await handler_with_provider.session_manager.create_session()
        session.add_provider(OAuthProvider.GOOGLE)
        await handler_with_provider.session_manager.update_session(session)

        # Store token
        token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="test-token",
        )
        await handler_with_provider.token_vault.store_token(session.session_id, token)

        with patch.object(
            handler_with_provider._backends["google"],
            "revoke_token",
            new_callable=AsyncMock,
        ):
            await handler_with_provider.logout(
                session.session_id,
                provider=OAuthProvider.GOOGLE,
            )

        # Token should be deleted
        with pytest.raises(TokenNotFoundError):
            await handler_with_provider.token_vault.get_token(
                session.session_id,
                OAuthProvider.GOOGLE,
            )

        # Session should still exist but without provider
        updated_session = await handler_with_provider.session_manager.get_session(
            session.session_id
        )
        assert OAuthProvider.GOOGLE.value not in updated_session.authenticated_providers

    @pytest.mark.asyncio
    async def test_logout_all_providers(self, handler_with_provider):
        """Should logout from all providers and delete session."""
        session = await handler_with_provider.session_manager.create_session()

        # Store token
        token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="test-token",
        )
        await handler_with_provider.token_vault.store_token(session.session_id, token)

        with patch.object(
            handler_with_provider._backends["google"],
            "revoke_token",
            new_callable=AsyncMock,
        ):
            await handler_with_provider.logout(session.session_id)

        # Session should be deleted
        with pytest.raises(SessionNotFoundError):
            await handler_with_provider.session_manager.get_session(session.session_id)

    @pytest.mark.asyncio
    async def test_get_session(self, handler_with_provider):
        """Should return session data."""
        session = await handler_with_provider.session_manager.create_session()

        retrieved = await handler_with_provider.get_session(session.session_id)

        assert retrieved.session_id == session.session_id

    @pytest.mark.asyncio
    async def test_validate_csrf(self, handler_with_provider):
        """Should validate CSRF token."""
        session = await handler_with_provider.session_manager.create_session()

        result = await handler_with_provider.validate_csrf(
            session.session_id,
            session.csrf_token,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_authenticated_providers(self, handler_with_provider):
        """Should return list of authenticated providers."""
        session = await handler_with_provider.session_manager.create_session()

        # Store token
        token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="test-token",
        )
        await handler_with_provider.token_vault.store_token(session.session_id, token)

        providers = await handler_with_provider.get_authenticated_providers(
            session.session_id
        )

        assert OAuthProvider.GOOGLE in providers

    def test_get_cookie_options(self, handler_with_provider):
        """Should return cookie options."""
        options = handler_with_provider.get_cookie_options()

        assert options["key"] == "test-session"
        assert options["httponly"] is True

    @pytest.mark.asyncio
    async def test_close(self, handler_with_provider):
        """Should close all backends."""
        with patch.object(
            handler_with_provider._backends["google"],
            "close",
            new_callable=AsyncMock,
        ) as mock_close:
            await handler_with_provider.close()

            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_session(self, handler_with_provider):
        """Should extend session expiration (sliding expiration)."""
        session = await handler_with_provider.session_manager.create_session()
        original_expires = session.expires_at

        # Wait a tiny bit to ensure time difference
        import asyncio

        await asyncio.sleep(0.01)

        refreshed = await handler_with_provider.refresh_session(session.session_id)

        assert refreshed.session_id == session.session_id
        assert refreshed.expires_at > original_expires

    @pytest.mark.asyncio
    async def test_refresh_session_not_found(self, handler_with_provider):
        """Should raise SessionNotFoundError for unknown session."""
        with pytest.raises(SessionNotFoundError):
            await handler_with_provider.refresh_session("nonexistent-session-id")

    @pytest.mark.asyncio
    async def test_validate_csrf_header_success(self, handler_with_provider):
        """Should validate CSRF token from header."""
        session = await handler_with_provider.session_manager.create_session()

        result = await handler_with_provider.validate_csrf_header(
            session.session_id,
            session.csrf_token,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_csrf_header_missing(self, handler_with_provider):
        """Should raise CSRFValidationError when header is missing."""
        session = await handler_with_provider.session_manager.create_session()

        with pytest.raises(CSRFValidationError, match="Missing"):
            await handler_with_provider.validate_csrf_header(
                session.session_id,
                None,
            )

    @pytest.mark.asyncio
    async def test_validate_csrf_header_invalid(self, handler_with_provider):
        """Should raise CSRFValidationError for invalid token."""
        session = await handler_with_provider.session_manager.create_session()

        with pytest.raises(CSRFValidationError):
            await handler_with_provider.validate_csrf_header(
                session.session_id,
                "invalid-csrf-token",
            )

    # Back-channel logout tests

    def _create_logout_token(
        self,
        sub: str | None = "user-123",
        sid: str | None = None,
        iss: str = "https://accounts.google.com",
        aud: str = "test-client-id",
        iat: int | None = None,
        exp: int | None = None,
        jti: str = "unique-token-id",
        include_event: bool = True,
    ) -> str:
        """Create a test logout token."""
        import base64
        import json
        import time

        if iat is None:
            iat = int(time.time())

        claims = {
            "iss": iss,
            "aud": aud,
            "iat": iat,
            "jti": jti,
        }

        if include_event:
            claims["events"] = {
                "http://schemas.openid.net/event/backchannel-logout": {}
            }

        if sub:
            claims["sub"] = sub
        if sid:
            claims["sid"] = sid
        if exp:
            claims["exp"] = exp

        # Create unsigned JWT (for testing purposes)
        header = {"alg": "none", "typ": "JWT"}
        header_b64 = (
            base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
        )
        payload_b64 = (
            base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
        )

        return f"{header_b64}.{payload_b64}."

    @pytest.fixture
    def handler_with_issuer(self, encryption_key):
        """Create handler with provider that has issuer configured."""
        handler = BFFOAuthHandler(
            encryption_key=encryption_key,
            redirect_base_uri="https://app.example.com",
            cookie_name="test-session",
            cookie_secure=False,
        )
        config = ProviderConfig(
            provider=OAuthProvider.GOOGLE,
            client_id="test-client-id",
            client_secret="test-client-secret",
            authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            issuer="https://accounts.google.com",
        )
        handler.register_provider(config)
        return handler

    @pytest.mark.asyncio
    async def test_backchannel_logout_success(self, handler_with_issuer):
        """Should invalidate sessions for user on back-channel logout."""
        # Create a session with user_id
        session = await handler_with_issuer.session_manager.create_session(
            user_id="user-123"
        )

        # Store a token for the session
        token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="test-token",
        )
        await handler_with_issuer.token_vault.store_token(session.session_id, token)

        # Create logout token
        logout_token = self._create_logout_token(sub="user-123")

        # Handle back-channel logout
        count = await handler_with_issuer.handle_backchannel_logout(logout_token)

        assert count == 1

        # Session should be deleted
        with pytest.raises(SessionNotFoundError):
            await handler_with_issuer.get_session(session.session_id)

    @pytest.mark.asyncio
    async def test_backchannel_logout_multiple_sessions(self, handler_with_issuer):
        """Should invalidate all sessions for user."""
        # Create multiple sessions for the same user
        session1 = await handler_with_issuer.session_manager.create_session(
            user_id="user-456"
        )
        session2 = await handler_with_issuer.session_manager.create_session(
            user_id="user-456"
        )

        logout_token = self._create_logout_token(sub="user-456")
        count = await handler_with_issuer.handle_backchannel_logout(logout_token)

        assert count == 2

        with pytest.raises(SessionNotFoundError):
            await handler_with_issuer.get_session(session1.session_id)
        with pytest.raises(SessionNotFoundError):
            await handler_with_issuer.get_session(session2.session_id)

    @pytest.mark.asyncio
    async def test_backchannel_logout_no_matching_sessions(self, handler_with_issuer):
        """Should return 0 when no sessions match."""
        logout_token = self._create_logout_token(sub="unknown-user")
        count = await handler_with_issuer.handle_backchannel_logout(logout_token)

        assert count == 0

    @pytest.mark.asyncio
    async def test_backchannel_logout_invalid_jwt(self, handler_with_issuer):
        """Should raise LogoutTokenError for invalid JWT format."""
        with pytest.raises(LogoutTokenError, match="Invalid JWT format"):
            await handler_with_issuer.handle_backchannel_logout("not-a-jwt")

    @pytest.mark.asyncio
    async def test_backchannel_logout_missing_required_claim(self, handler_with_issuer):
        """Should raise LogoutTokenError for missing required claims."""
        import base64
        import json

        # Create token missing 'iss' claim
        claims = {
            "aud": "test-client-id",
            "iat": 1234567890,
            "jti": "test",
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
            "sub": "user-123",
        }
        header = {"alg": "none"}
        header_b64 = (
            base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
        )
        payload_b64 = (
            base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
        )
        token = f"{header_b64}.{payload_b64}."

        with pytest.raises(LogoutTokenError, match="Missing required claim: iss"):
            await handler_with_issuer.handle_backchannel_logout(token)

    @pytest.mark.asyncio
    async def test_backchannel_logout_missing_event(self, handler_with_issuer):
        """Should raise LogoutTokenError when back-channel logout event missing."""
        logout_token = self._create_logout_token(include_event=False)

        with pytest.raises(LogoutTokenError, match="Missing required claim: events"):
            await handler_with_issuer.handle_backchannel_logout(logout_token)

    @pytest.mark.asyncio
    async def test_backchannel_logout_missing_sub_and_sid(self, handler_with_issuer):
        """Should raise LogoutTokenError when both sub and sid missing."""
        logout_token = self._create_logout_token(sub=None, sid=None)

        with pytest.raises(LogoutTokenError, match="sub.*sid"):
            await handler_with_issuer.handle_backchannel_logout(logout_token)

    @pytest.mark.asyncio
    async def test_backchannel_logout_unrecognized_issuer(self, handler_with_issuer):
        """Should raise LogoutTokenError for unrecognized issuer."""
        logout_token = self._create_logout_token(iss="https://unknown-provider.com")

        with pytest.raises(LogoutTokenError, match="not recognized"):
            await handler_with_issuer.handle_backchannel_logout(logout_token)

    @pytest.mark.asyncio
    async def test_backchannel_logout_wrong_audience(self, handler_with_issuer):
        """Should raise LogoutTokenError for wrong audience."""
        logout_token = self._create_logout_token(aud="wrong-client-id")

        with pytest.raises(LogoutTokenError, match="not recognized"):
            await handler_with_issuer.handle_backchannel_logout(logout_token)

    @pytest.mark.asyncio
    async def test_backchannel_logout_expired_token(self, handler_with_issuer):
        """Should raise LogoutTokenError for expired token."""
        import time

        logout_token = self._create_logout_token(
            exp=int(time.time()) - 3600  # Expired 1 hour ago
        )

        with pytest.raises(LogoutTokenError, match="expired"):
            await handler_with_issuer.handle_backchannel_logout(logout_token)

    @pytest.mark.asyncio
    async def test_backchannel_logout_token_too_old(self, handler_with_issuer):
        """Should raise LogoutTokenError for token older than 10 minutes."""
        import time

        logout_token = self._create_logout_token(
            iat=int(time.time()) - 3600  # Issued 1 hour ago
        )

        with pytest.raises(LogoutTokenError, match="too old"):
            await handler_with_issuer.handle_backchannel_logout(logout_token)

    @pytest.mark.asyncio
    async def test_backchannel_logout_with_sid_only(self, handler_with_issuer):
        """Should handle logout with sid claim only."""
        # This test documents that sid-only logout returns 0 since
        # we don't have secondary indexing by sid in place yet
        logout_token = self._create_logout_token(sub=None, sid="session-at-idp")

        count = await handler_with_issuer.handle_backchannel_logout(logout_token)
        assert count == 0  # No sessions matched (sid lookup not implemented)

    # RP-Initiated Logout (ID Token Hint) tests

    @pytest.fixture
    def handler_with_end_session(self, encryption_key):
        """Create handler with provider that has end_session_endpoint."""
        handler = BFFOAuthHandler(
            encryption_key=encryption_key,
            redirect_base_uri="https://app.example.com",
            cookie_name="test-session",
            cookie_secure=False,
        )
        config = ProviderConfig(
            provider=OAuthProvider.AZURE,
            client_id="test-client-id",
            client_secret="test-client-secret",
            authorization_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            issuer="https://login.microsoftonline.com/common/v2.0",
            end_session_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/logout",
        )
        handler.register_provider(config)
        return handler

    @pytest.mark.asyncio
    async def test_get_logout_url_with_id_token(self, handler_with_end_session):
        """Should return logout URL with id_token_hint when ID token available."""
        session = await handler_with_end_session.session_manager.create_session()

        # Store token with ID token
        token = TokenRecord(
            provider=OAuthProvider.AZURE,
            access_token="test-access-token",
            id_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature",
        )
        await handler_with_end_session.token_vault.store_token(
            session.session_id, token
        )

        logout_url = await handler_with_end_session.get_logout_url(
            session.session_id,
            OAuthProvider.AZURE,
            post_logout_redirect_uri="https://app.example.com/",
        )

        assert logout_url is not None
        assert (
            "https://login.microsoftonline.com/common/oauth2/v2.0/logout" in logout_url
        )
        assert "id_token_hint=" in logout_url
        assert "post_logout_redirect_uri=https%3A%2F%2Fapp.example.com%2F" in logout_url

    @pytest.mark.asyncio
    async def test_get_logout_url_without_id_token(self, handler_with_end_session):
        """Should return logout URL with client_id when no ID token."""
        session = await handler_with_end_session.session_manager.create_session()

        # Store token without ID token
        token = TokenRecord(
            provider=OAuthProvider.AZURE,
            access_token="test-access-token",
        )
        await handler_with_end_session.token_vault.store_token(
            session.session_id, token
        )

        logout_url = await handler_with_end_session.get_logout_url(
            session.session_id,
            OAuthProvider.AZURE,
        )

        assert logout_url is not None
        assert "client_id=test-client-id" in logout_url
        assert "id_token_hint" not in logout_url

    @pytest.mark.asyncio
    async def test_get_logout_url_no_token(self, handler_with_end_session):
        """Should return logout URL with client_id when no token stored."""
        session = await handler_with_end_session.session_manager.create_session()

        logout_url = await handler_with_end_session.get_logout_url(
            session.session_id,
            OAuthProvider.AZURE,
        )

        assert logout_url is not None
        assert "client_id=test-client-id" in logout_url

    @pytest.mark.asyncio
    async def test_get_logout_url_with_state(self, handler_with_end_session):
        """Should include state parameter when provided."""
        session = await handler_with_end_session.session_manager.create_session()

        logout_url = await handler_with_end_session.get_logout_url(
            session.session_id,
            OAuthProvider.AZURE,
            state="my-state-value",
        )

        assert logout_url is not None
        assert "state=my-state-value" in logout_url

    @pytest.mark.asyncio
    async def test_get_logout_url_no_end_session_endpoint(self, handler_with_provider):
        """Should return None when provider has no end_session_endpoint."""
        session = await handler_with_provider.session_manager.create_session()

        logout_url = await handler_with_provider.get_logout_url(
            session.session_id,
            OAuthProvider.GOOGLE,
        )

        assert logout_url is None

    @pytest.mark.asyncio
    async def test_get_logout_url_provider_not_registered(
        self, handler_with_end_session
    ):
        """Should return None for unregistered provider."""
        session = await handler_with_end_session.session_manager.create_session()

        logout_url = await handler_with_end_session.get_logout_url(
            session.session_id,
            OAuthProvider.GOOGLE,  # Not registered
        )

        assert logout_url is None
