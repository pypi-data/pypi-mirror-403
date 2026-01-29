"""
Generic OAuth Provider Configuration.

Supports custom OAuth 2.0 / OpenID Connect providers.
"""


from ..core.models import OAuthProvider, ProviderConfig


def create_custom_config(
    client_id: str,
    authorization_endpoint: str,
    token_endpoint: str,
    client_secret: str | None = None,
    userinfo_endpoint: str | None = None,
    revocation_endpoint: str | None = None,
    jwks_uri: str | None = None,
    issuer: str | None = None,
    scope: str = "openid",
    use_pkce: bool = True,
    extra_auth_params: dict[str, str] | None = None,
    extra_token_params: dict[str, str] | None = None,
) -> ProviderConfig:
    """
    Create a custom OAuth provider configuration.

    Use this for any OAuth 2.0 or OpenID Connect provider not directly supported.

    Args:
        client_id: OAuth client ID.
        authorization_endpoint: Authorization endpoint URL.
        token_endpoint: Token endpoint URL.
        client_secret: OAuth client secret (for confidential clients).
        userinfo_endpoint: UserInfo endpoint URL (OIDC).
        revocation_endpoint: Token revocation endpoint URL.
        jwks_uri: JWKS endpoint for ID token verification.
        issuer: OIDC issuer identifier.
        scope: OAuth scopes.
        use_pkce: Enable PKCE (recommended).
        extra_auth_params: Additional authorization parameters.
        extra_token_params: Additional token request parameters.

    Returns:
        ProviderConfig for custom provider.
    """
    return ProviderConfig(
        provider=OAuthProvider.CUSTOM,
        client_id=client_id,
        client_secret=client_secret,
        authorization_endpoint=authorization_endpoint,
        token_endpoint=token_endpoint,
        userinfo_endpoint=userinfo_endpoint,
        revocation_endpoint=revocation_endpoint,
        jwks_uri=jwks_uri,
        issuer=issuer,
        scope=scope,
        use_pkce=use_pkce,
        extra_auth_params=extra_auth_params or {},
        extra_token_params=extra_token_params or {},
    )


def create_oidc_config_from_discovery(
    client_id: str,
    discovery_url: str,
    client_secret: str | None = None,
    scope: str = "openid email profile",
) -> ProviderConfig:
    """
    Create provider config from OIDC discovery document.

    This is a placeholder - actual implementation would fetch
    the discovery document and parse endpoints.

    Args:
        client_id: OAuth client ID.
        discovery_url: OIDC discovery document URL (.well-known/openid-configuration).
        client_secret: OAuth client secret.
        scope: OAuth scopes.

    Returns:
        ProviderConfig populated from discovery document.

    Note:
        For production use, this should fetch the discovery document.
        Consider using httpx to fetch and cache the discovery document.
    """
    # This would normally fetch the discovery document
    # For now, raise an error indicating async fetch is needed
    raise NotImplementedError(
        "Use create_oidc_config_from_discovery_async for runtime discovery. "
        "This sync version is not implemented."
    )


async def create_oidc_config_from_discovery_async(
    client_id: str,
    discovery_url: str,
    client_secret: str | None = None,
    scope: str = "openid email profile",
) -> ProviderConfig:
    """
    Create provider config from OIDC discovery document (async).

    Fetches the OIDC discovery document and creates a ProviderConfig
    with the discovered endpoints.

    Args:
        client_id: OAuth client ID.
        discovery_url: OIDC discovery document URL (.well-known/openid-configuration).
        client_secret: OAuth client secret.
        scope: OAuth scopes.

    Returns:
        ProviderConfig populated from discovery document.
    """
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(discovery_url)
        response.raise_for_status()
        discovery = response.json()

    return ProviderConfig(
        provider=OAuthProvider.CUSTOM,
        client_id=client_id,
        client_secret=client_secret,
        authorization_endpoint=discovery["authorization_endpoint"],
        token_endpoint=discovery["token_endpoint"],
        userinfo_endpoint=discovery.get("userinfo_endpoint"),
        revocation_endpoint=discovery.get("revocation_endpoint"),
        jwks_uri=discovery.get("jwks_uri"),
        issuer=discovery.get("issuer"),
        scope=scope,
        use_pkce=True,
    )
