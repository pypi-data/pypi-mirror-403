"""
Microsoft Azure AD / Entra ID OAuth Provider Configuration.

Implements Microsoft identity platform OAuth 2.0 with OpenID Connect.
Supports multi-tenant, single-tenant, and B2C configurations.
"""

from ..core.models import OAuthProvider, ProviderConfig


def create_azure_config(
    client_id: str,
    client_secret: str | None = None,
    tenant_id: str = "common",
    scope: str = "openid email profile",
    extra_auth_params: dict[str, str] | None = None,
) -> ProviderConfig:
    """
    Create Microsoft Azure AD / Entra ID provider configuration.

    Args:
        client_id: Azure AD application (client) ID.
        client_secret: Azure AD client secret. Optional for public clients.
        tenant_id: Azure AD tenant ID or "common", "organizations", "consumers".
        scope: OAuth scopes. Defaults to OpenID Connect basics.
        extra_auth_params: Additional authorization parameters.

    Returns:
        ProviderConfig for Azure AD.
    """
    base_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0"

    return ProviderConfig(
        provider=OAuthProvider.AZURE,
        client_id=client_id,
        client_secret=client_secret,
        authorization_endpoint=f"{base_url}/authorize",
        token_endpoint=f"{base_url}/token",
        userinfo_endpoint="https://graph.microsoft.com/oidc/userinfo",
        revocation_endpoint=None,  # Azure uses logout endpoint instead
        jwks_uri=f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys",
        issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        end_session_endpoint=f"{base_url}/logout",
        scope=scope,
        use_pkce=True,
        extra_auth_params=extra_auth_params or {},
    )


def create_azure_b2c_config(
    client_id: str,
    client_secret: str | None,
    tenant_name: str,
    policy_name: str,
    scope: str = "openid email profile",
    extra_auth_params: dict[str, str] | None = None,
) -> ProviderConfig:
    """
    Create Azure AD B2C provider configuration.

    Args:
        client_id: Azure AD B2C application ID.
        client_secret: Azure AD B2C client secret.
        tenant_name: B2C tenant name (e.g., "contoso").
        policy_name: B2C policy/user flow name (e.g., "B2C_1_signup_signin").
        scope: OAuth scopes.
        extra_auth_params: Additional authorization parameters.

    Returns:
        ProviderConfig for Azure AD B2C.
    """
    base_url = f"https://{tenant_name}.b2clogin.com/{tenant_name}.onmicrosoft.com/{policy_name}/oauth2/v2.0"

    return ProviderConfig(
        provider=OAuthProvider.AZURE,
        client_id=client_id,
        client_secret=client_secret,
        authorization_endpoint=f"{base_url}/authorize",
        token_endpoint=f"{base_url}/token",
        userinfo_endpoint=None,  # B2C returns claims in ID token
        revocation_endpoint=None,
        jwks_uri=f"https://{tenant_name}.b2clogin.com/{tenant_name}.onmicrosoft.com/{policy_name}/discovery/v2.0/keys",
        issuer=f"https://{tenant_name}.b2clogin.com/{tenant_name}.onmicrosoft.com/{policy_name}/v2.0",
        end_session_endpoint=f"{base_url}/logout",
        scope=scope,
        use_pkce=True,
        extra_auth_params=extra_auth_params or {},
    )


# Common Microsoft Graph scopes
AZURE_SCOPES = {
    "basic": "openid email profile",
    "user_read": "User.Read",
    "mail_read": "Mail.Read",
    "mail_send": "Mail.Send",
    "calendars_read": "Calendars.Read",
    "calendars_readwrite": "Calendars.ReadWrite",
    "files_read": "Files.Read",
    "files_readwrite": "Files.ReadWrite",
    "offline_access": "offline_access",  # Required for refresh tokens
}


# Tenant ID constants
AZURE_TENANT_COMMON = "common"  # Any Azure AD or personal Microsoft account
AZURE_TENANT_ORGANIZATIONS = "organizations"  # Any Azure AD account
AZURE_TENANT_CONSUMERS = "consumers"  # Personal Microsoft accounts only
