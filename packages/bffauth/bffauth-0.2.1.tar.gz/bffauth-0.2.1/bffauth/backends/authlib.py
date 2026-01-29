"""
Authlib OAuth Backend.

Wraps Authlib's OAuth2Client to provide BFF-specific functionality
including PKCE, state management, and token handling.
"""

import base64
import secrets
from datetime import datetime, timedelta
from typing import Any, cast
from urllib.parse import urlencode

import httpx
from authlib.oauth2.rfc7636 import create_s256_code_challenge

from ..core.exceptions import (
    ConfigurationError,
    StateValidationError,
    TokenExchangeError,
    TokenRefreshError,
)
from ..core.models import (
    AuthorizationResult,
    OAuthState,
    ProviderConfig,
    TokenRecord,
)


class PKCEGenerator:
    """
    PKCE (Proof Key for Code Exchange) generator.

    Implements RFC 7636 for secure authorization code exchange.
    Uses S256 challenge method (SHA-256 hash of verifier).
    """

    @staticmethod
    def generate_verifier(length: int = 64) -> str:
        """
        Generate cryptographically random code verifier.

        Args:
            length: Length of verifier (43-128 characters).

        Returns:
            URL-safe base64 encoded random string.
        """
        if not 43 <= length <= 128:
            raise ValueError("Verifier length must be between 43 and 128")
        return secrets.token_urlsafe(length)[:length]

    @staticmethod
    def generate_challenge(verifier: str) -> str:
        """
        Generate S256 code challenge from verifier.

        Args:
            verifier: Code verifier string.

        Returns:
            Base64url-encoded SHA-256 hash of verifier.
        """
        return cast(str, create_s256_code_challenge(verifier))

    @classmethod
    def generate(cls) -> tuple[str, str]:
        """
        Generate verifier and challenge pair.

        Returns:
            Tuple of (verifier, challenge).
        """
        verifier = cls.generate_verifier()
        challenge = cls.generate_challenge(verifier)
        return verifier, challenge


class AuthlibBackend:
    """
    OAuth backend using Authlib.

    Provides:
    - Authorization URL generation with PKCE
    - Authorization code exchange
    - Token refresh
    - Token revocation
    - OpenID Connect support
    """

    def __init__(
        self,
        config: ProviderConfig,
        http_client: httpx.AsyncClient | None = None,
    ):
        """
        Initialize Authlib backend.

        Args:
            config: Provider configuration.
            http_client: Optional httpx client for requests.
        """
        self.config = config
        self._http_client = http_client
        self._owns_client = http_client is None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client if we own it."""
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def create_authorization_url(
        self,
        redirect_uri: str,
        scope: str | None = None,
        state: str | None = None,
        nonce: str | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> tuple[str, OAuthState]:
        """
        Create authorization URL with PKCE.

        Args:
            redirect_uri: Callback URL for authorization response.
            scope: OAuth scopes. Defaults to config scope.
            state: Optional state parameter. Generated if not provided.
            nonce: Optional nonce for OpenID Connect.
            extra_params: Additional query parameters.

        Returns:
            Tuple of (authorization_url, oauth_state).
        """
        # Generate PKCE
        code_verifier, code_challenge = PKCEGenerator.generate()

        # Generate state if not provided
        if state is None:
            state = secrets.token_urlsafe(32)

        # Generate nonce for OIDC if not provided and using openid scope
        scope = scope or self.config.scope
        if nonce is None and "openid" in scope:
            nonce = secrets.token_urlsafe(32)

        # Build query parameters
        params = {
            "client_id": self.config.client_id,
            "response_type": self.config.response_type,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        if nonce:
            params["nonce"] = nonce

        # Add provider-specific extra params
        params.update(self.config.extra_auth_params)

        # Add caller-provided extra params
        if extra_params:
            params.update(extra_params)

        # Build URL
        auth_url = f"{self.config.authorization_endpoint}?{urlencode(params)}"

        # Create state object for later verification
        oauth_state = OAuthState(
            state=state,
            provider=self.config.provider,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
            scope=scope,
            nonce=nonce,
            extra_params=extra_params or {},
        )

        return auth_url, oauth_state

    async def exchange_code(
        self,
        code: str,
        oauth_state: OAuthState,
    ) -> AuthorizationResult:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback.
            oauth_state: State object from authorization request.

        Returns:
            AuthorizationResult with tokens and optional user info.

        Raises:
            TokenExchangeError: If exchange fails.
        """
        client = await self._get_client()

        # Build token request
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": oauth_state.redirect_uri,
            "client_id": self.config.client_id,
            "code_verifier": oauth_state.code_verifier,
        }

        # Add client secret if configured (confidential client)
        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret

        # Add provider-specific extra params
        data.update(self.config.extra_token_params)

        try:
            response = await client.post(
                self.config.token_endpoint,
                data=data,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            token_data = response.json()
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_body = e.response.json()
                error_detail = error_body.get(
                    "error_description", error_body.get("error", "")
                )
            except Exception:
                error_detail = e.response.text[:200]
            raise TokenExchangeError(
                self.config.provider.value,
                f"HTTP {e.response.status_code}: {error_detail}",
            )
        except Exception as e:
            raise TokenExchangeError(self.config.provider.value, str(e))

        # Parse token response
        token = self._parse_token_response(token_data)

        # Parse ID token claims if present
        id_token_claims = None
        if token.id_token:
            id_token_claims = self._decode_id_token(token.id_token)
            # Verify nonce if present
            if oauth_state.nonce and id_token_claims.get("nonce") != oauth_state.nonce:
                raise StateValidationError("ID token nonce mismatch")

        return AuthorizationResult(
            token=token,
            id_token_claims=id_token_claims,
        )

    async def refresh_token(
        self,
        refresh_token: str,
        scope: str | None = None,
    ) -> TokenRecord:
        """
        Refresh access token.

        Args:
            refresh_token: Refresh token from previous authorization.
            scope: Optional scope for new token (may be reduced).

        Returns:
            New TokenRecord with refreshed access token.

        Raises:
            TokenRefreshError: If refresh fails.
        """
        client = await self._get_client()

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
        }

        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret

        if scope:
            data["scope"] = scope

        try:
            response = await client.post(
                self.config.token_endpoint,
                data=data,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            token_data = response.json()
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_body = e.response.json()
                error_detail = error_body.get(
                    "error_description", error_body.get("error", "")
                )
            except Exception:
                error_detail = e.response.text[:200]
            raise TokenRefreshError(
                self.config.provider.value,
                f"HTTP {e.response.status_code}: {error_detail}",
            )
        except Exception as e:
            raise TokenRefreshError(self.config.provider.value, str(e))

        return self._parse_token_response(token_data)

    async def revoke_token(
        self,
        token: str,
        token_type_hint: str = "access_token",
    ) -> bool:
        """
        Revoke a token.

        Args:
            token: Token to revoke.
            token_type_hint: Type of token ("access_token" or "refresh_token").

        Returns:
            True if revocation was successful.
        """
        if not self.config.revocation_endpoint:
            return False

        client = await self._get_client()

        data = {
            "token": token,
            "token_type_hint": token_type_hint,
            "client_id": self.config.client_id,
        }

        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret

        try:
            response = await client.post(
                self.config.revocation_endpoint,
                data=data,
            )
            # RFC 7009: 200 OK means success, even if token was already revoked
            return response.status_code == 200
        except Exception:
            return False

    async def fetch_userinfo(self, access_token: str) -> dict[str, Any]:
        """
        Fetch user info from userinfo endpoint.

        Args:
            access_token: Valid access token.

        Returns:
            User info claims.
        """
        if not self.config.userinfo_endpoint:
            raise ConfigurationError("Provider has no userinfo endpoint")

        client = await self._get_client()

        response = await client.get(
            self.config.userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    def _parse_token_response(self, data: dict[str, Any]) -> TokenRecord:
        """Parse token response into TokenRecord."""
        from datetime import timezone

        # Calculate expiration time
        expires_at = None
        if "expires_in" in data:
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=int(data["expires_in"])
            )
        elif "expires_at" in data:
            expires_at = datetime.fromtimestamp(data["expires_at"], tz=timezone.utc)

        return TokenRecord(
            provider=self.config.provider,
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=data.get("scope"),
            id_token=data.get("id_token"),
        )

    def _decode_id_token(self, id_token: str) -> dict[str, Any]:
        """
        Decode ID token claims without verification.

        For full verification, use the validate_id_token method
        with JWKS validation.

        Args:
            id_token: JWT ID token.

        Returns:
            Claims from ID token payload.
        """
        try:
            # Split JWT
            parts = id_token.split(".")
            if len(parts) != 3:
                return {}

            # Decode payload (middle part)
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            import json

            decoded = base64.urlsafe_b64decode(payload)
            return cast(dict[str, Any], json.loads(decoded))
        except Exception:
            return {}


class AuthlibBackendFactory:
    """Factory for creating Authlib backends for different providers."""

    _backends: dict[str, AuthlibBackend] = {}
    _http_client: httpx.AsyncClient | None = None

    @classmethod
    async def get_backend(
        cls,
        config: ProviderConfig,
        shared_client: bool = True,
    ) -> AuthlibBackend:
        """
        Get or create backend for provider.

        Args:
            config: Provider configuration.
            shared_client: Share HTTP client across backends.

        Returns:
            AuthlibBackend instance.
        """
        key = config.provider.value

        if key not in cls._backends:
            if shared_client:
                if cls._http_client is None:
                    cls._http_client = httpx.AsyncClient(timeout=30.0)
                cls._backends[key] = AuthlibBackend(config, cls._http_client)
            else:
                cls._backends[key] = AuthlibBackend(config)

        return cls._backends[key]

    @classmethod
    async def close_all(cls) -> None:
        """Close all backends and shared client."""
        for backend in cls._backends.values():
            await backend.close()
        cls._backends.clear()

        if cls._http_client is not None:
            await cls._http_client.aclose()
            cls._http_client = None
