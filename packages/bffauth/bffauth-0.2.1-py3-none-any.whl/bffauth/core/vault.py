"""
BFF Token Vault.

Secure encrypted storage for OAuth tokens with:
- Fernet encryption (AES-128-CBC + HMAC-SHA256)
- Multi-provider support per session
- Automatic token expiration tracking
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, cast

from cryptography.fernet import Fernet, InvalidToken

from .exceptions import (
    DecryptionError,
    EncryptionError,
    InvalidEncryptionKeyError,
    TokenNotFoundError,
)
from .models import OAuthProvider, TokenRecord, TokenVaultEntry, utc_now


class TokenVaultStorageProtocol(ABC):
    """Abstract interface for token vault storage backends."""

    @abstractmethod
    async def get(self, session_id: str) -> bytes | None:
        """Retrieve encrypted vault data by session ID."""
        pass

    @abstractmethod
    async def set(self, session_id: str, data: bytes) -> None:
        """Store encrypted vault data."""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete vault data. Returns True if existed."""
        pass

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """Check if vault exists for session."""
        pass


class InMemoryVaultStorage(TokenVaultStorageProtocol):
    """
    In-memory token vault storage for development/testing.

    NOT suitable for production multi-instance deployments.
    Use Redis or database storage for production.
    """

    def __init__(self) -> None:
        self._vaults: dict[str, bytes] = {}

    async def get(self, session_id: str) -> bytes | None:
        """Retrieve encrypted vault data."""
        return self._vaults.get(session_id)

    async def set(self, session_id: str, data: bytes) -> None:
        """Store encrypted vault data."""
        self._vaults[session_id] = data

    async def delete(self, session_id: str) -> bool:
        """Delete vault data."""
        if session_id in self._vaults:
            del self._vaults[session_id]
            return True
        return False

    async def exists(self, session_id: str) -> bool:
        """Check if vault exists."""
        return session_id in self._vaults


class TokenVault:
    """
    Encrypted token vault for BFF pattern.

    Stores OAuth tokens encrypted at rest using Fernet symmetric encryption.
    Supports multiple providers per session for multi-provider scenarios.

    Security features:
    - AES-128-CBC encryption with HMAC-SHA256 authentication
    - Tokens never exposed to frontend
    - Session-bound token storage
    """

    def __init__(
        self,
        encryption_key: str,
        storage: TokenVaultStorageProtocol | None = None,
        token_refresh_buffer: int = 300,
    ):
        """
        Initialize token vault.

        Args:
            encryption_key: Fernet encryption key (base64-encoded 32 bytes).
            storage: Storage backend. Defaults to in-memory.
            token_refresh_buffer: Seconds before expiry to consider token expired.

        Raises:
            InvalidEncryptionKeyError: If encryption key is invalid.
        """
        self.storage = storage or InMemoryVaultStorage()
        self.token_refresh_buffer = token_refresh_buffer

        # Validate and initialize Fernet cipher
        try:
            key_bytes = (
                encryption_key.encode()
                if isinstance(encryption_key, str)
                else encryption_key
            )
            self._cipher = Fernet(key_bytes)
        except (ValueError, TypeError) as e:
            raise InvalidEncryptionKeyError() from e

    def _encrypt(self, data: dict[str, Any]) -> bytes:
        """Encrypt dictionary data."""
        try:
            json_bytes = json.dumps(data, default=str).encode("utf-8")
            encrypted: bytes = self._cipher.encrypt(json_bytes)
            return encrypted
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data: {e}")

    def _decrypt(self, encrypted_data: bytes) -> dict[str, Any]:
        """Decrypt data to dictionary."""
        try:
            decrypted_bytes = self._cipher.decrypt(encrypted_data)
            return cast(dict[str, Any], json.loads(decrypted_bytes.decode("utf-8")))
        except InvalidToken:
            raise DecryptionError("Invalid encryption key or corrupted data")
        except Exception as e:
            raise DecryptionError(f"Decryption failed: {e}")

    def _serialize_vault(self, vault: TokenVaultEntry) -> dict[str, Any]:
        """Serialize vault to dict for encryption."""
        return {
            "tokens": {
                provider: {
                    "provider": token.provider.value,
                    "access_token": token.access_token,
                    "refresh_token": token.refresh_token,
                    "token_type": token.token_type,
                    "expires_at": (
                        token.expires_at.isoformat() if token.expires_at else None
                    ),
                    "scope": token.scope,
                    "id_token": token.id_token,
                    "issued_at": token.issued_at.isoformat(),
                    "metadata": token.metadata,
                }
                for provider, token in vault.tokens.items()
            },
            "created_at": vault.created_at.isoformat(),
            "last_accessed": vault.last_accessed.isoformat(),
        }

    def _deserialize_vault(self, data: dict[str, Any]) -> TokenVaultEntry:
        """Deserialize dict to vault."""
        tokens = {}
        for provider, token_data in data.get("tokens", {}).items():
            tokens[provider] = TokenRecord(
                provider=OAuthProvider(token_data["provider"]),
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type=token_data.get("token_type", "Bearer"),
                expires_at=(
                    datetime.fromisoformat(token_data["expires_at"])
                    if token_data.get("expires_at")
                    else None
                ),
                scope=token_data.get("scope"),
                id_token=token_data.get("id_token"),
                issued_at=datetime.fromisoformat(token_data["issued_at"]),
                metadata=token_data.get("metadata", {}),
            )

        return TokenVaultEntry(
            tokens=tokens,
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
        )

    async def get_vault(self, session_id: str) -> TokenVaultEntry:
        """
        Get or create token vault for session.

        Args:
            session_id: Session identifier.

        Returns:
            TokenVaultEntry for the session.
        """
        encrypted_data = await self.storage.get(session_id)
        if encrypted_data is None:
            return TokenVaultEntry()

        data = self._decrypt(encrypted_data)
        return self._deserialize_vault(data)

    async def save_vault(self, session_id: str, vault: TokenVaultEntry) -> None:
        """
        Save token vault for session.

        Args:
            session_id: Session identifier.
            vault: Token vault to save.
        """
        vault.last_accessed = utc_now()
        data = self._serialize_vault(vault)
        encrypted_data = self._encrypt(data)
        await self.storage.set(session_id, encrypted_data)

    async def store_token(
        self,
        session_id: str,
        token: TokenRecord,
    ) -> None:
        """
        Store token for provider in session's vault.

        Args:
            session_id: Session identifier.
            token: Token record to store.
        """
        vault = await self.get_vault(session_id)
        vault.set_token(token)
        await self.save_vault(session_id, vault)

    async def get_token(
        self,
        session_id: str,
        provider: OAuthProvider,
    ) -> TokenRecord:
        """
        Get token for provider from session's vault.

        Args:
            session_id: Session identifier.
            provider: OAuth provider.

        Returns:
            TokenRecord for the provider.

        Raises:
            TokenNotFoundError: If no token exists for provider.
        """
        vault = await self.get_vault(session_id)
        token = vault.get_token(provider)
        if token is None:
            raise TokenNotFoundError(provider.value)
        return token

    async def get_valid_token(
        self,
        session_id: str,
        provider: OAuthProvider,
    ) -> TokenRecord | None:
        """
        Get token if it exists and is not expired.

        Args:
            session_id: Session identifier.
            provider: OAuth provider.

        Returns:
            TokenRecord if valid, None if expired or not found.
        """
        try:
            token = await self.get_token(session_id, provider)
            if token.is_expired(buffer_seconds=self.token_refresh_buffer):
                return None
            return token
        except TokenNotFoundError:
            return None

    async def delete_token(
        self,
        session_id: str,
        provider: OAuthProvider,
    ) -> bool:
        """
        Delete token for provider from session's vault.

        Args:
            session_id: Session identifier.
            provider: OAuth provider.

        Returns:
            True if token existed and was deleted.
        """
        vault = await self.get_vault(session_id)
        removed = vault.remove_token(provider)
        if removed:
            await self.save_vault(session_id, vault)
        return removed

    async def list_providers(self, session_id: str) -> list[OAuthProvider]:
        """
        List providers with tokens in session's vault.

        Args:
            session_id: Session identifier.

        Returns:
            List of providers with stored tokens.
        """
        vault = await self.get_vault(session_id)
        return vault.list_providers()

    async def clear_vault(self, session_id: str) -> int:
        """
        Clear all tokens for session.

        Args:
            session_id: Session identifier.

        Returns:
            Number of tokens removed.
        """
        vault = await self.get_vault(session_id)
        count = vault.clear()
        await self.storage.delete(session_id)
        return count

    async def delete_vault(self, session_id: str) -> bool:
        """
        Delete entire vault for session.

        Args:
            session_id: Session identifier.

        Returns:
            True if vault existed.
        """
        return await self.storage.delete(session_id)

    async def update_token(
        self,
        session_id: str,
        provider: OAuthProvider,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
    ) -> TokenRecord:
        """
        Update existing token with new values.

        Useful for token refresh where you want to preserve metadata.

        Args:
            session_id: Session identifier.
            provider: OAuth provider.
            access_token: New access token.
            refresh_token: New refresh token (if rotated).
            expires_at: New expiration time.

        Returns:
            Updated TokenRecord.

        Raises:
            TokenNotFoundError: If no existing token.
        """
        token = await self.get_token(session_id, provider)

        # Update token with new values
        token.access_token = access_token
        if refresh_token is not None:
            token.refresh_token = refresh_token
        if expires_at is not None:
            token.expires_at = expires_at
        token.issued_at = utc_now()

        await self.store_token(session_id, token)
        return token
