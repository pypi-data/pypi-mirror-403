"""
Unit tests for token vault.
"""

from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet

from bffauth.core.exceptions import (
    DecryptionError,
    InvalidEncryptionKeyError,
    TokenNotFoundError,
)
from bffauth.core.models import OAuthProvider, TokenRecord
from bffauth.core.vault import InMemoryVaultStorage, TokenVault


class TestTokenVault:
    """Test TokenVault functionality."""

    @pytest.fixture
    def encryption_key(self):
        """Generate valid Fernet key."""
        return Fernet.generate_key().decode()

    @pytest.fixture
    def vault(self, encryption_key):
        """Create token vault."""
        return TokenVault(encryption_key=encryption_key)

    @pytest.fixture
    def token_record(self):
        """Create sample token record."""
        return TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="ya29.test-access-token",
            refresh_token="1//test-refresh-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scope="openid email",
        )

    def test_invalid_encryption_key(self):
        """Should reject invalid encryption key."""
        with pytest.raises(InvalidEncryptionKeyError):
            TokenVault(encryption_key="invalid-key")

    @pytest.mark.asyncio
    async def test_store_and_get_token(self, vault, token_record):
        """Should store and retrieve token."""
        await vault.store_token("session-123", token_record)
        retrieved = await vault.get_token("session-123", OAuthProvider.GOOGLE)

        assert retrieved.access_token == token_record.access_token
        assert retrieved.refresh_token == token_record.refresh_token
        assert retrieved.scope == token_record.scope

    @pytest.mark.asyncio
    async def test_get_token_not_found(self, vault):
        """Should raise TokenNotFoundError for unknown provider."""
        with pytest.raises(TokenNotFoundError):
            await vault.get_token("session-123", OAuthProvider.GOOGLE)

    @pytest.mark.asyncio
    async def test_get_valid_token(self, vault, token_record):
        """Should return valid (non-expired) token."""
        await vault.store_token("session-123", token_record)
        token = await vault.get_valid_token("session-123", OAuthProvider.GOOGLE)

        assert token is not None
        assert token.access_token == token_record.access_token

    @pytest.mark.asyncio
    async def test_get_valid_token_expired(self, vault):
        """Should return None for expired token."""
        expired_token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="expired-token",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        await vault.store_token("session-123", expired_token)
        token = await vault.get_valid_token("session-123", OAuthProvider.GOOGLE)

        assert token is None

    @pytest.mark.asyncio
    async def test_delete_token(self, vault, token_record):
        """Should delete token."""
        await vault.store_token("session-123", token_record)
        deleted = await vault.delete_token("session-123", OAuthProvider.GOOGLE)

        assert deleted is True

        with pytest.raises(TokenNotFoundError):
            await vault.get_token("session-123", OAuthProvider.GOOGLE)

    @pytest.mark.asyncio
    async def test_delete_token_not_found(self, vault):
        """Should return False for nonexistent token."""
        deleted = await vault.delete_token("session-123", OAuthProvider.GOOGLE)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_providers(self, vault):
        """Should list all providers with tokens."""
        google_token = TokenRecord(
            provider=OAuthProvider.GOOGLE,
            access_token="google-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        azure_token = TokenRecord(
            provider=OAuthProvider.AZURE,
            access_token="azure-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        await vault.store_token("session-123", google_token)
        await vault.store_token("session-123", azure_token)

        providers = await vault.list_providers("session-123")

        assert OAuthProvider.GOOGLE in providers
        assert OAuthProvider.AZURE in providers

    @pytest.mark.asyncio
    async def test_list_providers_empty(self, vault):
        """Should return empty list for session without tokens."""
        providers = await vault.list_providers("session-123")
        assert providers == []

    @pytest.mark.asyncio
    async def test_clear_vault(self, vault, token_record):
        """Should clear all tokens for session."""
        await vault.store_token("session-123", token_record)
        count = await vault.clear_vault("session-123")

        assert count == 1
        assert await vault.list_providers("session-123") == []

    @pytest.mark.asyncio
    async def test_update_token(self, vault, token_record):
        """Should update existing token."""
        await vault.store_token("session-123", token_record)

        updated = await vault.update_token(
            "session-123",
            OAuthProvider.GOOGLE,
            access_token="new-access-token",
            refresh_token="new-refresh-token",
        )

        assert updated.access_token == "new-access-token"
        assert updated.refresh_token == "new-refresh-token"

        # Verify persistence
        retrieved = await vault.get_token("session-123", OAuthProvider.GOOGLE)
        assert retrieved.access_token == "new-access-token"

    @pytest.mark.asyncio
    async def test_encryption_works(self, encryption_key, token_record):
        """Should encrypt token data at rest."""
        storage = InMemoryVaultStorage()
        vault = TokenVault(encryption_key=encryption_key, storage=storage)

        await vault.store_token("session-123", token_record)

        # Get raw encrypted data
        raw_data = await storage.get("session-123")

        # Should not contain plaintext token
        assert b"ya29.test-access-token" not in raw_data
        assert b"1//test-refresh-token" not in raw_data

    @pytest.mark.asyncio
    async def test_wrong_key_fails(self, encryption_key, token_record):
        """Should fail to decrypt with wrong key."""
        storage = InMemoryVaultStorage()
        vault1 = TokenVault(encryption_key=encryption_key, storage=storage)

        await vault1.store_token("session-123", token_record)

        # Create vault with different key
        different_key = Fernet.generate_key().decode()
        vault2 = TokenVault(encryption_key=different_key, storage=storage)

        with pytest.raises(DecryptionError):
            await vault2.get_token("session-123", OAuthProvider.GOOGLE)


class TestInMemoryVaultStorage:
    """Test InMemoryVaultStorage."""

    @pytest.fixture
    def storage(self):
        """Create storage instance."""
        return InMemoryVaultStorage()

    @pytest.mark.asyncio
    async def test_set_and_get(self, storage):
        """Should store and retrieve data."""
        await storage.set("key-1", b"encrypted-data")
        data = await storage.get("key-1")

        assert data == b"encrypted-data"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, storage):
        """Should return None for nonexistent key."""
        data = await storage.get("nonexistent")
        assert data is None

    @pytest.mark.asyncio
    async def test_delete(self, storage):
        """Should delete data."""
        await storage.set("key-1", b"data")
        deleted = await storage.delete("key-1")

        assert deleted is True
        assert await storage.get("key-1") is None

    @pytest.mark.asyncio
    async def test_exists(self, storage):
        """Should check if key exists."""
        await storage.set("key-1", b"data")

        assert await storage.exists("key-1") is True
        assert await storage.exists("nonexistent") is False
