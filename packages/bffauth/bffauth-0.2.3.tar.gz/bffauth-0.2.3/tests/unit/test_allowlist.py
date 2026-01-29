"""
Unit tests for allowlist validation.
"""

import pytest

from bffauth.core.allowlist import (
    AllowlistValidator,
    create_allowlist_from_origins,
    create_common_allowlist,
)
from bffauth.core.exceptions import ResourceNotAllowedError
from bffauth.core.models import AllowedResource, OAuthProvider, ProxyRequest


class TestAllowlistValidator:
    """Test AllowlistValidator functionality."""

    @pytest.fixture
    def allowlist(self):
        """Create allowlist with test resources."""
        return AllowlistValidator(
            [
                AllowedResource(
                    name="google_apis",
                    url_pattern=r"^https://.*\.googleapis\.com/.*$",
                    provider=OAuthProvider.GOOGLE,
                ),
                AllowedResource(
                    name="internal_api",
                    url_pattern=r"^https://api\.example\.com/.*$",
                    allowed_methods=["GET", "POST"],
                ),
            ]
        )

    def test_validate_url_allowed(self, allowlist):
        """Should allow matching URL."""
        resource = allowlist.validate_url("https://www.googleapis.com/calendar/v3")
        assert resource.name == "google_apis"

    def test_validate_url_not_allowed(self, allowlist):
        """Should reject non-matching URL."""
        with pytest.raises(ResourceNotAllowedError) as exc_info:
            allowlist.validate_url("https://evil.com/api")

        assert "https://evil.com/api" in str(exc_info.value)

    def test_validate_request_allowed(self, allowlist):
        """Should allow matching request."""
        request = ProxyRequest(
            url="https://api.example.com/users",
            method="GET",
        )
        resource = allowlist.validate_request(request)
        assert resource.name == "internal_api"

    def test_validate_request_method_not_allowed(self, allowlist):
        """Should reject disallowed method."""
        request = ProxyRequest(
            url="https://api.example.com/users",
            method="DELETE",
        )
        with pytest.raises(ResourceNotAllowedError) as exc_info:
            allowlist.validate_request(request)

        assert "DELETE not allowed" in str(exc_info.value)

    def test_validate_request_with_scopes(self):
        """Should validate required scopes."""
        allowlist = AllowlistValidator(
            [
                AllowedResource(
                    name="secure_api",
                    url_pattern=r"^https://secure\.example\.com/.*$",
                    required_scopes=["admin", "write"],
                ),
            ]
        )

        request = ProxyRequest(url="https://secure.example.com/data")

        # Missing scopes
        with pytest.raises(ResourceNotAllowedError) as exc_info:
            allowlist.validate_request(request, user_scopes=["read"])

        assert "missing scopes" in str(exc_info.value)

        # With required scopes
        resource = allowlist.validate_request(
            request,
            user_scopes=["admin", "write", "read"],
        )
        assert resource.name == "secure_api"

    def test_validate_request_provider_restriction(self, allowlist):
        """Should enforce provider restriction."""
        request = ProxyRequest(
            url="https://www.googleapis.com/calendar",
            method="GET",
            provider=OAuthProvider.AZURE,  # Wrong provider
        )

        with pytest.raises(ResourceNotAllowedError) as exc_info:
            allowlist.validate_request(request)

        assert "requires provider google" in str(exc_info.value)

    def test_is_allowed(self, allowlist):
        """Should check if URL is allowed."""
        assert allowlist.is_allowed("https://www.googleapis.com/api") is True
        assert allowlist.is_allowed("https://evil.com/api") is False
        assert allowlist.is_allowed("https://api.example.com/data", "GET") is True
        assert allowlist.is_allowed("https://api.example.com/data", "DELETE") is False

    def test_add_resource(self, allowlist):
        """Should add new resource."""
        allowlist.add_resource(
            AllowedResource(
                name="new_api",
                url_pattern=r"^https://new\.example\.com/.*$",
            )
        )

        assert allowlist.is_allowed("https://new.example.com/data") is True

    def test_remove_resource(self, allowlist):
        """Should remove resource."""
        assert allowlist.is_allowed("https://www.googleapis.com/api") is True

        removed = allowlist.remove_resource("google_apis")
        assert removed is True

        assert allowlist.is_allowed("https://www.googleapis.com/api") is False

    def test_remove_resource_not_found(self, allowlist):
        """Should return False for nonexistent resource."""
        removed = allowlist.remove_resource("nonexistent")
        assert removed is False

    def test_get_resource(self, allowlist):
        """Should get resource by name."""
        resource = allowlist.get_resource("google_apis")
        assert resource is not None
        assert resource.provider == OAuthProvider.GOOGLE

    def test_list_resources(self, allowlist):
        """Should list all resources."""
        resources = allowlist.list_resources()
        assert len(resources) == 2

    def test_get_provider_for_url(self, allowlist):
        """Should get required provider for URL."""
        provider = allowlist.get_provider_for_url("https://www.googleapis.com/api")
        assert provider == OAuthProvider.GOOGLE

        provider = allowlist.get_provider_for_url("https://api.example.com/data")
        assert provider is None  # No provider restriction

    def test_disabled_resource(self):
        """Should ignore disabled resources."""
        allowlist = AllowlistValidator(
            [
                AllowedResource(
                    name="disabled",
                    url_pattern=r"^https://disabled\.com/.*$",
                    enabled=False,
                ),
            ]
        )

        assert allowlist.is_allowed("https://disabled.com/api") is False


class TestAllowlistFactories:
    """Test allowlist factory functions."""

    def test_create_from_origins(self):
        """Should create allowlist from origin URLs."""
        allowlist = create_allowlist_from_origins(
            [
                "https://api.example.com",
                "https://auth.example.com",
            ]
        )

        assert allowlist.is_allowed("https://api.example.com/users") is True
        assert allowlist.is_allowed("https://auth.example.com/login") is True
        assert allowlist.is_allowed("https://evil.com/api") is False

    def test_create_from_origins_with_methods(self):
        """Should respect method restrictions."""
        allowlist = create_allowlist_from_origins(
            ["https://api.example.com"],
            allowed_methods=["GET"],
        )

        assert allowlist.is_allowed("https://api.example.com/data", "GET") is True
        assert allowlist.is_allowed("https://api.example.com/data", "POST") is False

    def test_create_common_allowlist(self):
        """Should create common API patterns."""
        allowlist = create_common_allowlist()

        # Google APIs
        assert allowlist.is_allowed("https://www.googleapis.com/calendar/v3") is True
        # Microsoft Graph
        assert allowlist.is_allowed("https://graph.microsoft.com/v1.0/me") is True
        # GitHub API
        assert allowlist.is_allowed("https://api.github.com/user") is True
