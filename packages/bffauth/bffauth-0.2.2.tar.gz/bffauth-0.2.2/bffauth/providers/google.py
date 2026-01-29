"""
Google OAuth Provider Configuration.

Implements Google OAuth 2.0 with OpenID Connect support.
"""


from ..core.models import OAuthProvider, ProviderConfig


def create_google_config(
    client_id: str,
    client_secret: str,
    scope: str = "openid email profile",
    extra_auth_params: dict[str, str] | None = None,
) -> ProviderConfig:
    """
    Create Google OAuth provider configuration.

    Args:
        client_id: Google OAuth client ID.
        client_secret: Google OAuth client secret.
        scope: OAuth scopes. Defaults to OpenID Connect basics.
        extra_auth_params: Additional authorization parameters.

    Returns:
        ProviderConfig for Google.
    """
    return ProviderConfig(
        provider=OAuthProvider.GOOGLE,
        client_id=client_id,
        client_secret=client_secret,
        authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint="https://oauth2.googleapis.com/token",
        userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
        revocation_endpoint="https://oauth2.googleapis.com/revoke",
        jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
        issuer="https://accounts.google.com",
        scope=scope,
        use_pkce=True,
        extra_auth_params=extra_auth_params or {},
    )


# Common Google OAuth scopes
GOOGLE_SCOPES = {
    "basic": "openid email profile",
    "calendar": "https://www.googleapis.com/auth/calendar",
    "calendar_readonly": "https://www.googleapis.com/auth/calendar.readonly",
    "drive": "https://www.googleapis.com/auth/drive",
    "drive_readonly": "https://www.googleapis.com/auth/drive.readonly",
    "gmail_readonly": "https://www.googleapis.com/auth/gmail.readonly",
    "gmail_send": "https://www.googleapis.com/auth/gmail.send",
    "sheets": "https://www.googleapis.com/auth/spreadsheets",
    "sheets_readonly": "https://www.googleapis.com/auth/spreadsheets.readonly",
}
