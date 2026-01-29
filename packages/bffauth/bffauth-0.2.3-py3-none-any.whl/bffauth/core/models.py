"""
BFFAuth data models using Pydantic.

These models represent OAuth tokens, sessions, and related data structures.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""

    GOOGLE = "google"
    AZURE = "azure"
    GITHUB = "github"
    OKTA = "okta"
    AUTH0 = "auth0"
    KEYCLOAK = "keycloak"
    COGNITO = "cognito"
    SERVICENOW = "servicenow"
    ATLASSIAN = "atlassian"
    CUSTOM = "custom"


class TokenRecord(BaseModel):
    """
    Represents OAuth tokens for a single provider.

    Stores access token, optional refresh token, expiration, and metadata.
    """

    provider: OAuthProvider
    access_token: str = Field(..., min_length=1)
    refresh_token: str | None = None
    token_type: str = Field(default="Bearer")
    expires_at: datetime | None = None
    scope: str | None = None
    id_token: str | None = None
    issued_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """
        Check if access token is expired or will expire soon.

        Args:
            buffer_seconds: Consider expired if within this many seconds of expiry.

        Returns:
            True if token is expired or will expire within buffer.
        """
        if self.expires_at is None:
            return False
        threshold = utc_now() + timedelta(seconds=buffer_seconds)
        return self.expires_at <= threshold

    def time_until_expiry(self) -> timedelta | None:
        """Return time until token expires, or None if no expiry set."""
        if self.expires_at is None:
            return None
        return self.expires_at - utc_now()


class TokenVaultEntry(BaseModel):
    """
    A collection of tokens for multiple providers for a single user/session.

    The vault stores encrypted tokens and supports multi-provider scenarios.
    """

    tokens: dict[str, TokenRecord] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    last_accessed: datetime = Field(default_factory=utc_now)

    def get_token(self, provider: OAuthProvider) -> TokenRecord | None:
        """Get token for a specific provider."""
        return self.tokens.get(provider.value)

    def set_token(self, token: TokenRecord) -> None:
        """Store or update token for a provider."""
        self.tokens[token.provider.value] = token
        self.last_accessed = utc_now()

    def remove_token(self, provider: OAuthProvider) -> bool:
        """Remove token for a provider. Returns True if token existed."""
        if provider.value in self.tokens:
            del self.tokens[provider.value]
            return True
        return False

    def list_providers(self) -> list[OAuthProvider]:
        """List all providers with stored tokens."""
        return [OAuthProvider(p) for p in self.tokens.keys()]

    def clear(self) -> int:
        """Clear all tokens. Returns count of removed tokens."""
        count = len(self.tokens)
        self.tokens.clear()
        return count


class OAuthState(BaseModel):
    """
    OAuth state parameter data stored during authorization flow.

    Contains PKCE verifier and other data needed to complete the flow.
    """

    state: str = Field(..., min_length=32)
    provider: OAuthProvider
    code_verifier: str = Field(..., min_length=43)  # PKCE verifier
    redirect_uri: str
    scope: str | None = None
    nonce: str | None = None  # For OpenID Connect
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime = Field(
        default_factory=lambda: utc_now() + timedelta(minutes=10)
    )
    extra_params: dict[str, str] = Field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if state has expired."""
        return utc_now() >= self.expires_at


class SessionData(BaseModel):
    """
    BFF session data stored server-side.

    Contains CSRF token, user info, and reference to token vault.
    """

    session_id: str = Field(..., min_length=32)
    csrf_token: str = Field(..., min_length=32)
    created_at: datetime = Field(default_factory=utc_now)
    last_activity: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    user_id: str | None = None
    user_info: dict[str, Any] = Field(default_factory=dict)
    authenticated_providers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return utc_now() >= self.expires_at

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = utc_now()

    def add_provider(self, provider: OAuthProvider) -> None:
        """Mark provider as authenticated."""
        if provider.value not in self.authenticated_providers:
            self.authenticated_providers.append(provider.value)

    def remove_provider(self, provider: OAuthProvider) -> None:
        """Remove provider from authenticated list."""
        if provider.value in self.authenticated_providers:
            self.authenticated_providers.remove(provider.value)


class ProviderConfig(BaseModel):
    """
    Configuration for an OAuth provider.

    Contains endpoints, client credentials, and provider-specific settings.
    """

    provider: OAuthProvider
    client_id: str
    client_secret: str | None = None  # Public clients may not have secret
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str | None = None
    revocation_endpoint: str | None = None
    jwks_uri: str | None = None
    issuer: str | None = None
    end_session_endpoint: str | None = None  # OIDC RP-Initiated Logout
    scope: str = "openid email profile"
    response_type: str = "code"
    grant_type: str = "authorization_code"
    use_pkce: bool = True
    extra_auth_params: dict[str, str] = Field(default_factory=dict)
    extra_token_params: dict[str, str] = Field(default_factory=dict)

    @field_validator("authorization_endpoint", "token_endpoint")
    @classmethod
    def validate_https(cls, v: str) -> str:
        """Validate endpoints use HTTPS (except localhost for dev)."""
        if (
            not v.startswith("https://")
            and "localhost" not in v
            and "127.0.0.1" not in v
        ):
            raise ValueError("Endpoint must use HTTPS")
        return v


class AllowedResource(BaseModel):
    """
    An allowed resource server configuration.

    Per IETF draft-ietf-oauth-browser-based-apps section 6.2.4.
    """

    name: str
    url_pattern: str  # Regex pattern for URL matching
    allowed_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE"]
    )
    required_scopes: list[str] = Field(default_factory=list)
    provider: OAuthProvider | None = None  # If specific provider required
    headers_to_forward: list[str] = Field(default_factory=list)
    enabled: bool = True

    @field_validator("url_pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        """Validate the URL pattern is a valid regex."""
        import re

        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid URL pattern regex: {e}")
        return v


class ProxyRequest(BaseModel):
    """
    Request to proxy to a resource server.

    Used by the BFF to forward requests with injected access tokens.
    """

    url: str
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    body: bytes | None = None
    provider: OAuthProvider | None = None  # Which provider's token to use
    timeout: float = 30.0


class ProxyResponse(BaseModel):
    """
    Response from proxied request to resource server.
    """

    status_code: int
    headers: dict[str, str] = Field(default_factory=dict)
    body: bytes = b""
    elapsed_ms: float = 0.0


class AuthorizationResult(BaseModel):
    """
    Result of authorization code exchange.

    Contains tokens and optional user info from ID token.
    """

    token: TokenRecord
    id_token_claims: dict[str, Any] | None = None
    user_info: dict[str, Any] | None = None
