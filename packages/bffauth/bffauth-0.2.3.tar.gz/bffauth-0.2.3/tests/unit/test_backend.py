"""
Unit tests for Authlib OAuth Backend.
"""

import base64
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bffauth.backends.authlib import (
    AuthlibBackend,
    AuthlibBackendFactory,
    PKCEGenerator,
)
from bffauth.core.exceptions import (
    ConfigurationError,
    StateValidationError,
    TokenExchangeError,
    TokenRefreshError,
)
from bffauth.core.models import (
    OAuthProvider,
    OAuthState,
    ProviderConfig,
)


class TestPKCEGenerator:
    """Test PKCE generation."""

    def test_generate_verifier(self):
        """Should generate verifier of correct length."""
        verifier = PKCEGenerator.generate_verifier(64)
        assert len(verifier) == 64

    def test_generate_verifier_min_length(self):
        """Should generate verifier at minimum length."""
        verifier = PKCEGenerator.generate_verifier(43)
        assert len(verifier) == 43

    def test_generate_verifier_max_length(self):
        """Should generate verifier at maximum length."""
        verifier = PKCEGenerator.generate_verifier(128)
        assert len(verifier) == 128

    def test_generate_verifier_invalid_length_too_short(self):
        """Should reject verifier length below 43."""
        with pytest.raises(ValueError, match="43 and 128"):
            PKCEGenerator.generate_verifier(42)

    def test_generate_verifier_invalid_length_too_long(self):
        """Should reject verifier length above 128."""
        with pytest.raises(ValueError, match="43 and 128"):
            PKCEGenerator.generate_verifier(129)

    def test_generate_challenge(self):
        """Should generate valid S256 challenge."""
        verifier = "test_verifier_string_that_is_long_enough_for_pkce_validation"
        challenge = PKCEGenerator.generate_challenge(verifier)

        # Challenge should be base64url encoded
        assert challenge is not None
        assert len(challenge) > 0

    def test_generate_pair(self):
        """Should generate matching verifier and challenge pair."""
        verifier, challenge = PKCEGenerator.generate()

        assert len(verifier) == 64  # Default length
        assert challenge is not None

        # Verify challenge matches verifier
        expected_challenge = PKCEGenerator.generate_challenge(verifier)
        assert challenge == expected_challenge

    def test_verifier_uniqueness(self):
        """Should generate unique verifiers."""
        verifiers = [PKCEGenerator.generate_verifier() for _ in range(100)]
        assert len(set(verifiers)) == 100


class TestAuthlibBackend:
    """Test AuthlibBackend functionality."""

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
            revocation_endpoint="https://oauth2.googleapis.com/revoke",
            scope="openid email profile",
        )

    @pytest.fixture
    def backend(self, provider_config):
        """Create backend instance."""
        return AuthlibBackend(provider_config)

    def test_initialization(self, backend, provider_config):
        """Should initialize with config."""
        assert backend.config == provider_config
        assert backend._http_client is None
        assert backend._owns_client is True

    def test_initialization_with_client(self, provider_config):
        """Should use provided HTTP client."""
        mock_client = MagicMock(spec=httpx.AsyncClient)
        backend = AuthlibBackend(provider_config, http_client=mock_client)

        assert backend._http_client == mock_client
        assert backend._owns_client is False

    def test_create_authorization_url(self, backend):
        """Should create authorization URL with PKCE."""
        redirect_uri = "https://app.example.com/callback"

        auth_url, oauth_state = backend.create_authorization_url(
            redirect_uri=redirect_uri,
        )

        # Check URL components
        assert auth_url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
        assert "client_id=test-client-id" in auth_url
        assert "redirect_uri=" in auth_url
        assert "code_challenge=" in auth_url
        assert "code_challenge_method=S256" in auth_url
        assert "state=" in auth_url

        # Check state object
        assert oauth_state.provider == OAuthProvider.GOOGLE
        assert oauth_state.redirect_uri == redirect_uri
        assert len(oauth_state.code_verifier) >= 43
        assert len(oauth_state.state) >= 32

    def test_create_authorization_url_with_nonce(self, backend):
        """Should include nonce for OIDC."""
        auth_url, oauth_state = backend.create_authorization_url(
            redirect_uri="https://app.example.com/callback",
            scope="openid email",
        )

        assert "nonce=" in auth_url
        assert oauth_state.nonce is not None

    def test_create_authorization_url_custom_scope(self, backend):
        """Should use custom scope."""
        auth_url, oauth_state = backend.create_authorization_url(
            redirect_uri="https://app.example.com/callback",
            scope="custom_scope",
        )

        assert "scope=custom_scope" in auth_url
        assert oauth_state.scope == "custom_scope"

    def test_create_authorization_url_extra_params(self, backend):
        """Should include extra parameters."""
        auth_url, oauth_state = backend.create_authorization_url(
            redirect_uri="https://app.example.com/callback",
            extra_params={"prompt": "consent", "access_type": "offline"},
        )

        assert "prompt=consent" in auth_url
        assert "access_type=offline" in auth_url

    def test_create_authorization_url_custom_state(self, backend):
        """Should use provided state."""
        custom_state = "a" * 32
        auth_url, oauth_state = backend.create_authorization_url(
            redirect_uri="https://app.example.com/callback",
            state=custom_state,
        )

        assert f"state={custom_state}" in auth_url
        assert oauth_state.state == custom_state

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, backend):
        """Should exchange code for tokens."""
        oauth_state = OAuthState(
            state="a" * 32,
            provider=OAuthProvider.GOOGLE,
            code_verifier="b" * 50,
            redirect_uri="https://app.example.com/callback",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "openid email profile",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await backend.exchange_code("auth-code", oauth_state)

            assert result.token.access_token == "test-access-token"
            assert result.token.refresh_token == "test-refresh-token"
            assert result.token.provider == OAuthProvider.GOOGLE

    @pytest.mark.asyncio
    async def test_exchange_code_with_id_token(self, backend):
        """Should parse ID token claims."""
        oauth_state = OAuthState(
            state="a" * 32,
            provider=OAuthProvider.GOOGLE,
            code_verifier="b" * 50,
            redirect_uri="https://app.example.com/callback",
            nonce="test-nonce",
        )

        # Create a mock ID token
        header = (
            base64.urlsafe_b64encode(json.dumps({"alg": "RS256"}).encode())
            .decode()
            .rstrip("=")
        )
        payload = (
            base64.urlsafe_b64encode(
                json.dumps(
                    {
                        "sub": "user-123",
                        "email": "test@example.com",
                        "nonce": "test-nonce",
                    }
                ).encode()
            )
            .decode()
            .rstrip("=")
        )
        signature = "mock_signature"
        id_token = f"{header}.{payload}.{signature}"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "id_token": id_token,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await backend.exchange_code("auth-code", oauth_state)

            assert result.id_token_claims is not None
            assert result.id_token_claims["sub"] == "user-123"
            assert result.id_token_claims["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_exchange_code_nonce_mismatch(self, backend):
        """Should reject ID token with mismatched nonce."""
        oauth_state = OAuthState(
            state="a" * 32,
            provider=OAuthProvider.GOOGLE,
            code_verifier="b" * 50,
            redirect_uri="https://app.example.com/callback",
            nonce="expected-nonce",
        )

        # Create ID token with wrong nonce
        header = (
            base64.urlsafe_b64encode(json.dumps({"alg": "RS256"}).encode())
            .decode()
            .rstrip("=")
        )
        payload = (
            base64.urlsafe_b64encode(
                json.dumps(
                    {
                        "sub": "user-123",
                        "nonce": "wrong-nonce",
                    }
                ).encode()
            )
            .decode()
            .rstrip("=")
        )
        id_token = f"{header}.{payload}.signature"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "id_token": id_token,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            with pytest.raises(StateValidationError, match="nonce"):
                await backend.exchange_code("auth-code", oauth_state)

    @pytest.mark.asyncio
    async def test_exchange_code_http_error(self, backend):
        """Should raise TokenExchangeError on HTTP error."""
        oauth_state = OAuthState(
            state="a" * 32,
            provider=OAuthProvider.GOOGLE,
            code_verifier="b" * 50,
            redirect_uri="https://app.example.com/callback",
        )

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Code expired",
        }
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            with pytest.raises(TokenExchangeError):
                await backend.exchange_code("auth-code", oauth_state)

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, backend):
        """Should refresh access token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            token = await backend.refresh_token("old-refresh-token")

            assert token.access_token == "new-access-token"
            assert token.refresh_token == "new-refresh-token"

    @pytest.mark.asyncio
    async def test_refresh_token_http_error(self, backend):
        """Should raise TokenRefreshError on HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid_grant"}
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            with pytest.raises(TokenRefreshError):
                await backend.refresh_token("invalid-refresh-token")

    @pytest.mark.asyncio
    async def test_revoke_token_success(self, backend):
        """Should revoke token successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await backend.revoke_token("test-token")

            assert result is True

    @pytest.mark.asyncio
    async def test_revoke_token_no_endpoint(self, provider_config):
        """Should return False if no revocation endpoint."""
        provider_config.revocation_endpoint = None
        backend = AuthlibBackend(provider_config)

        result = await backend.revoke_token("test-token")

        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_token_error(self, backend):
        """Should return False on error."""
        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Network error")
            mock_get_client.return_value = mock_client

            result = await backend.revoke_token("test-token")

            assert result is False

    @pytest.mark.asyncio
    async def test_fetch_userinfo_success(self, backend):
        """Should fetch user info."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sub": "user-123",
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(backend, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            userinfo = await backend.fetch_userinfo("test-access-token")

            assert userinfo["sub"] == "user-123"
            assert userinfo["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_fetch_userinfo_no_endpoint(self, provider_config):
        """Should raise ConfigurationError if no userinfo endpoint."""
        provider_config.userinfo_endpoint = None
        backend = AuthlibBackend(provider_config)

        with pytest.raises(ConfigurationError, match="userinfo"):
            await backend.fetch_userinfo("test-token")

    @pytest.mark.asyncio
    async def test_close_owned_client(self, backend):
        """Should close owned HTTP client."""
        # Force client creation
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        backend._http_client = mock_client
        backend._owns_client = True

        await backend.close()

        mock_client.aclose.assert_called_once()
        assert backend._http_client is None

    @pytest.mark.asyncio
    async def test_close_external_client(self, provider_config):
        """Should not close external HTTP client."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        backend = AuthlibBackend(provider_config, http_client=mock_client)

        await backend.close()

        # Should not close external client
        mock_client.aclose.assert_not_called()

    def test_decode_id_token_valid(self, backend):
        """Should decode valid ID token."""
        header = (
            base64.urlsafe_b64encode(json.dumps({"alg": "RS256"}).encode())
            .decode()
            .rstrip("=")
        )
        payload = (
            base64.urlsafe_b64encode(
                json.dumps(
                    {
                        "sub": "user-123",
                        "email": "test@example.com",
                    }
                ).encode()
            )
            .decode()
            .rstrip("=")
        )
        id_token = f"{header}.{payload}.signature"

        claims = backend._decode_id_token(id_token)

        assert claims["sub"] == "user-123"
        assert claims["email"] == "test@example.com"

    def test_decode_id_token_invalid(self, backend):
        """Should return empty dict for invalid ID token."""
        claims = backend._decode_id_token("invalid-token")
        assert claims == {}

    def test_parse_token_response_with_expires_in(self, backend):
        """Should calculate expires_at from expires_in."""
        data = {
            "access_token": "test-token",
            "expires_in": 3600,
        }

        token = backend._parse_token_response(data)

        assert token.expires_at is not None
        # Should be approximately 1 hour from now
        expected = datetime.now(timezone.utc) + timedelta(hours=1)
        assert abs((token.expires_at - expected).total_seconds()) < 5

    def test_parse_token_response_with_expires_at(self, backend):
        """Should use expires_at timestamp."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)
        data = {
            "access_token": "test-token",
            "expires_at": future_time.timestamp(),
        }

        token = backend._parse_token_response(data)

        assert token.expires_at is not None


class TestAuthlibBackendFactory:
    """Test AuthlibBackendFactory."""

    @pytest.fixture
    def provider_config(self):
        """Create test provider configuration."""
        return ProviderConfig(
            provider=OAuthProvider.GOOGLE,
            client_id="test-client-id",
            client_secret="test-client-secret",
            authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
        )

    @pytest.fixture(autouse=True)
    async def cleanup_factory(self):
        """Clean up factory after each test."""
        yield
        await AuthlibBackendFactory.close_all()

    @pytest.mark.asyncio
    async def test_get_backend_creates_new(self, provider_config):
        """Should create new backend for new provider."""
        backend = await AuthlibBackendFactory.get_backend(provider_config)

        assert backend is not None
        assert backend.config == provider_config

    @pytest.mark.asyncio
    async def test_get_backend_reuses_existing(self, provider_config):
        """Should reuse existing backend for same provider."""
        backend1 = await AuthlibBackendFactory.get_backend(provider_config)
        backend2 = await AuthlibBackendFactory.get_backend(provider_config)

        assert backend1 is backend2

    @pytest.mark.asyncio
    async def test_close_all(self, provider_config):
        """Should close all backends."""
        await AuthlibBackendFactory.get_backend(provider_config)

        await AuthlibBackendFactory.close_all()

        assert len(AuthlibBackendFactory._backends) == 0
        assert AuthlibBackendFactory._http_client is None
