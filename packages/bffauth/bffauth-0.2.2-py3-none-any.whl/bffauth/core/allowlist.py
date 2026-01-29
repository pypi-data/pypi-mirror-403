"""
BFF Resource Server Allowlist Validator.

Implements IETF draft-ietf-oauth-browser-based-apps section 6.2.4
for validating resource server requests before token injection.
"""

import re
from urllib.parse import urlparse

from .exceptions import ResourceNotAllowedError
from .models import AllowedResource, OAuthProvider, ProxyRequest


class AllowlistValidator:
    """
    Validates requests against allowed resource servers.

    Per IETF BFF security requirements, the BFF must maintain an allowlist
    of resource servers that can receive access tokens. This prevents
    token leakage to unauthorized endpoints.

    Features:
    - URL pattern matching (regex-based)
    - HTTP method validation
    - Scope-based access control
    - Provider-specific restrictions
    """

    def __init__(self, allowed_resources: list[AllowedResource] | None = None):
        """
        Initialize allowlist validator.

        Args:
            allowed_resources: List of allowed resource configurations.
        """
        self._resources: list[AllowedResource] = allowed_resources or []
        self._compiled_patterns: dict[str, re.Pattern[str]] = {}

        # Compile regex patterns for performance
        for resource in self._resources:
            if resource.enabled:
                self._compiled_patterns[resource.name] = re.compile(
                    resource.url_pattern
                )

    def add_resource(self, resource: AllowedResource) -> None:
        """
        Add a resource to the allowlist.

        Args:
            resource: Resource configuration to add.
        """
        self._resources.append(resource)
        if resource.enabled:
            self._compiled_patterns[resource.name] = re.compile(resource.url_pattern)

    def remove_resource(self, name: str) -> bool:
        """
        Remove a resource from the allowlist.

        Args:
            name: Resource name to remove.

        Returns:
            True if resource was found and removed.
        """
        for i, resource in enumerate(self._resources):
            if resource.name == name:
                self._resources.pop(i)
                self._compiled_patterns.pop(name, None)
                return True
        return False

    def get_resource(self, name: str) -> AllowedResource | None:
        """
        Get resource configuration by name.

        Args:
            name: Resource name.

        Returns:
            Resource configuration or None.
        """
        for resource in self._resources:
            if resource.name == name:
                return resource
        return None

    def list_resources(self) -> list[AllowedResource]:
        """Get all configured resources."""
        return self._resources.copy()

    def _match_url(self, url: str) -> AllowedResource | None:
        """
        Find matching resource for URL.

        Args:
            url: URL to match.

        Returns:
            First matching AllowedResource or None.
        """
        for resource in self._resources:
            if not resource.enabled:
                continue
            pattern = self._compiled_patterns.get(resource.name)
            if pattern and pattern.match(url):
                return resource
        return None

    def validate_url(self, url: str) -> AllowedResource:
        """
        Validate that URL is in the allowlist.

        Args:
            url: URL to validate.

        Returns:
            Matching AllowedResource.

        Raises:
            ResourceNotAllowedError: If URL not in allowlist.
        """
        resource = self._match_url(url)
        if resource is None:
            raise ResourceNotAllowedError(url)
        return resource

    def validate_request(
        self,
        request: ProxyRequest,
        user_scopes: list[str] | None = None,
    ) -> AllowedResource:
        """
        Validate a proxy request against the allowlist.

        Checks:
        1. URL matches an allowed resource pattern
        2. HTTP method is allowed for the resource
        3. User has required scopes (if any)
        4. Provider matches (if resource is provider-specific)

        Args:
            request: Proxy request to validate.
            user_scopes: Scopes the user has for the provider.

        Returns:
            Matching AllowedResource.

        Raises:
            ResourceNotAllowedError: If request is not allowed.
        """
        # Check URL matches allowlist
        resource = self._match_url(request.url)
        if resource is None:
            raise ResourceNotAllowedError(request.url)

        # Check HTTP method
        if request.method.upper() not in [m.upper() for m in resource.allowed_methods]:
            raise ResourceNotAllowedError(
                f"{request.url} (method {request.method} not allowed)"
            )

        # Check required scopes
        if resource.required_scopes:
            user_scopes = user_scopes or []
            missing_scopes = set(resource.required_scopes) - set(user_scopes)
            if missing_scopes:
                raise ResourceNotAllowedError(
                    f"{request.url} (missing scopes: {', '.join(missing_scopes)})"
                )

        # Check provider restriction
        if resource.provider is not None and request.provider is not None:
            if resource.provider != request.provider:
                raise ResourceNotAllowedError(
                    f"{request.url} (requires provider {resource.provider.value})"
                )

        return resource

    def is_allowed(
        self,
        url: str,
        method: str = "GET",
        provider: OAuthProvider | None = None,
    ) -> bool:
        """
        Quick check if URL/method is allowed.

        Args:
            url: URL to check.
            method: HTTP method.
            provider: OAuth provider (if checking provider restriction).

        Returns:
            True if allowed.
        """
        try:
            request = ProxyRequest(url=url, method=method, provider=provider)
            self.validate_request(request)
            return True
        except ResourceNotAllowedError:
            return False

    def get_provider_for_url(self, url: str) -> OAuthProvider | None:
        """
        Get the provider required for a URL.

        Args:
            url: URL to check.

        Returns:
            Required provider or None if any provider allowed.
        """
        resource = self._match_url(url)
        if resource is None:
            return None
        return resource.provider


def create_common_allowlist() -> AllowlistValidator:
    """
    Create allowlist with common API patterns.

    This is a convenience function for common use cases.
    Production should use explicit allowlists.

    Returns:
        AllowlistValidator with common patterns.
    """
    resources = [
        # Google APIs
        AllowedResource(
            name="google_apis",
            url_pattern=r"^https://.*\.googleapis\.com/.*$",
            provider=OAuthProvider.GOOGLE,
        ),
        # Microsoft Graph
        AllowedResource(
            name="microsoft_graph",
            url_pattern=r"^https://graph\.microsoft\.com/.*$",
            provider=OAuthProvider.AZURE,
        ),
        # GitHub API
        AllowedResource(
            name="github_api",
            url_pattern=r"^https://api\.github\.com/.*$",
            provider=OAuthProvider.GITHUB,
        ),
    ]
    return AllowlistValidator(resources)


def create_allowlist_from_origins(
    origins: list[str],
    allowed_methods: list[str] | None = None,
) -> AllowlistValidator:
    """
    Create allowlist from a list of origin URLs.

    Convenience function to create simple allowlists from origins.

    Args:
        origins: List of origin URLs (e.g., ["https://api.example.com"]).
        allowed_methods: HTTP methods to allow. Defaults to all common methods.

    Returns:
        AllowlistValidator with origin-based patterns.
    """
    allowed_methods = allowed_methods or ["GET", "POST", "PUT", "PATCH", "DELETE"]
    resources = []

    for origin in origins:
        parsed = urlparse(origin)
        # Escape special regex characters in the origin
        escaped_origin = re.escape(f"{parsed.scheme}://{parsed.netloc}")
        pattern = f"^{escaped_origin}/.*$"

        resources.append(
            AllowedResource(
                name=f"origin_{parsed.netloc.replace('.', '_')}",
                url_pattern=pattern,
                allowed_methods=allowed_methods,
            )
        )

    return AllowlistValidator(resources)
