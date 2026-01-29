"""
BFFAuth - OAuth 2.1 + BFF (Backend-for-Frontend) Authentication Library.

A Python library implementing the BFF (Backend-for-Frontend) pattern for OAuth 2.1
authentication, built on top of Authlib.

Features:
- Secure token storage with Fernet encryption
- Session management with __Host- cookie prefix
- CSRF protection
- Multi-provider OAuth support
- PKCE (Proof Key for Code Exchange)
- Resource server allowlist validation
- Automatic token refresh

Quick Start:

    from bffauth import BFFOAuthHandler, OAuthProvider
    from bffauth.providers import create_google_config

    # Create handler
    handler = BFFOAuthHandler(
        encryption_key="your-fernet-encryption-key",
        redirect_base_uri="https://app.example.com",
    )

    # Register provider
    handler.register_provider(create_google_config(
        client_id="your-client-id",
        client_secret="your-client-secret",
    ))

    # Start OAuth flow
    auth_url, session = await handler.start_authorization(OAuthProvider.GOOGLE)

    # Handle callback (after redirect)
    result = await handler.handle_callback(
        session_id=session.session_id,
        code=authorization_code,
        state=state_param,
    )

    # Get access token for API calls
    token = await handler.get_access_token(session_id, OAuthProvider.GOOGLE)
"""

__version__ = "0.1.0"
__author__ = "BFFAuth Contributors"
__license__ = "Apache-2.0"

# Main handler
# Backends
from .backends import (
    AuthlibBackend,
    AuthlibBackendFactory,
    PKCEGenerator,
)

# Core components
from .core import (
    # Models
    AllowedResource,
    # Exceptions
    AllowlistError,
    # Allowlist
    AllowlistValidator,
    AuthorizationError,
    AuthorizationResult,
    BFFAuthError,
    ConfigurationError,
    CSRFValidationError,
    DecryptionError,
    EncryptionError,
    # Session
    InMemorySessionStorage,
    # Vault
    InMemoryVaultStorage,
    InvalidEncryptionKeyError,
    LogoutTokenError,
    OAuthError,
    OAuthProvider,
    OAuthState,
    PKCEError,
    ProviderConfig,
    ProviderNotConfiguredError,
    ProxyRequest,
    ProxyResponse,
    ResourceNotAllowedError,
    SessionData,
    SessionError,
    SessionExpiredError,
    SessionManager,
    SessionNotFoundError,
    SessionStorageProtocol,
    StateValidationError,
    StorageError,
    TokenError,
    TokenExchangeError,
    TokenExpiredError,
    TokenNotFoundError,
    TokenRecord,
    TokenRefreshError,
    TokenRevocationError,
    TokenVault,
    TokenVaultEntry,
    TokenVaultStorageProtocol,
    create_allowlist_from_origins,
    create_common_allowlist,
)
from .handler import BFFOAuthHandler

__all__ = [
    # Version
    "__version__",
    # Main handler
    "BFFOAuthHandler",
    # Allowlist
    "AllowlistValidator",
    "create_allowlist_from_origins",
    "create_common_allowlist",
    # Exceptions
    "AllowlistError",
    "AuthorizationError",
    "BFFAuthError",
    "ConfigurationError",
    "CSRFValidationError",
    "DecryptionError",
    "EncryptionError",
    "InvalidEncryptionKeyError",
    "LogoutTokenError",
    "OAuthError",
    "PKCEError",
    "ProviderNotConfiguredError",
    "ResourceNotAllowedError",
    "SessionError",
    "SessionExpiredError",
    "SessionNotFoundError",
    "StateValidationError",
    "StorageError",
    "TokenError",
    "TokenExchangeError",
    "TokenExpiredError",
    "TokenNotFoundError",
    "TokenRefreshError",
    "TokenRevocationError",
    # Models
    "AllowedResource",
    "AuthorizationResult",
    "OAuthProvider",
    "OAuthState",
    "ProviderConfig",
    "ProxyRequest",
    "ProxyResponse",
    "SessionData",
    "TokenRecord",
    "TokenVaultEntry",
    # Session
    "InMemorySessionStorage",
    "SessionManager",
    "SessionStorageProtocol",
    # Vault
    "InMemoryVaultStorage",
    "TokenVault",
    "TokenVaultStorageProtocol",
    # Backends
    "AuthlibBackend",
    "AuthlibBackendFactory",
    "PKCEGenerator",
]
