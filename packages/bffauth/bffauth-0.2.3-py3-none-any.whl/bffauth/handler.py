"""
BFF OAuth Handler.

Main orchestrator for BFF authentication pattern.
Combines session management, token vault, OAuth backend, and allowlist
into a cohesive authentication handler.
"""

from datetime import timedelta
from typing import Any

from .backends.authlib import AuthlibBackend
from .core.allowlist import AllowlistValidator
from .core.exceptions import (
    AuthorizationError,
    LogoutTokenError,
    ProviderNotConfiguredError,
    SessionNotFoundError,
    StateValidationError,
    TokenExpiredError,
    TokenNotFoundError,
)
from .core.models import (
    AuthorizationResult,
    OAuthProvider,
    OAuthState,
    ProviderConfig,
    SessionData,
)
from .core.session import SessionManager, SessionStorageProtocol
from .core.vault import TokenVault, TokenVaultStorageProtocol


class BFFOAuthHandler:
    """
    BFF OAuth Handler.

    Provides a complete BFF authentication implementation:
    - Session management with secure cookies
    - Multi-provider OAuth with PKCE
    - Encrypted token storage
    - Automatic token refresh
    - Resource server allowlist validation

    Example usage:

        from bffauth import BFFOAuthHandler
        from bffauth.providers import create_google_config

        handler = BFFOAuthHandler(
            encryption_key="your-fernet-key",
            redirect_base_uri="https://app.example.com",
        )

        handler.register_provider(create_google_config(
            client_id="...",
            client_secret="...",
        ))

        # Start OAuth flow
        auth_url, session = await handler.start_authorization(
            provider=OAuthProvider.GOOGLE,
        )

        # Handle callback
        result = await handler.handle_callback(
            session_id=session.session_id,
            code="...",
            state="...",
        )
    """

    def __init__(
        self,
        encryption_key: str,
        redirect_base_uri: str = "http://localhost:8080",
        callback_path: str = "/auth/callback",
        session_lifetime: timedelta = timedelta(hours=24),
        token_refresh_buffer: int = 300,
        session_storage: SessionStorageProtocol | None = None,
        token_storage: TokenVaultStorageProtocol | None = None,
        allowlist: AllowlistValidator | None = None,
        cookie_name: str = "__Host-session",
        cookie_secure: bool = True,
        cookie_samesite: str = "strict",
    ):
        """
        Initialize BFF OAuth Handler.

        Args:
            encryption_key: Fernet encryption key for token encryption.
            redirect_base_uri: Base URI for OAuth callbacks.
            callback_path: Path for OAuth callback endpoint.
            session_lifetime: Session duration.
            token_refresh_buffer: Seconds before expiry to refresh tokens.
            session_storage: Optional session storage backend.
            token_storage: Optional token vault storage backend.
            allowlist: Optional resource server allowlist.
            cookie_name: Session cookie name.
            cookie_secure: Secure cookie flag.
            cookie_samesite: SameSite cookie attribute.
        """
        self.redirect_base_uri = redirect_base_uri.rstrip("/")
        self.callback_path = callback_path
        self.token_refresh_buffer = token_refresh_buffer

        # Initialize components
        self.session_manager = SessionManager(
            storage=session_storage,
            session_lifetime=session_lifetime,
            cookie_name=cookie_name,
            cookie_secure=cookie_secure,
            cookie_samesite=cookie_samesite,
        )

        self.token_vault = TokenVault(
            encryption_key=encryption_key,
            storage=token_storage,
            token_refresh_buffer=token_refresh_buffer,
        )

        self.allowlist = allowlist or AllowlistValidator()

        # Provider configurations and backends
        self._providers: dict[str, ProviderConfig] = {}
        self._backends: dict[str, AuthlibBackend] = {}

    def register_provider(self, config: ProviderConfig) -> None:
        """
        Register an OAuth provider.

        Args:
            config: Provider configuration.
        """
        key = config.provider.value
        self._providers[key] = config
        self._backends[key] = AuthlibBackend(config)

    def get_provider(self, provider: OAuthProvider) -> ProviderConfig:
        """
        Get provider configuration.

        Args:
            provider: OAuth provider.

        Returns:
            Provider configuration.

        Raises:
            ProviderNotConfiguredError: If provider not registered.
        """
        config = self._providers.get(provider.value)
        if config is None:
            raise ProviderNotConfiguredError(provider.value)
        return config

    def get_backend(self, provider: OAuthProvider) -> AuthlibBackend:
        """
        Get OAuth backend for provider.

        Args:
            provider: OAuth provider.

        Returns:
            AuthlibBackend instance.

        Raises:
            ProviderNotConfiguredError: If provider not registered.
        """
        backend = self._backends.get(provider.value)
        if backend is None:
            raise ProviderNotConfiguredError(provider.value)
        return backend

    def get_redirect_uri(self, provider: OAuthProvider) -> str:
        """
        Get redirect URI for provider.

        Args:
            provider: OAuth provider.

        Returns:
            Full redirect URI.
        """
        return f"{self.redirect_base_uri}{self.callback_path}/{provider.value}"

    async def start_authorization(
        self,
        provider: OAuthProvider,
        scope: str | None = None,
        extra_params: dict[str, str] | None = None,
        existing_session: SessionData | None = None,
    ) -> tuple[str, SessionData]:
        """
        Start OAuth authorization flow.

        Creates a session (if needed), generates authorization URL with PKCE,
        and stores state for callback verification.

        Args:
            provider: OAuth provider to authenticate with.
            scope: Optional scope override.
            extra_params: Additional authorization parameters.
            existing_session: Existing session to use (for adding providers).

        Returns:
            Tuple of (authorization_url, session).
        """
        backend = self.get_backend(provider)
        redirect_uri = self.get_redirect_uri(provider)

        # Create or use existing session
        if existing_session:
            session = existing_session
        else:
            session = await self.session_manager.create_session()

        # Generate authorization URL
        auth_url, oauth_state = backend.create_authorization_url(
            redirect_uri=redirect_uri,
            scope=scope,
            extra_params=extra_params,
        )

        # Store OAuth state in session metadata for callback verification
        # Serialized to dict for storage compatibility
        session.metadata["oauth_state"] = {
            "state": oauth_state.state,
            "provider": oauth_state.provider.value,
            "code_verifier": oauth_state.code_verifier,
            "nonce": oauth_state.nonce,
            "redirect_uri": oauth_state.redirect_uri,
            "created_at": oauth_state.created_at.isoformat(),
            "expires_at": oauth_state.expires_at.isoformat(),
        }
        await self.session_manager.update_session(session)

        return auth_url, session

    async def handle_callback(
        self,
        session_id: str,
        code: str | None = None,
        state: str | None = None,
        error: str | None = None,
        error_description: str | None = None,
    ) -> AuthorizationResult:
        """
        Handle OAuth callback.

        Validates state, exchanges code for tokens, and stores tokens
        in the encrypted vault.

        Args:
            session_id: Session ID from cookie.
            code: Authorization code from provider.
            state: State parameter from provider.
            error: Error code from provider (if authorization failed).
            error_description: Error description from provider.

        Returns:
            AuthorizationResult with tokens.

        Raises:
            AuthorizationError: If authorization was denied.
            StateValidationError: If state validation fails.
            SessionNotFoundError: If session not found.
        """
        # Check for error response
        if error:
            raise AuthorizationError(error, error_description)

        if not code or not state:
            raise AuthorizationError(
                "missing_parameters", "Code and state are required"
            )

        # Validate session
        session = await self.session_manager.get_session(session_id)

        # Validate state from session metadata
        stored_state = session.metadata.get("oauth_state")
        if stored_state is None:
            raise StateValidationError("No pending OAuth state in session")

        if stored_state["state"] != state:
            raise StateValidationError("State mismatch")

        # Reconstruct OAuthState from stored data
        from datetime import datetime

        oauth_state = OAuthState(
            state=stored_state["state"],
            provider=OAuthProvider(stored_state["provider"]),
            code_verifier=stored_state["code_verifier"],
            nonce=stored_state.get("nonce"),
            redirect_uri=stored_state["redirect_uri"],
            created_at=datetime.fromisoformat(stored_state["created_at"]),
            expires_at=datetime.fromisoformat(stored_state["expires_at"]),
        )

        if oauth_state.is_expired():
            # Clear expired state from session
            del session.metadata["oauth_state"]
            await self.session_manager.update_session(session)
            raise StateValidationError("State has expired")

        # Exchange code for tokens
        backend = self.get_backend(oauth_state.provider)
        result = await backend.exchange_code(code, oauth_state)

        # Store tokens in vault
        await self.token_vault.store_token(session_id, result.token)

        # Update session with authenticated provider and clear OAuth state
        session.add_provider(oauth_state.provider)
        if result.id_token_claims:
            session.user_info.update(result.id_token_claims)
            if "sub" in result.id_token_claims and not session.user_id:
                session.user_id = result.id_token_claims["sub"]

        # Clear OAuth state after successful callback (one-time use)
        session.metadata.pop("oauth_state", None)

        await self.session_manager.update_session(session)

        return result

    async def get_access_token(
        self,
        session_id: str,
        provider: OAuthProvider,
        auto_refresh: bool = True,
    ) -> str:
        """
        Get valid access token for provider.

        Automatically refreshes if expired and refresh token available.

        Args:
            session_id: Session ID.
            provider: OAuth provider.
            auto_refresh: Attempt refresh if token expired.

        Returns:
            Valid access token.

        Raises:
            TokenNotFoundError: If no token for provider.
            TokenExpiredError: If token expired and no refresh available.
            TokenRefreshError: If refresh fails.
        """
        # Try to get valid token
        token = await self.token_vault.get_valid_token(session_id, provider)

        if token is not None:
            return token.access_token

        # Token expired or not found - try refresh
        token = await self.token_vault.get_token(session_id, provider)

        if not auto_refresh or not token.refresh_token:
            raise TokenExpiredError(provider.value)

        # Refresh token
        backend = self.get_backend(provider)
        new_token = await backend.refresh_token(token.refresh_token)

        # Update vault with new token
        await self.token_vault.store_token(session_id, new_token)

        return new_token.access_token

    async def get_logout_url(
        self,
        session_id: str,
        provider: OAuthProvider,
        post_logout_redirect_uri: str | None = None,
        state: str | None = None,
    ) -> str | None:
        """
        Get RP-Initiated Logout URL for the identity provider.

        Per OpenID Connect RP-Initiated Logout 1.0 specification.
        Returns a URL to redirect the user to for IdP-side logout.

        The ID token hint is automatically included if available.

        Example usage:

            @app.get("/logout")
            async def logout(request):
                session_id = request.cookies.get("__Host-session")
                if session_id:
                    logout_url = await handler.get_logout_url(
                        session_id,
                        provider=OAuthProvider.GOOGLE,
                        post_logout_redirect_uri="https://app.example.com/",
                    )
                    # Clear local session
                    await handler.logout(session_id)
                    if logout_url:
                        return RedirectResponse(logout_url)
                return RedirectResponse("/")

        Args:
            session_id: Session ID.
            provider: OAuth provider to logout from.
            post_logout_redirect_uri: Where to redirect after logout.
            state: Optional state parameter for the redirect.

        Returns:
            Logout URL with id_token_hint if available, or None if
            provider has no end_session_endpoint configured.
        """
        from urllib.parse import urlencode

        # Get provider config
        config = self._providers.get(provider.value)
        if config is None or config.end_session_endpoint is None:
            return None

        # Build query parameters
        params: dict[str, str] = {}

        # Try to get ID token for hint
        try:
            token = await self.token_vault.get_token(session_id, provider)
            if token.id_token:
                params["id_token_hint"] = token.id_token
        except TokenNotFoundError:
            # No token available, include client_id instead
            params["client_id"] = config.client_id

        # Include client_id if no id_token_hint (some IdPs require it)
        if "id_token_hint" not in params:
            params["client_id"] = config.client_id

        if post_logout_redirect_uri:
            params["post_logout_redirect_uri"] = post_logout_redirect_uri

        if state:
            params["state"] = state

        # Build URL
        return f"{config.end_session_endpoint}?{urlencode(params)}"

    async def logout(
        self,
        session_id: str,
        provider: OAuthProvider | None = None,
        revoke_tokens: bool = True,
    ) -> None:
        """
        Logout user.

        Optionally revokes tokens with provider and clears session/vault.
        Does NOT redirect to IdP - use get_logout_url() for RP-Initiated Logout.

        Args:
            session_id: Session ID.
            provider: Specific provider to logout from, or None for all.
            revoke_tokens: Attempt to revoke tokens with provider.
        """
        if provider:
            # Logout from specific provider
            if revoke_tokens:
                try:
                    token = await self.token_vault.get_token(session_id, provider)
                    backend = self.get_backend(provider)
                    await backend.revoke_token(token.access_token)
                    if token.refresh_token:
                        await backend.revoke_token(token.refresh_token, "refresh_token")
                except (TokenNotFoundError, ProviderNotConfiguredError):
                    pass

            await self.token_vault.delete_token(session_id, provider)

            # Update session
            try:
                session = await self.session_manager.get_session(session_id)
                session.remove_provider(provider)
                await self.session_manager.update_session(session)
            except SessionNotFoundError:
                pass
        else:
            # Full logout
            if revoke_tokens:
                providers = await self.token_vault.list_providers(session_id)
                for p in providers:
                    try:
                        token = await self.token_vault.get_token(session_id, p)
                        backend = self.get_backend(p)
                        await backend.revoke_token(token.access_token)
                    except (TokenNotFoundError, ProviderNotConfiguredError):
                        pass

            await self.token_vault.clear_vault(session_id)
            await self.session_manager.delete_session(session_id)

    async def get_session(self, session_id: str) -> SessionData:
        """
        Get session data.

        Args:
            session_id: Session ID from cookie.

        Returns:
            SessionData.

        Raises:
            SessionNotFoundError: If session not found.
        """
        return await self.session_manager.get_session(session_id)

    async def validate_csrf(
        self,
        session_id: str,
        csrf_token: str,
    ) -> bool:
        """
        Validate CSRF token.

        Args:
            session_id: Session ID.
            csrf_token: CSRF token from request.

        Returns:
            True if valid.

        Raises:
            CSRFValidationError: If validation fails.
        """
        return await self.session_manager.validate_csrf(session_id, csrf_token)

    async def refresh_session(self, session_id: str) -> SessionData:
        """
        Refresh session expiration (sliding expiration).

        Call this on each request to extend session lifetime for active users.
        The session expiration will be reset to session_lifetime from now.

        Example usage in middleware:

            @app.middleware("http")
            async def sliding_session(request, call_next):
                session_id = request.cookies.get("__Host-session")
                if session_id:
                    try:
                        await handler.refresh_session(session_id)
                    except SessionNotFoundError:
                        pass
                return await call_next(request)

        Args:
            session_id: Session ID from cookie.

        Returns:
            Updated SessionData with new expiration.

        Raises:
            SessionNotFoundError: If session not found.
            SessionExpiredError: If session has expired.
        """
        return await self.session_manager.refresh_session(session_id)

    async def validate_csrf_header(
        self,
        session_id: str,
        csrf_header: str | None,
        header_name: str = "X-CSRF-Token",
    ) -> bool:
        """
        Validate CSRF token from request header.

        This is the recommended CSRF validation method for API endpoints.
        The frontend should send the CSRF token in the X-CSRF-Token header.

        Example usage:

            @app.post("/api/transfer")
            async def transfer(request):
                session_id = request.cookies.get("__Host-session")
                csrf_token = request.headers.get("X-CSRF-Token")
                await handler.validate_csrf_header(session_id, csrf_token)
                # ... process request

        Args:
            session_id: Session ID from cookie.
            csrf_header: CSRF token from request header.
            header_name: Header name (for error messages).

        Returns:
            True if valid.

        Raises:
            CSRFValidationError: If header missing or token invalid.
            SessionNotFoundError: If session not found.
        """
        from .core.exceptions import CSRFValidationError

        if not csrf_header:
            raise CSRFValidationError(f"Missing {header_name} header")

        return await self.session_manager.validate_csrf(session_id, csrf_header)

    async def get_authenticated_providers(
        self,
        session_id: str,
    ) -> list[OAuthProvider]:
        """
        Get list of authenticated providers for session.

        Args:
            session_id: Session ID.

        Returns:
            List of authenticated providers.
        """
        return await self.token_vault.list_providers(session_id)

    def get_cookie_options(self) -> dict[str, Any]:
        """
        Get cookie options for setting session cookie.

        Returns:
            Dict of cookie options.
        """
        return self.session_manager.get_cookie_options()

    async def handle_backchannel_logout(
        self,
        logout_token: str,
        provider: OAuthProvider | None = None,
    ) -> int:
        """
        Handle OpenID Connect Back-Channel Logout.

        Validates the logout token and invalidates all sessions for the user.
        Per OpenID Connect Back-Channel Logout 1.0 specification.

        The endpoint receiving this should:
        1. Accept POST request with logout_token form parameter
        2. Call this method with the token
        3. Return 200 OK on success
        4. Return 400 Bad Request on validation failure

        Example endpoint (FastAPI):

            @app.post("/auth/backchannel-logout")
            async def backchannel_logout(logout_token: str = Form(...)):
                try:
                    count = await handler.handle_backchannel_logout(logout_token)
                    return Response(status_code=200)
                except LogoutTokenError as e:
                    return Response(status_code=400, content=str(e))

        Args:
            logout_token: JWT logout token from identity provider.
            provider: Expected provider (for issuer validation). If None,
                checks against all registered providers.

        Returns:
            Number of sessions invalidated.

        Raises:
            LogoutTokenError: If token validation fails.
        """
        import base64
        import json
        from datetime import datetime, timezone

        # Decode JWT payload without signature verification
        # Note: In production, implement full JWKS signature validation
        try:
            parts = logout_token.split(".")
            if len(parts) != 3:
                raise LogoutTokenError("Invalid JWT format")

            # Decode payload
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)
        except LogoutTokenError:
            raise
        except Exception as e:
            raise LogoutTokenError(f"Failed to decode token: {e}")

        # Validate required claims per OIDC Back-Channel Logout spec
        # Required: iss, aud, iat, jti, events
        # Required (one of): sub, sid
        required_claims = ["iss", "aud", "iat", "jti", "events"]
        for claim in required_claims:
            if claim not in claims:
                raise LogoutTokenError(f"Missing required claim: {claim}")

        # Validate events claim contains back-channel logout event
        events = claims.get("events", {})
        if not isinstance(events, dict):
            raise LogoutTokenError("Invalid events claim format")
        if "http://schemas.openid.net/event/backchannel-logout" not in events:
            raise LogoutTokenError("Missing back-channel logout event")

        # Must have either sub or sid
        sub = claims.get("sub")
        sid = claims.get("sid")
        if not sub and not sid:
            raise LogoutTokenError("Token must contain 'sub' or 'sid' claim")

        # Validate issuer against registered providers
        issuer = claims.get("iss")
        audience = claims.get("aud")

        # Audience can be string or list
        if isinstance(audience, str):
            audience = [audience]

        valid_provider = None
        if provider:
            config = self._providers.get(provider.value)
            if config and config.issuer == issuer and config.client_id in audience:
                valid_provider = provider
        else:
            # Check all registered providers
            for key, config in self._providers.items():
                if config.issuer == issuer and config.client_id in audience:
                    valid_provider = OAuthProvider(key)
                    break

        if valid_provider is None:
            raise LogoutTokenError("Issuer/audience not recognized")

        # Validate iat (issued at) - must not be too old
        iat = claims.get("iat")
        if isinstance(iat, int) or isinstance(iat, float):
            issued_at = datetime.fromtimestamp(iat, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            # Reject tokens older than 10 minutes
            max_age = timedelta(minutes=10)
            if now - issued_at > max_age:
                raise LogoutTokenError("Token is too old")

        # Validate exp if present
        exp = claims.get("exp")
        if exp is not None and (isinstance(exp, int) or isinstance(exp, float)):
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                raise LogoutTokenError("Token has expired")

        # Find and invalidate sessions
        sessions_deleted = 0

        if sub:
            # Find all sessions for this user and invalidate them
            sessions = await self.session_manager.find_sessions_by_user(sub)
            for session in sessions:
                # Also clear token vault for each session
                await self.token_vault.clear_vault(session.session_id)
                await self.session_manager.delete_session(session.session_id)
                sessions_deleted += 1

        if sid:
            # Find sessions with matching IdP session ID in metadata
            # This requires scanning sessions - could optimize with secondary index
            # For now, if we already deleted by sub, skip this
            if not sub:
                # Would need to scan all sessions - not implemented yet
                # This is a limitation that should be documented
                pass

        return sessions_deleted

    async def close(self) -> None:
        """Close handler and release resources."""
        for backend in self._backends.values():
            await backend.close()
