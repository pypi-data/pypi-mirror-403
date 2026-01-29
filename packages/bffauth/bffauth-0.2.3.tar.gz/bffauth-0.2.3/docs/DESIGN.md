# BFFAuth Design Document

## Overview

This document describes the detailed design of BFFAuth components, including both implemented features and planned enhancements identified through competitive analysis.

---

## 1. Core Architecture

### 1.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   FastAPI   │  │   Flask     │  │   Django    │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BFFAuth Integration Layer                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Framework Adapters (Middleware)              │   │
│  │     FastAPIBFF    │    FlaskBFF    │    DjangoBFF        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BFFAuth Core Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  Session   │  │   Token    │  │   OAuth    │  │ Allowlist │ │
│  │  Manager   │  │   Vault    │  │  Handler   │  │ Validator │ │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬─────┘ │
│        │               │               │               │        │
│        ▼               ▼               ▼               ▼        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Protocol Interfaces                     │   │
│  │  SessionStorageProtocol │ VaultStorageProtocol │ etc.    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│  │ InMemory │    │  Redis   │    │ Database │                   │
│  │ (Dev)    │    │ (Prod)   │    │ (Prod)   │                   │
│  └──────────┘    └──────────┘    └──────────┘                   │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│  │  Google  │    │  Azure   │    │  Custom  │                   │
│  │  OAuth   │    │   AD     │    │  OIDC    │                   │
│  └──────────┘    └──────────┘    └──────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Interactions

```
                    Browser Request
                          │
                          ▼
┌─────────────────────────────────────────────┐
│            Framework Middleware              │
│  1. Extract session cookie                  │
│  2. Load session from SessionManager        │
│  3. Validate CSRF if POST/PUT/DELETE        │
└─────────────────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │ /login   │  │ /callback│  │ /api/*   │
     └────┬─────┘  └────┬─────┘  └────┬─────┘
          │             │             │
          ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Generate │  │ Exchange │  │  Inject  │
    │ Auth URL │  │  Code    │  │  Token   │
    │ + State  │  │  for     │  │  into    │
    │ + PKCE   │  │  Tokens  │  │  Request │
    └────┬─────┘  └────┬─────┘  └────┬─────┘
          │             │             │
          ▼             ▼             ▼
    ┌──────────────────────────────────────┐
    │           Token Vault                 │
    │  - Store encrypted tokens            │
    │  - Retrieve for API calls            │
    │  - Refresh when expired              │
    └──────────────────────────────────────┘
```

---

## 2. Session Manager Design

### 2.1 Current Implementation

```python
class SessionManager:
    """
    Manages BFF sessions with security best practices.

    Features:
    - Cryptographically secure session IDs (256-bit)
    - __Host- prefixed cookies
    - CSRF tokens per session
    - Constant-time comparisons
    """

    def __init__(
        self,
        storage: SessionStorageProtocol,
        session_lifetime: timedelta = timedelta(hours=24),
        cookie_name: str = "__Host-session",
        cookie_secure: bool = True,
        cookie_samesite: str = "strict",
    ):
        self.storage = storage
        self.session_lifetime = session_lifetime
        self.cookie_config = CookieConfig(
            name=cookie_name,
            secure=cookie_secure,
            httponly=True,
            samesite=cookie_samesite,
            path="/",
        )
```

### 2.2 Planned Enhancement: Sliding Expiration

```python
class SessionManager:
    """Enhanced with sliding expiration support."""

    def __init__(
        self,
        ...,
        sliding_expiration: bool = True,
        sliding_threshold: float = 0.5,  # Extend when 50% lifetime elapsed
    ):
        self.sliding_expiration = sliding_expiration
        self.sliding_threshold = sliding_threshold

    async def get_session(self, session_id: str) -> SessionData:
        """Get session, optionally extending lifetime."""
        session = await self.storage.get(session_id)

        if session is None:
            raise SessionNotFoundError(session_id)

        if session.is_expired():
            await self.storage.delete(session_id)
            raise SessionExpiredError()

        # Sliding expiration logic
        if self.sliding_expiration:
            elapsed = utc_now() - session.created_at
            threshold = self.session_lifetime * self.sliding_threshold

            if elapsed > threshold:
                session.expires_at = utc_now() + self.session_lifetime
                await self.storage.set(session)

        return session
```

### 2.3 Planned Enhancement: Session Revocation

```python
class SessionManager:
    """Enhanced with session revocation for logout-all."""

    async def revoke_user_sessions(self, user_id: str) -> int:
        """
        Revoke all sessions for a user (logout all devices).

        Returns:
            Number of sessions revoked.
        """
        # Requires storage backend to support user_id lookup
        if not hasattr(self.storage, 'get_by_user_id'):
            raise NotImplementedError(
                "Session revocation requires storage with user_id index"
            )

        sessions = await self.storage.get_by_user_id(user_id)
        count = 0

        for session in sessions:
            if await self.storage.delete(session.session_id):
                count += 1

        return count

    async def get_user_sessions(self, user_id: str) -> list[SessionData]:
        """List all active sessions for a user."""
        return await self.storage.get_by_user_id(user_id)
```

---

## 3. Token Vault Design

### 3.1 Current Implementation

```python
class TokenVault:
    """
    Encrypted multi-provider token storage.

    Security:
    - Fernet encryption (AES-128-CBC + HMAC-SHA256)
    - Per-session token isolation
    - Automatic expiration tracking
    """

    def __init__(
        self,
        encryption_key: str,
        storage: VaultStorageProtocol,
        token_refresh_buffer: int = 300,  # 5 minutes
    ):
        self._cipher = Fernet(encryption_key.encode())
        self.storage = storage
        self.token_refresh_buffer = token_refresh_buffer
```

### 3.2 Vault Storage Structure

```python
@dataclass
class TokenVaultEntry:
    """
    Complete token vault for a session.

    Structure:
    {
        "tokens": {
            "google": TokenRecord(...),
            "azure": TokenRecord(...),
        },
        "created_at": datetime,
        "last_accessed": datetime,
    }
    """
    tokens: dict[str, TokenRecord] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    last_accessed: datetime = field(default_factory=utc_now)
```

### 3.3 Planned Enhancement: Token Refresh Coordination

```python
class TokenVault:
    """Enhanced with coordinated token refresh."""

    def __init__(
        self,
        ...,
        refresh_lock_ttl: int = 30,  # Lock expires after 30s
    ):
        self.refresh_lock_ttl = refresh_lock_ttl
        self._refresh_locks: dict[str, asyncio.Lock] = {}

    async def get_or_refresh_token(
        self,
        session_id: str,
        provider: OAuthProvider,
        oauth_client: OAuth2Client,
    ) -> TokenRecord:
        """
        Get valid token, refreshing if necessary.

        Uses locking to prevent thundering herd on refresh.
        """
        # Check for valid token first
        token = await self.get_valid_token(session_id, provider)
        if token is not None:
            return token

        # Need refresh - acquire lock
        lock_key = f"{session_id}:{provider.value}"
        lock = self._get_or_create_lock(lock_key)

        async with lock:
            # Double-check after acquiring lock
            token = await self.get_valid_token(session_id, provider)
            if token is not None:
                return token

            # Perform refresh
            current_token = await self.get_token(session_id, provider)
            if current_token.refresh_token is None:
                raise TokenRefreshError("No refresh token available")

            new_tokens = await oauth_client.refresh_tokens(
                current_token.refresh_token
            )

            # Handle refresh token rotation
            await self.update_token(
                session_id,
                provider,
                access_token=new_tokens.access_token,
                refresh_token=new_tokens.refresh_token,  # May be rotated
                expires_at=new_tokens.expires_at,
            )

            return await self.get_token(session_id, provider)
```

---

## 4. Back-Channel Logout Design (Implemented)

### 4.1 Overview

Back-channel logout (OIDC) allows identity providers to directly notify the BFF when a user logs out, enabling immediate session termination across all applications.

```
┌─────────────┐     1. User logs out     ┌─────────────┐
│   Browser   │ ──────────────────────▶  │   IdP       │
└─────────────┘                          └──────┬──────┘
                                                │
                                    2. POST /backchannel-logout
                                       (Logout Token JWT)
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │   BFFAuth   │
                                         │   Server    │
                                         └──────┬──────┘
                                                │
                                    3. Validate JWT, extract sid/sub
                                    4. Delete matching sessions
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │   Session   │
                                         │   Storage   │
                                         └─────────────┘
```

### 4.2 Implementation (Actual)

Back-channel logout is implemented directly in `BFFOAuthHandler`:

```python
from bffauth import BFFOAuthHandler, LogoutTokenError

# The handler validates logout tokens and terminates sessions
async def handle_backchannel_logout(
    self,
    logout_token: str,
    provider: OAuthProvider | None = None,
) -> int:
    """
    Handle OpenID Connect Back-Channel Logout.

    Args:
        logout_token: JWT logout token from identity provider
        provider: Expected provider (for issuer validation)

    Returns:
        Number of sessions invalidated

    Raises:
        LogoutTokenError: If token validation fails
    """
```

**Validation performed:**

1. **JWT decoding** - Decodes payload without signature verification (signature verification can be added with JWKS)
2. **Required claims** - Validates `iss`, `aud`, `iat`, `jti`, `events` are present
3. **Back-channel logout event** - Verifies `events` contains `http://schemas.openid.net/event/backchannel-logout`
4. **Subject or session** - Requires `sub` or `sid` claim (at least one)
5. **Issuer/audience** - Validates against registered providers
6. **Token freshness** - Rejects tokens older than 10 minutes (`iat` check)
7. **Expiration** - Rejects expired tokens if `exp` claim present

**Session termination:**

```python
# Find all sessions for user
sessions = await self.session_manager.find_sessions_by_user(sub)
for session in sessions:
    # Clear token vault
    await self.token_vault.clear_vault(session.session_id)
    # Delete session
    await self.session_manager.delete_session(session.session_id)
```

**Session storage additions:**

```python
class SessionStorageProtocol(ABC):
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> list[SessionData]:
        """Find all sessions for a user (for back-channel logout)."""
        pass
```

### 4.3 Endpoint Registration

```python
# FastAPI example
from fastapi import APIRouter, Form, Response
from bffauth import BFFOAuthHandler, LogoutTokenError

router = APIRouter()

@router.post("/auth/backchannel-logout")
async def backchannel_logout(
    logout_token: str = Form(...),
    handler: BFFOAuthHandler = Depends(get_handler),
):
    """
    OIDC back-channel logout endpoint.

    Provider sends POST with logout_token form parameter.
    Returns 200 OK on success, 400 Bad Request on validation failure.
    """
    try:
        count = await handler.handle_backchannel_logout(logout_token)
        return Response(status_code=200)
    except LogoutTokenError as e:
        return Response(status_code=400, content=str(e))
```

---

## 5. Silent Login Design (Planned)

### 5.1 Overview

Silent login uses hidden iframes to check authentication status and refresh tokens without user interaction.

```
┌─────────────┐                    ┌─────────────┐
│   Browser   │                    │   BFFAuth   │
│   (SPA)     │                    │   Server    │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │  1. Create hidden iframe         │
       │     /auth/silent?provider=google │
       │─────────────────────────────────▶│
       │                                  │
       │                     2. Check session validity
       │                     3. If valid, redirect with session token
       │                     4. If invalid, redirect with error
       │                                  │
       │  5. postMessage result           │
       │◀─────────────────────────────────│
       │                                  │
```

### 5.2 Implementation Design

```python
class SilentLoginHandler:
    """
    Handles silent login via iframe.

    Used for:
    - Session keepalive
    - Token refresh without redirect
    - SSO session check
    """

    def __init__(
        self,
        session_manager: SessionManager,
        token_vault: TokenVault,
        allowed_origins: list[str],
    ):
        self.session_manager = session_manager
        self.token_vault = token_vault
        self.allowed_origins = allowed_origins

    async def handle_silent_login(
        self,
        session_id: Optional[str],
        provider: str,
        origin: str,
    ) -> SilentLoginResult:
        """
        Handle silent login request from iframe.

        Returns HTML page that posts result to parent window.
        """
        # Validate origin
        if origin not in self.allowed_origins:
            return SilentLoginResult(
                success=False,
                error="invalid_origin",
            )

        if session_id is None:
            return SilentLoginResult(
                success=False,
                error="no_session",
            )

        try:
            # Check session validity
            session = await self.session_manager.get_session(session_id)

            # Check if provider token is valid
            token = await self.token_vault.get_valid_token(
                session_id,
                OAuthProvider(provider),
            )

            if token is None:
                # Try silent refresh at IdP
                return await self._try_silent_refresh(session, provider)

            return SilentLoginResult(
                success=True,
                session_valid=True,
                user_info=session.user_info,
            )

        except SessionNotFoundError:
            return SilentLoginResult(
                success=False,
                error="session_not_found",
            )
        except SessionExpiredError:
            return SilentLoginResult(
                success=False,
                error="session_expired",
            )

    def render_response_page(self, result: SilentLoginResult) -> str:
        """Render HTML page that posts result to parent."""
        return f"""
        <!DOCTYPE html>
        <html>
        <body>
        <script>
            window.parent.postMessage(
                {json.dumps(result.dict())},
                '*'
            );
        </script>
        </body>
        </html>
        """
```

---

## 6. API Proxy Design (Planned)

### 6.1 Overview

The API proxy injects access tokens into requests to backend APIs, hiding token management from the frontend.

```
┌─────────────┐     /api/users      ┌─────────────┐     GET /users        ┌─────────────┐
│   Browser   │ ─────────────────▶  │   BFFAuth   │ ──────────────────▶   │  Backend    │
│   (SPA)     │   (cookie only)     │   Proxy     │   (Bearer token)      │    API      │
└─────────────┘                     └─────────────┘                       └─────────────┘
                                          │
                                    1. Validate session
                                    2. Check allowlist
                                    3. Get token from vault
                                    4. Inject Authorization header
```

### 6.2 Implementation Design

```python
class APIProxy:
    """
    Proxies API requests with token injection.

    Security:
    - Validates session before proxying
    - Checks request URL against allowlist
    - Never exposes tokens to frontend
    """

    def __init__(
        self,
        session_manager: SessionManager,
        token_vault: TokenVault,
        allowlist: AllowlistValidator,
        http_client: httpx.AsyncClient,
    ):
        self.session_manager = session_manager
        self.token_vault = token_vault
        self.allowlist = allowlist
        self.http_client = http_client

    async def proxy_request(
        self,
        request: Request,
        session_id: str,
        target_url: str,
    ) -> Response:
        """
        Proxy request to target URL with token injection.

        Args:
            request: Incoming request
            session_id: Session ID from cookie
            target_url: Target API URL

        Returns:
            Proxied response
        """
        # 1. Validate session
        session = await self.session_manager.get_session(session_id)

        # 2. Validate target against allowlist
        provider = self.allowlist.validate_url(target_url)
        if provider is None:
            raise AllowlistViolationError(target_url)

        # 3. Get valid token
        token = await self.token_vault.get_valid_token(
            session_id,
            provider,
        )

        if token is None:
            raise TokenNotAvailableError(provider.value)

        # 4. Build proxied request
        headers = dict(request.headers)
        headers["Authorization"] = f"Bearer {token.access_token}"

        # Remove BFF-specific headers
        headers.pop("Cookie", None)
        headers.pop("X-CSRF-Token", None)

        # 5. Execute request
        response = await self.http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=await request.body(),
        )

        # 6. Return response (strip sensitive headers)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=self._filter_response_headers(response.headers),
        )

    def _filter_response_headers(
        self,
        headers: httpx.Headers,
    ) -> dict[str, str]:
        """Remove headers that shouldn't be forwarded."""
        blocked = {
            "set-cookie",
            "www-authenticate",
            "transfer-encoding",
        }
        return {
            k: v for k, v in headers.items()
            if k.lower() not in blocked
        }
```

### 6.3 Allowlist Configuration

```python
class AllowlistValidator:
    """
    Validates outbound URLs against allowlist.

    Per IETF 6.2.4, BFF must only forward tokens to trusted APIs.
    """

    def __init__(self, config: AllowlistConfig):
        self.entries = config.entries

    def validate_url(self, url: str) -> Optional[OAuthProvider]:
        """
        Check if URL is allowed and return associated provider.

        Returns:
            Provider if URL matches allowlist, None otherwise.
        """
        parsed = urlparse(url)

        for entry in self.entries:
            if self._matches_entry(parsed, entry):
                return entry.provider

        return None

    def _matches_entry(
        self,
        parsed: ParseResult,
        entry: AllowlistEntry,
    ) -> bool:
        """Check if parsed URL matches allowlist entry."""
        # Check scheme
        if parsed.scheme not in entry.allowed_schemes:
            return False

        # Check host (exact match or wildcard)
        if entry.host.startswith("*."):
            # Wildcard subdomain
            suffix = entry.host[1:]  # .example.com
            if not parsed.netloc.endswith(suffix):
                return False
        else:
            # Exact match
            if parsed.netloc != entry.host:
                return False

        # Check path prefix
        if entry.path_prefix:
            if not parsed.path.startswith(entry.path_prefix):
                return False

        return True


# Configuration example
allowlist_config = AllowlistConfig(
    entries=[
        AllowlistEntry(
            host="api.example.com",
            provider=OAuthProvider.GOOGLE,
            allowed_schemes=["https"],
        ),
        AllowlistEntry(
            host="*.googleapis.com",
            provider=OAuthProvider.GOOGLE,
            path_prefix="/v1/",
            allowed_schemes=["https"],
        ),
        AllowlistEntry(
            host="graph.microsoft.com",
            provider=OAuthProvider.AZURE,
            allowed_schemes=["https"],
        ),
    ]
)
```

---

## 7. OpenTelemetry Integration Design (Planned)

### 7.1 Overview

OpenTelemetry integration provides observability into BFF operations including authentication flows, token management, and API proxying.

### 7.2 Span Structure

```
bffauth.login
├── bffauth.session.create
├── bffauth.oauth.authorize_url
└── bffauth.cookie.set

bffauth.callback
├── bffauth.state.validate
├── bffauth.oauth.exchange
├── bffauth.token.encrypt
├── bffauth.vault.store
└── bffauth.session.update

bffauth.proxy
├── bffauth.session.validate
├── bffauth.allowlist.check
├── bffauth.vault.get_token
├── bffauth.token.refresh (optional)
└── bffauth.http.request
```

### 7.3 Implementation Design

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("bffauth")


class InstrumentedSessionManager:
    """Session manager with OpenTelemetry instrumentation."""

    def __init__(self, session_manager: SessionManager):
        self._inner = session_manager

    async def create_session(self, **kwargs) -> SessionData:
        with tracer.start_as_current_span(
            "bffauth.session.create",
            attributes={
                "bffauth.session.has_user_id": kwargs.get("user_id") is not None,
            },
        ) as span:
            try:
                session = await self._inner.create_session(**kwargs)
                span.set_attribute("bffauth.session.id_prefix", session.session_id[:8])
                return session
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    async def get_session(self, session_id: str) -> SessionData:
        with tracer.start_as_current_span(
            "bffauth.session.get",
            attributes={
                "bffauth.session.id_prefix": session_id[:8],
            },
        ) as span:
            try:
                session = await self._inner.get_session(session_id)
                span.set_attribute("bffauth.session.valid", True)
                return session
            except SessionNotFoundError:
                span.set_attribute("bffauth.session.valid", False)
                span.set_attribute("bffauth.session.error", "not_found")
                raise
            except SessionExpiredError:
                span.set_attribute("bffauth.session.valid", False)
                span.set_attribute("bffauth.session.error", "expired")
                raise


class InstrumentedTokenVault:
    """Token vault with OpenTelemetry instrumentation."""

    def __init__(self, token_vault: TokenVault):
        self._inner = token_vault

    async def get_valid_token(
        self,
        session_id: str,
        provider: OAuthProvider,
    ) -> Optional[TokenRecord]:
        with tracer.start_as_current_span(
            "bffauth.vault.get_token",
            attributes={
                "bffauth.provider": provider.value,
                "bffauth.session.id_prefix": session_id[:8],
            },
        ) as span:
            token = await self._inner.get_valid_token(session_id, provider)

            span.set_attribute("bffauth.token.found", token is not None)
            if token:
                # Log time until expiration (not the token itself!)
                if token.expires_at:
                    ttl = (token.expires_at - utc_now()).total_seconds()
                    span.set_attribute("bffauth.token.ttl_seconds", ttl)

            return token
```

---

## 8. Redis Storage Backend Design (Implemented)

**Status**: ✅ Implemented in v0.2.0

The Redis storage backends provide production-ready session and token vault storage
with automatic TTL management, multi-tenant support, and horizontal scalability.

### 8.1 Installation

```bash
pip install bffauth[redis]
```

### 8.2 Quick Start

```python
import redis.asyncio as redis
from bffauth import BFFOAuthHandler
from bffauth.storage import RedisSessionStorage, RedisVaultStorage

# Create Redis client
client = redis.Redis(host="localhost", port=6379, db=0)

# Create storage backends with custom prefixes
session_storage = RedisSessionStorage(client, key_prefix="myapp:session:")
vault_storage = RedisVaultStorage(client, key_prefix="myapp:vault:")

# Initialize handler with Redis storage
handler = BFFOAuthHandler(
    encryption_key="your-fernet-key",
    session_storage=session_storage,
    token_storage=vault_storage,
)
```

### 8.3 RedisSessionStorage Implementation

```python
class RedisSessionStorage(SessionStorageProtocol):
    """
    Redis-backed session storage for production deployments.

    Features:
    - Automatic TTL management aligned with session expiration
    - Custom key prefix for multi-tenant deployments
    - Sliding expiration support via extend_session()
    - Double-check expiration (Redis TTL + application-level)

    Location: bffauth/storage/redis.py
    """

    def __init__(
        self,
        redis_client: Any,  # redis.asyncio.Redis
        key_prefix: str = "bffauth:session:",
    ):
        self._redis = redis_client
        self._prefix = key_prefix

    async def get(self, session_id: str) -> SessionData | None:
        """Retrieve session, returns None if expired or not found."""
        data = await self._redis.get(self._key(session_id))
        if data is None:
            return None
        session = SessionData.model_validate_json(data)
        if session.is_expired():
            await self.delete(session_id)
            return None
        return session

    async def set(self, session: SessionData) -> None:
        """Store session with automatic TTL from expires_at."""
        ttl = int((session.expires_at - utc_now()).total_seconds())
        if ttl <= 0:
            return  # Don't store expired sessions
        await self._redis.setex(
            self._key(session.session_id),
            ttl,
            session.model_dump_json().encode(),
        )

    async def extend_session(
        self, session_id: str, additional_time: timedelta
    ) -> bool:
        """Extend session expiration (sliding expiration)."""
        session = await self.get(session_id)
        if session is None:
            return False
        session.expires_at = utc_now() + additional_time
        session.touch()
        await self.set(session)
        return True
```

### 8.4 RedisVaultStorage Implementation

```python
class RedisVaultStorage(TokenVaultStorageProtocol):
    """
    Redis-backed token vault storage.

    Features:
    - Stores encrypted vault data (encryption handled by TokenVault)
    - Configurable default TTL (default: 24 hours)
    - Custom key prefix support
    - TTL querying for monitoring

    Location: bffauth/storage/redis.py
    """

    def __init__(
        self,
        redis_client: Any,
        key_prefix: str = "bffauth:vault:",
        default_ttl: int | None = 86400,  # 24 hours
    ):
        self._redis = redis_client
        self._prefix = key_prefix
        self._default_ttl = default_ttl

    async def get(self, session_id: str) -> bytes | None:
        """Retrieve encrypted vault data."""
        return await self._redis.get(self._key(session_id))

    async def set(self, session_id: str, data: bytes) -> None:
        """Store encrypted vault data with TTL."""
        if self._default_ttl:
            await self._redis.setex(self._key(session_id), self._default_ttl, data)
        else:
            await self._redis.set(self._key(session_id), data)

    async def set_with_ttl(self, session_id: str, data: bytes, ttl: int) -> None:
        """Store with custom TTL."""
        await self._redis.setex(self._key(session_id), ttl, data)
```

### 8.5 Key Design Decisions

1. **Protocol-Based Design**: Both storage classes implement the abstract
   protocol interfaces, allowing seamless swapping between in-memory and Redis.

2. **TTL Alignment**: Session storage automatically sets Redis TTL to match
   the session's `expires_at` timestamp, ensuring consistency.

3. **Double-Check Expiration**: Even with Redis TTL, the application checks
   `session.is_expired()` to handle clock skew edge cases.

4. **Key Prefixes**: Support for custom prefixes enables multi-tenant
   deployments and separating data by environment.

5. **Sliding Expiration**: `extend_session()` allows refreshing session
   lifetime on user activity.

### 8.6 Testing

Integration tests run against real Redis to validate behavior:

```bash
# Start Redis
docker run -d --name bffauth-redis -p 6379:6379 redis:7-alpine

# Run integration tests
pytest tests/integration/test_redis_integration.py -v

# Tests include:
# - Session lifecycle (create, get, update, delete)
# - TTL validation
# - CSRF validation with real storage
# - Multi-provider token storage
# - Encryption isolation (different keys can't read each other's data)
```

### 8.7 Future Enhancements (Planned)

```python
class RedisSessionStorage(SessionStorageProtocol):
    """Future enhancements for user-based session management."""

    async def get_by_user_id(self, user_id: str) -> list[SessionData]:
        """Get all sessions for a user (for "logout all devices")."""
        # Requires user ID indexing
        pass

    async def revoke_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user."""
        # For security events or user-initiated logout
        pass
```

---

## 8.8 Legacy Planned Design (Superseded)

The following was the original planned design, preserved for reference.
The actual implementation above is simpler and sufficient for most use cases.

<details>
<summary>Click to expand original design</summary>

```python
class RedisVaultStorage(VaultStorageProtocol):
    """Redis-backed token vault storage."""

    def __init__(
        self,
        redis_client: redis.Redis,
        key_prefix: str = "bffauth:vault:",
    ):
        self.redis = redis_client
        self.key_prefix = key_prefix

    def _vault_key(self, session_id: str) -> str:
        return f"{self.key_prefix}{session_id}"

    async def get(self, session_id: str) -> Optional[bytes]:
        return await self.redis.get(self._vault_key(session_id))

    async def set(self, session_id: str, data: bytes) -> None:
        await self.redis.set(self._vault_key(session_id), data)

    async def delete(self, session_id: str) -> bool:
        result = await self.redis.delete(self._vault_key(session_id))
        return result > 0

    async def exists(self, session_id: str) -> bool:
        return await self.redis.exists(self._vault_key(session_id)) > 0
```

---

## 9. Security Considerations

### 9.1 Cookie Security Matrix

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| `__Host-` prefix | Required | Prevents cookie tossing attacks |
| `Secure` | `true` | Ensures HTTPS-only transmission |
| `HttpOnly` | `true` | Prevents XSS token theft |
| `SameSite` | `Strict` | Prevents CSRF |
| `Path` | `/` | Required for `__Host-` prefix |

### 9.2 Token Security

1. **Encryption**: All tokens encrypted with Fernet (AES-128-CBC + HMAC-SHA256)
2. **Key Rotation**: Support for encryption key rotation (planned)
3. **No Browser Exposure**: Tokens never sent to browser, only session cookie
4. **Allowlist Validation**: Tokens only attached to pre-approved API destinations

### 9.3 CSRF Protection

1. **SameSite Cookie**: Primary defense via `SameSite=Strict`
2. **CSRF Token**: Secondary defense via per-session token
3. **Custom Header**: `X-CSRF-Token` header requirement for state-changing requests
4. **Constant-Time Comparison**: Prevents timing attacks on token validation

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Session creation and validation
- Token encryption/decryption
- CSRF token validation
- Allowlist matching

### 10.2 Integration Tests

- Full OAuth flow with mock provider
- Session lifecycle
- Token refresh flow
- Back-channel logout

### 10.3 Security Tests

- Cookie attribute verification
- CSRF attack simulation
- Token exposure checks
- Allowlist bypass attempts
