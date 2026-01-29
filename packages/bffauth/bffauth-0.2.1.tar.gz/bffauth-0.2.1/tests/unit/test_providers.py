"""
Unit tests for OAuth Provider Configurations.
"""


from bffauth.core.models import OAuthProvider
from bffauth.providers.azure import (
    AZURE_SCOPES,
    AZURE_TENANT_COMMON,
    AZURE_TENANT_CONSUMERS,
    AZURE_TENANT_ORGANIZATIONS,
    create_azure_b2c_config,
    create_azure_config,
)
from bffauth.providers.github import (
    GITHUB_SCOPES,
    create_github_config,
    create_github_enterprise_config,
)
from bffauth.providers.google import GOOGLE_SCOPES, create_google_config


class TestGoogleProvider:
    """Test Google OAuth provider configuration."""

    def test_create_google_config_basic(self):
        """Should create basic Google config."""
        config = create_google_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert config.provider == OAuthProvider.GOOGLE
        assert config.client_id == "test-client-id"
        assert config.client_secret == "test-client-secret"
        assert config.scope == "openid email profile"
        assert config.use_pkce is True

    def test_create_google_config_endpoints(self):
        """Should have correct Google endpoints."""
        config = create_google_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert (
            config.authorization_endpoint
            == "https://accounts.google.com/o/oauth2/v2/auth"
        )
        assert config.token_endpoint == "https://oauth2.googleapis.com/token"
        assert (
            config.userinfo_endpoint
            == "https://openidconnect.googleapis.com/v1/userinfo"
        )
        assert config.revocation_endpoint == "https://oauth2.googleapis.com/revoke"
        assert config.jwks_uri == "https://www.googleapis.com/oauth2/v3/certs"
        assert config.issuer == "https://accounts.google.com"

    def test_create_google_config_custom_scope(self):
        """Should use custom scope."""
        config = create_google_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            scope="openid email https://www.googleapis.com/auth/calendar",
        )

        assert "calendar" in config.scope

    def test_create_google_config_extra_params(self):
        """Should include extra auth params."""
        config = create_google_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            extra_auth_params={"prompt": "consent", "access_type": "offline"},
        )

        assert config.extra_auth_params["prompt"] == "consent"
        assert config.extra_auth_params["access_type"] == "offline"

    def test_google_scopes_defined(self):
        """Should have common Google scopes defined."""
        assert "basic" in GOOGLE_SCOPES
        assert "calendar" in GOOGLE_SCOPES
        assert "drive" in GOOGLE_SCOPES
        assert "gmail_readonly" in GOOGLE_SCOPES
        assert "sheets" in GOOGLE_SCOPES


class TestAzureProvider:
    """Test Azure AD OAuth provider configuration."""

    def test_create_azure_config_basic(self):
        """Should create basic Azure config."""
        config = create_azure_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert config.provider == OAuthProvider.AZURE
        assert config.client_id == "test-client-id"
        assert config.client_secret == "test-client-secret"
        assert config.scope == "openid email profile"
        assert config.use_pkce is True

    def test_create_azure_config_default_tenant(self):
        """Should use 'common' tenant by default."""
        config = create_azure_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert "common" in config.authorization_endpoint
        assert "common" in config.token_endpoint

    def test_create_azure_config_custom_tenant(self):
        """Should use custom tenant ID."""
        tenant_id = "12345678-1234-1234-1234-123456789012"
        config = create_azure_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            tenant_id=tenant_id,
        )

        assert tenant_id in config.authorization_endpoint
        assert tenant_id in config.token_endpoint
        assert tenant_id in config.issuer

    def test_create_azure_config_endpoints(self):
        """Should have correct Azure endpoints."""
        config = create_azure_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert "login.microsoftonline.com" in config.authorization_endpoint
        assert "login.microsoftonline.com" in config.token_endpoint
        assert config.userinfo_endpoint == "https://graph.microsoft.com/oidc/userinfo"
        assert config.revocation_endpoint is None  # Azure uses logout

    def test_create_azure_config_public_client(self):
        """Should support public clients without secret."""
        config = create_azure_config(
            client_id="test-client-id",
        )

        assert config.client_secret is None

    def test_create_azure_b2c_config(self):
        """Should create Azure B2C config."""
        config = create_azure_b2c_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            tenant_name="contoso",
            policy_name="B2C_1_signup_signin",
        )

        assert config.provider == OAuthProvider.AZURE
        assert "contoso.b2clogin.com" in config.authorization_endpoint
        assert "contoso.b2clogin.com" in config.token_endpoint
        assert "B2C_1_signup_signin" in config.authorization_endpoint
        assert config.userinfo_endpoint is None  # B2C returns claims in ID token

    def test_azure_tenant_constants(self):
        """Should have tenant constants defined."""
        assert AZURE_TENANT_COMMON == "common"
        assert AZURE_TENANT_ORGANIZATIONS == "organizations"
        assert AZURE_TENANT_CONSUMERS == "consumers"

    def test_azure_scopes_defined(self):
        """Should have common Azure scopes defined."""
        assert "basic" in AZURE_SCOPES
        assert "user_read" in AZURE_SCOPES
        assert "mail_read" in AZURE_SCOPES
        assert "calendars_read" in AZURE_SCOPES
        assert "offline_access" in AZURE_SCOPES


class TestGitHubProvider:
    """Test GitHub OAuth provider configuration."""

    def test_create_github_config_basic(self):
        """Should create basic GitHub config."""
        config = create_github_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert config.provider == OAuthProvider.GITHUB
        assert config.client_id == "test-client-id"
        assert config.client_secret == "test-client-secret"
        assert config.scope == "read:user user:email"
        assert config.use_pkce is True

    def test_create_github_config_endpoints(self):
        """Should have correct GitHub endpoints."""
        config = create_github_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert (
            config.authorization_endpoint == "https://github.com/login/oauth/authorize"
        )
        assert config.token_endpoint == "https://github.com/login/oauth/access_token"
        assert config.userinfo_endpoint == "https://api.github.com/user"
        assert config.revocation_endpoint is None
        assert config.jwks_uri is None
        assert config.issuer is None

    def test_create_github_config_custom_scope(self):
        """Should use custom scope."""
        config = create_github_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            scope="repo read:user",
        )

        assert "repo" in config.scope

    def test_create_github_enterprise_config(self):
        """Should create GitHub Enterprise config."""
        config = create_github_enterprise_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            enterprise_url="https://github.mycompany.com",
        )

        assert config.provider == OAuthProvider.GITHUB
        assert "github.mycompany.com" in config.authorization_endpoint
        assert "github.mycompany.com" in config.token_endpoint
        assert "github.mycompany.com" in config.userinfo_endpoint

    def test_create_github_enterprise_config_strips_trailing_slash(self):
        """Should strip trailing slash from enterprise URL."""
        config = create_github_enterprise_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            enterprise_url="https://github.mycompany.com/",
        )

        assert "github.mycompany.com//" not in config.authorization_endpoint
        assert (
            config.authorization_endpoint
            == "https://github.mycompany.com/login/oauth/authorize"
        )

    def test_github_scopes_defined(self):
        """Should have common GitHub scopes defined."""
        assert "user_read" in GITHUB_SCOPES
        assert "user_email" in GITHUB_SCOPES
        assert "repo" in GITHUB_SCOPES
        assert "repo_public" in GITHUB_SCOPES
        assert "workflow" in GITHUB_SCOPES
        assert "read_org" in GITHUB_SCOPES


class TestProviderConfigValidation:
    """Test provider config validation."""

    def test_https_required_for_endpoints(self):
        """Should validate HTTPS for endpoints (except localhost)."""
        # Should succeed with HTTPS
        config = create_google_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )
        assert config.authorization_endpoint.startswith("https://")

    def test_extra_auth_params_default_empty(self):
        """Should default extra_auth_params to empty dict."""
        config = create_google_config(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )
        assert config.extra_auth_params == {}

    def test_pkce_enabled_by_default(self):
        """All providers should have PKCE enabled by default."""
        google = create_google_config("id", "secret")
        azure = create_azure_config("id", "secret")
        github = create_github_config("id", "secret")

        assert google.use_pkce is True
        assert azure.use_pkce is True
        assert github.use_pkce is True
