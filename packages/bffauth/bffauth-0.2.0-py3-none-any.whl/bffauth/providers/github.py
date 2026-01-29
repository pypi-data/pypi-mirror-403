"""
GitHub OAuth Provider Configuration.

Implements GitHub OAuth 2.0 for GitHub Apps and OAuth Apps.
"""


from ..core.models import OAuthProvider, ProviderConfig


def create_github_config(
    client_id: str,
    client_secret: str,
    scope: str = "read:user user:email",
    extra_auth_params: dict[str, str] | None = None,
) -> ProviderConfig:
    """
    Create GitHub OAuth provider configuration.

    Args:
        client_id: GitHub OAuth App client ID.
        client_secret: GitHub OAuth App client secret.
        scope: GitHub scopes. Defaults to user read access.
        extra_auth_params: Additional authorization parameters.

    Returns:
        ProviderConfig for GitHub.
    """
    return ProviderConfig(
        provider=OAuthProvider.GITHUB,
        client_id=client_id,
        client_secret=client_secret,
        authorization_endpoint="https://github.com/login/oauth/authorize",
        token_endpoint="https://github.com/login/oauth/access_token",
        userinfo_endpoint="https://api.github.com/user",
        revocation_endpoint=None,  # GitHub uses application settings to revoke
        jwks_uri=None,
        issuer=None,
        scope=scope,
        use_pkce=True,  # GitHub supports PKCE
        extra_auth_params=extra_auth_params or {},
    )


def create_github_enterprise_config(
    client_id: str,
    client_secret: str,
    enterprise_url: str,
    scope: str = "read:user user:email",
    extra_auth_params: dict[str, str] | None = None,
) -> ProviderConfig:
    """
    Create GitHub Enterprise Server OAuth provider configuration.

    Args:
        client_id: GitHub Enterprise OAuth App client ID.
        client_secret: GitHub Enterprise OAuth App client secret.
        enterprise_url: GitHub Enterprise base URL (e.g., "https://github.mycompany.com").
        scope: GitHub scopes.
        extra_auth_params: Additional authorization parameters.

    Returns:
        ProviderConfig for GitHub Enterprise.
    """
    base_url = enterprise_url.rstrip("/")

    return ProviderConfig(
        provider=OAuthProvider.GITHUB,
        client_id=client_id,
        client_secret=client_secret,
        authorization_endpoint=f"{base_url}/login/oauth/authorize",
        token_endpoint=f"{base_url}/login/oauth/access_token",
        userinfo_endpoint=f"{base_url}/api/v3/user",
        revocation_endpoint=None,
        jwks_uri=None,
        issuer=None,
        scope=scope,
        use_pkce=True,
        extra_auth_params=extra_auth_params or {},
    )


# Common GitHub OAuth scopes
GITHUB_SCOPES = {
    "user_read": "read:user",
    "user_email": "user:email",
    "user_follow": "user:follow",
    "repo": "repo",
    "repo_public": "public_repo",
    "repo_status": "repo:status",
    "repo_deployment": "repo_deployment",
    "delete_repo": "delete_repo",
    "notifications": "notifications",
    "gist": "gist",
    "read_org": "read:org",
    "admin_org": "admin:org",
    "read_packages": "read:packages",
    "write_packages": "write:packages",
    "admin_gpg_key": "admin:gpg_key",
    "workflow": "workflow",
}
