"""
BFFAuth exception hierarchy.

All exceptions inherit from BFFAuthError for easy catching.
"""

from typing import Any


class BFFAuthError(Exception):
    """Base exception for all BFFAuth errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(BFFAuthError):
    """Raised when configuration is invalid or missing."""

    pass


class ProviderNotConfiguredError(ConfigurationError):
    """Raised when attempting to use an unconfigured OAuth provider."""

    def __init__(self, provider: str):
        super().__init__(
            f"OAuth provider '{provider}' is not configured", {"provider": provider}
        )
        self.provider = provider


# =============================================================================
# Session Errors
# =============================================================================


class SessionError(BFFAuthError):
    """Base exception for session-related errors."""

    pass


class SessionNotFoundError(SessionError):
    """Raised when session cannot be found or has expired."""

    def __init__(self, session_id: str | None = None):
        message = "Session not found or expired"
        if session_id:
            message = f"Session '{session_id[:8]}...' not found or expired"
        super().__init__(message)


class SessionExpiredError(SessionError):
    """Raised when session has expired."""

    def __init__(self, message: str = "Session has expired") -> None:
        super().__init__(message)


class CSRFValidationError(SessionError):
    """Raised when CSRF token validation fails."""

    def __init__(self, reason: str = "CSRF token mismatch"):
        super().__init__(f"CSRF validation failed: {reason}")


# =============================================================================
# Token Errors
# =============================================================================


class TokenError(BFFAuthError):
    """Base exception for token-related errors."""

    pass


class TokenNotFoundError(TokenError):
    """Raised when token is not found in storage."""

    def __init__(self, provider: str | None = None):
        message = "Token not found"
        if provider:
            message = f"Token for provider '{provider}' not found"
        super().__init__(message)
        self.provider = provider


class TokenExpiredError(TokenError):
    """Raised when access token has expired and refresh is needed."""

    def __init__(self, provider: str | None = None):
        message = "Access token has expired"
        if provider:
            message = f"Access token for '{provider}' has expired"
        super().__init__(message)
        self.provider = provider


class TokenRefreshError(TokenError):
    """Raised when token refresh fails."""

    def __init__(self, provider: str, reason: str):
        super().__init__(
            f"Failed to refresh token for '{provider}': {reason}",
            {"provider": provider, "reason": reason},
        )
        self.provider = provider
        self.reason = reason


class TokenRevocationError(TokenError):
    """Raised when token revocation fails."""

    pass


# =============================================================================
# Encryption Errors
# =============================================================================


class EncryptionError(BFFAuthError):
    """Raised when encryption/decryption operations fail."""

    pass


class InvalidEncryptionKeyError(EncryptionError):
    """Raised when encryption key is invalid."""

    def __init__(self) -> None:
        super().__init__(
            "Invalid encryption key. "
            "Must be a valid Fernet key (32 url-safe base64 bytes)"
        )


class DecryptionError(EncryptionError):
    """Raised when decryption fails (wrong key or corrupted data)."""

    def __init__(self, reason: str = "Decryption failed"):
        super().__init__(f"Failed to decrypt token data: {reason}")


# =============================================================================
# OAuth Flow Errors
# =============================================================================


class OAuthError(BFFAuthError):
    """Base exception for OAuth flow errors."""

    pass


class AuthorizationError(OAuthError):
    """Raised when authorization fails."""

    def __init__(self, error: str, error_description: str | None = None):
        message = f"Authorization failed: {error}"
        if error_description:
            message = f"{message} - {error_description}"
        super().__init__(
            message, {"error": error, "error_description": error_description}
        )
        self.error = error
        self.error_description = error_description


class StateValidationError(OAuthError):
    """Raised when OAuth state parameter validation fails."""

    def __init__(self, reason: str = "State mismatch"):
        super().__init__(f"OAuth state validation failed: {reason}")


class TokenExchangeError(OAuthError):
    """Raised when authorization code exchange fails."""

    def __init__(self, provider: str, reason: str):
        super().__init__(
            f"Token exchange failed for '{provider}': {reason}",
            {"provider": provider, "reason": reason},
        )
        self.provider = provider
        self.reason = reason


class PKCEError(OAuthError):
    """Raised when PKCE verification fails."""

    pass


class LogoutTokenError(OAuthError):
    """Raised when back-channel logout token validation fails."""

    def __init__(self, reason: str):
        super().__init__(f"Logout token validation failed: {reason}")
        self.reason = reason


# =============================================================================
# Allowlist Errors
# =============================================================================


class AllowlistError(BFFAuthError):
    """Base exception for allowlist validation errors."""

    pass


class ResourceNotAllowedError(AllowlistError):
    """Raised when resource server is not in allowlist."""

    def __init__(self, url: str):
        super().__init__(f"Resource server not allowed: {url}", {"url": url})
        self.url = url


# =============================================================================
# Storage Errors
# =============================================================================


class StorageError(BFFAuthError):
    """Base exception for storage backend errors."""

    pass


class StorageUnavailableError(StorageError):
    """Raised when storage backend is unavailable."""

    pass


class StorageWriteError(StorageError):
    """Raised when write to storage fails."""

    pass


class StorageReadError(StorageError):
    """Raised when read from storage fails."""

    pass
