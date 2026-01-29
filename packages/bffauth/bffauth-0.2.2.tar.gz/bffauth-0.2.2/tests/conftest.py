"""
Pytest configuration and shared fixtures.
"""

import pytest
from cryptography.fernet import Fernet


@pytest.fixture
def encryption_key():
    """Generate a valid Fernet encryption key for testing."""
    return Fernet.generate_key().decode()


@pytest.fixture
def mock_provider_config():
    """Create mock provider configuration."""
    from bffauth.core.models import OAuthProvider, ProviderConfig

    return ProviderConfig(
        provider=OAuthProvider.GOOGLE,
        client_id="test-client-id",
        client_secret="test-client-secret",
        authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint="https://oauth2.googleapis.com/token",
        userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
        scope="openid email profile",
    )
