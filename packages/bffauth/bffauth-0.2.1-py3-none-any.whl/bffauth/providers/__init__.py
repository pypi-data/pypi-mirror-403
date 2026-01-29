"""
BFFAuth OAuth Provider Configurations.

Pre-configured settings for common OAuth providers.
"""

from .azure import (
    AZURE_SCOPES,
    AZURE_TENANT_COMMON,
    AZURE_TENANT_CONSUMERS,
    AZURE_TENANT_ORGANIZATIONS,
    create_azure_b2c_config,
    create_azure_config,
)
from .generic import (
    create_custom_config,
    create_oidc_config_from_discovery_async,
)
from .github import (
    GITHUB_SCOPES,
    create_github_config,
    create_github_enterprise_config,
)
from .google import (
    GOOGLE_SCOPES,
    create_google_config,
)

__all__ = [
    # Azure
    "create_azure_config",
    "create_azure_b2c_config",
    "AZURE_SCOPES",
    "AZURE_TENANT_COMMON",
    "AZURE_TENANT_ORGANIZATIONS",
    "AZURE_TENANT_CONSUMERS",
    # GitHub
    "create_github_config",
    "create_github_enterprise_config",
    "GITHUB_SCOPES",
    # Google
    "create_google_config",
    "GOOGLE_SCOPES",
    # Generic
    "create_custom_config",
    "create_oidc_config_from_discovery_async",
]
