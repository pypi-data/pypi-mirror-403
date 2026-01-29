"""
BFFAuth Core Components.

This module provides the core building blocks for BFF authentication:
- Session management with CSRF protection
- Encrypted token vault
- Resource server allowlist validation
- Data models and exceptions
"""

from .allowlist import (
    AllowlistValidator,
    create_allowlist_from_origins,
    create_common_allowlist,
)
from .exceptions import (
    AllowlistError,
    AuthorizationError,
    BFFAuthError,
    ConfigurationError,
    CSRFValidationError,
    DecryptionError,
    EncryptionError,
    InvalidEncryptionKeyError,
    LogoutTokenError,
    OAuthError,
    PKCEError,
    ProviderNotConfiguredError,
    ResourceNotAllowedError,
    SessionError,
    SessionExpiredError,
    SessionNotFoundError,
    StateValidationError,
    StorageError,
    StorageReadError,
    StorageUnavailableError,
    StorageWriteError,
    TokenError,
    TokenExchangeError,
    TokenExpiredError,
    TokenNotFoundError,
    TokenRefreshError,
    TokenRevocationError,
)
from .models import (
    AllowedResource,
    AuthorizationResult,
    OAuthProvider,
    OAuthState,
    ProviderConfig,
    ProxyRequest,
    ProxyResponse,
    SessionData,
    TokenRecord,
    TokenVaultEntry,
)
from .session import (
    InMemorySessionStorage,
    SessionManager,
    SessionStorageProtocol,
)
from .vault import (
    InMemoryVaultStorage,
    TokenVault,
    TokenVaultStorageProtocol,
)

__all__ = [
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
    "StorageReadError",
    "StorageUnavailableError",
    "StorageWriteError",
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
]
