# BFFAuth Specification

## Overview

BFFAuth is a Python library implementing the Backend-for-Frontend (BFF) pattern for OAuth 2.0/2.1 as specified in [IETF draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps).

This specification defines the functional requirements, security requirements, and API contracts for the BFFAuth library.

## Version

- **Specification Version**: 1.0.0
- **Target IETF Draft**: draft-ietf-oauth-browser-based-apps-18

---

## 1. Functional Requirements

### 1.1 Core Authentication (Implemented)

| ID | Requirement | Status | Priority |
|----|-------------|--------|----------|
| FR-1.1 | OAuth 2.0 Authorization Code Flow with PKCE | ✅ Done | P0 |
| FR-1.2 | OAuth 2.1 compliance (PKCE mandatory, no implicit) | ✅ Done | P0 |
| FR-1.3 | State parameter generation and validation | ✅ Done | P0 |
| FR-1.4 | Token exchange (code → tokens) | ✅ Done | P0 |
| FR-1.5 | Token refresh with rotation support | ✅ Done | P0 |
| FR-1.6 | Multi-provider support per session | ✅ Done | P0 |

### 1.2 Session Management (Implemented)

| ID | Requirement | Status | Priority |
|----|-------------|--------|----------|
| FR-2.1 | Cryptographically secure session IDs (256-bit) | ✅ Done | P0 |
| FR-2.2 | `__Host-` prefixed session cookies | ✅ Done | P0 |
| FR-2.3 | CSRF token per session | ✅ Done | P0 |
| FR-2.4 | Session expiration with configurable lifetime | ✅ Done | P0 |
| FR-2.5 | Session activity tracking | ✅ Done | P1 |
| FR-2.6 | Sliding session expiration | ⏳ Planned | P1 |
| FR-2.7 | Session revocation (logout all devices) | ⏳ Planned | P2 |

### 1.3 Token Storage (Implemented)

| ID | Requirement | Status | Priority |
|----|-------------|--------|----------|
| FR-3.1 | Encrypted token storage (Fernet AES-128-CBC) | ✅ Done | P0 |
| FR-3.2 | Per-provider token isolation | ✅ Done | P0 |
| FR-3.3 | Token expiration tracking | ✅ Done | P0 |
| FR-3.4 | Automatic token refresh buffer (300s default) | ✅ Done | P1 |
| FR-3.5 | In-memory storage backend | ✅ Done | P0 |
| FR-3.6 | Redis storage backend | ⏳ Planned | P1 |
| FR-3.7 | Database storage backend (SQLAlchemy) | ⏳ Planned | P2 |

### 1.4 Endpoints (Partial)

| ID | Requirement | Status | Priority |
|----|-------------|--------|----------|
| FR-4.1 | `/auth/login` - Initiate OAuth flow | ✅ Done | P0 |
| FR-4.2 | `/auth/callback` - Handle OAuth callback | ✅ Done | P0 |
| FR-4.3 | `/auth/logout` - Terminate session | ✅ Done | P0 |
| FR-4.4 | `/auth/refresh` - Force token refresh | ✅ Done | P1 |
| FR-4.5 | `/auth/userinfo` - Return user information | ✅ Done | P1 |
| FR-4.6 | `/auth/claims` - Return ID token claims | ⏳ Planned | P1 |
| FR-4.7 | `/auth/session` - Return session status | ⏳ Planned | P2 |
| FR-4.8 | `/auth/providers` - List connected providers | ⏳ Planned | P2 |
| FR-4.9 | `/.well-known/bff-config` - Discovery endpoint | ⏳ Planned | P3 |

### 1.5 Logout Features (Partial)

| ID | Requirement | Status | Priority |
|----|-------------|--------|----------|
| FR-5.1 | Local session logout | ✅ Done | P0 |
| FR-5.2 | Provider logout redirect (end_session_endpoint) | ✅ Done | P1 |
| FR-5.3 | ID token hint in logout | ⏳ Planned | P1 |
| FR-5.4 | Back-channel logout (OIDC) | ⏳ Planned | P1 |
| FR-5.5 | Front-channel logout (OIDC) | ⏳ Planned | P2 |
| FR-5.6 | Post-logout redirect URI | ⏳ Planned | P1 |

### 1.6 Silent Authentication (Planned)

| ID | Requirement | Status | Priority |
|----|-------------|--------|----------|
| FR-6.1 | Silent login via iframe | ⏳ Planned | P2 |
| FR-6.2 | prompt=none support | ⏳ Planned | P2 |
| FR-6.3 | Session keepalive | ⏳ Planned | P2 |

### 1.7 API Proxy Integration (Planned)

| ID | Requirement | Status | Priority |
|----|-------------|--------|----------|
| FR-7.1 | Resource server allowlist validation | ✅ Done | P0 |
| FR-7.2 | Token injection to proxied requests | ⏳ Planned | P1 |
| FR-7.3 | API gateway integration patterns | ⏳ Planned | P2 |
| FR-7.4 | Request/response transformation | ⏳ Planned | P3 |

---

## 2. Security Requirements

### 2.1 Cookie Security (Implemented)

| ID | Requirement | Status | Reference |
|----|-------------|--------|-----------|
| SR-1.1 | `__Host-` prefix for session cookies | ✅ Done | IETF 6.2.1 |
| SR-1.2 | `Secure` flag required | ✅ Done | IETF 6.2.1 |
| SR-1.3 | `HttpOnly` flag required | ✅ Done | IETF 6.2.1 |
| SR-1.4 | `SameSite=Strict` for session cookie | ✅ Done | IETF 6.2.2 |
| SR-1.5 | `SameSite=Lax` support for cross-origin | ⏳ Planned | IETF 6.2.2 |
| SR-1.6 | Path=/ enforcement | ✅ Done | IETF 6.2.1 |

### 2.2 CSRF Protection (Implemented)

| ID | Requirement | Status | Reference |
|----|-------------|--------|-----------|
| SR-2.1 | CSRF token per session | ✅ Done | OWASP |
| SR-2.2 | Constant-time token comparison | ✅ Done | OWASP |
| SR-2.3 | CSRF token rotation on sensitive ops | ✅ Done | OWASP |
| SR-2.4 | Custom header validation (X-CSRF-Token) | ⏳ Planned | Duende |
| SR-2.5 | Double-submit cookie pattern | ⏳ Planned | OWASP |

### 2.3 Token Security (Implemented)

| ID | Requirement | Status | Reference |
|----|-------------|--------|-----------|
| SR-3.1 | Tokens encrypted at rest (Fernet) | ✅ Done | IETF 6.2.3 |
| SR-3.2 | Tokens never exposed to browser | ✅ Done | IETF 6.2.3 |
| SR-3.3 | Session-bound token storage | ✅ Done | IETF 6.2.3 |
| SR-3.4 | Refresh token rotation handling | ✅ Done | RFC 6749 |
| SR-3.5 | Token binding validation | ⏳ Planned | RFC 8471 |

### 2.4 OAuth Security (Implemented)

| ID | Requirement | Status | Reference |
|----|-------------|--------|-----------|
| SR-4.1 | PKCE required (SHA256) | ✅ Done | RFC 7636 |
| SR-4.2 | State parameter validation | ✅ Done | RFC 6749 |
| SR-4.3 | Nonce for OIDC | ✅ Done | OIDC Core |
| SR-4.4 | Redirect URI exact match | ✅ Done | RFC 6749 |
| SR-4.5 | Resource server allowlist | ✅ Done | IETF 6.2.4 |

### 2.5 Advanced Security (Planned)

| ID | Requirement | Status | Reference |
|----|-------------|--------|-----------|
| SR-5.1 | Pushed Authorization Requests (PAR) | ⏳ Planned | RFC 9126 |
| SR-5.2 | JWT-Secured Authorization Response (JARM) | ⏳ Planned | OIDC JARM |
| SR-5.3 | Mutual TLS client authentication | ⏳ Planned | RFC 8705 |
| SR-5.4 | DPoP (Demonstrating Proof of Possession) | ⏳ Planned | RFC 9449 |

---

## 3. Provider Requirements

### 3.1 Supported Providers (Implemented)

| Provider | Status | Features |
|----------|--------|----------|
| Google | ✅ Done | OIDC, refresh tokens, userinfo |
| Azure AD | ✅ Done | OIDC, refresh tokens, Graph API |
| Generic OIDC | ✅ Done | Discovery, PKCE, standard claims |
| GitHub | ⏳ Planned | OAuth 2.0 (non-OIDC) |
| Auth0 | ⏳ Planned | OIDC, custom domains |
| Okta | ⏳ Planned | OIDC, SAML bridge |
| Keycloak | ⏳ Planned | OIDC, back-channel logout |

### 3.2 Provider Configuration

```python
class ProviderConfig(BaseModel):
    """OAuth provider configuration."""

    # Required
    client_id: str
    authorize_endpoint: str
    token_endpoint: str

    # Optional (discovered via OIDC)
    userinfo_endpoint: Optional[str] = None
    end_session_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None

    # Security
    client_secret: Optional[SecretStr] = None  # Confidential clients
    pkce_required: bool = True

    # Scopes
    default_scopes: list[str] = ["openid", "profile", "email"]
```

---

## 4. API Contracts

### 4.1 Session Manager Protocol

```python
class SessionManagerProtocol(Protocol):
    """Abstract session management interface."""

    async def create_session(
        self,
        user_id: Optional[str] = None,
        user_info: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> SessionData: ...

    async def get_session(self, session_id: str) -> SessionData: ...

    async def update_session(self, session: SessionData) -> None: ...

    async def delete_session(self, session_id: str) -> bool: ...

    async def validate_csrf(
        self,
        session_id: str,
        csrf_token: str,
        rotate_on_success: bool = False,
    ) -> bool: ...
```

### 4.2 Token Vault Protocol

```python
class TokenVaultProtocol(Protocol):
    """Abstract token storage interface."""

    async def store_token(
        self,
        session_id: str,
        token: TokenRecord,
    ) -> None: ...

    async def get_token(
        self,
        session_id: str,
        provider: OAuthProvider,
    ) -> TokenRecord: ...

    async def get_valid_token(
        self,
        session_id: str,
        provider: OAuthProvider,
    ) -> Optional[TokenRecord]: ...

    async def delete_token(
        self,
        session_id: str,
        provider: OAuthProvider,
    ) -> bool: ...

    async def update_token(
        self,
        session_id: str,
        provider: OAuthProvider,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> TokenRecord: ...
```

### 4.3 Storage Backend Protocol

```python
class StorageBackendProtocol(Protocol):
    """Abstract storage backend for sessions and tokens."""

    async def get(self, key: str) -> Optional[bytes]: ...

    async def set(
        self,
        key: str,
        value: bytes,
        ttl: Optional[int] = None,
    ) -> None: ...

    async def delete(self, key: str) -> bool: ...

    async def exists(self, key: str) -> bool: ...
```

---

## 5. Configuration

### 5.1 Environment Variables

```bash
# Core Settings
BFFAUTH_ENCRYPTION_KEY=          # Required: Fernet key (generate with Fernet.generate_key())
BFFAUTH_SESSION_SECRET=          # Required: Session signing secret
BFFAUTH_SESSION_LIFETIME=86400   # Session lifetime in seconds (default: 24h)

# Cookie Settings
BFFAUTH_COOKIE_NAME=__Host-session
BFFAUTH_COOKIE_SECURE=true       # Must be true in production
BFFAUTH_COOKIE_SAMESITE=strict   # strict or lax

# Security Settings
BFFAUTH_CSRF_HEADER_NAME=X-CSRF-Token
BFFAUTH_TOKEN_REFRESH_BUFFER=300  # Refresh tokens 5min before expiry

# Provider Settings (per provider)
BFFAUTH_GOOGLE_CLIENT_ID=
BFFAUTH_GOOGLE_CLIENT_SECRET=
BFFAUTH_AZURE_CLIENT_ID=
BFFAUTH_AZURE_TENANT_ID=

# Storage Backend
BFFAUTH_STORAGE_BACKEND=memory   # memory, redis, database
BFFAUTH_REDIS_URL=               # For redis backend
BFFAUTH_DATABASE_URL=            # For database backend

# Observability
BFFAUTH_ENABLE_TELEMETRY=false
BFFAUTH_LOG_LEVEL=INFO
```

---

## 6. Competitive Feature Analysis

### 6.1 Feature Comparison Matrix

| Feature | BFFAuth | Duende BFF | Curity | michaelvl | FusionAuth |
|---------|---------|------------|--------|-----------|------------|
| **Core OAuth** |
| PKCE | ✅ | ✅ | ✅ | ✅ | ✅ |
| State validation | ✅ | ✅ | ✅ | ✅ | ✅ |
| Token refresh | ✅ | ✅ | ✅ | ✅ | ✅ |
| Multi-provider | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Session** |
| __Host- cookies | ✅ | ✅ | ✅ | ✅ | ✅ |
| CSRF protection | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sliding expiration | ⏳ | ✅ | ✅ | ❌ | ✅ |
| **Logout** |
| Local logout | ✅ | ✅ | ✅ | ✅ | ✅ |
| Back-channel | ⏳ | ✅ | ✅ | ❌ | ❌ |
| Front-channel | ⏳ | ✅ | ✅ | ❌ | ❌ |
| **Advanced** |
| Silent login | ⏳ | ✅ | ✅ | ❌ | ❌ |
| PAR | ⏳ | ❌ | ✅ | ❌ | ❌ |
| JARM | ⏳ | ❌ | ✅ | ❌ | ❌ |
| mTLS | ⏳ | ❌ | ✅ | ❌ | ❌ |
| **Observability** |
| OpenTelemetry | ⏳ | ✅ | ✅ | ❌ | ❌ |
| Health endpoint | ⏳ | ✅ | ✅ | ❌ | ✅ |
| **Integration** |
| API proxy | ⏳ | ✅ | ✅ | ❌ | ❌ |
| Gateway support | ⏳ | ❌ | ✅ | ❌ | ❌ |

### 6.2 BFFAuth Unique Features

| Feature | Description | Competitor Gap |
|---------|-------------|----------------|
| Python-native | Pure Python, no external runtime | All others are Go/.NET/Java |
| Authlib integration | Leverages battle-tested OAuth library | Custom implementations |
| Pydantic models | Type-safe configuration and validation | Limited typing support |
| Protocol-based | Swappable storage/session backends | Tight coupling in competitors |
| Apache 2.0 | Permissive license | Duende is commercial |
| ADK integration | Native Google ADK support | No AI framework support |

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Metric | Target | Notes |
|--------|--------|-------|
| Session lookup | < 5ms | In-memory backend |
| Token encryption | < 10ms | Fernet AES-128 |
| Token decryption | < 10ms | Fernet AES-128 |
| OAuth callback | < 100ms | Excluding provider latency |

### 7.2 Scalability

| Requirement | Status | Notes |
|-------------|--------|-------|
| Horizontal scaling | ⏳ | Requires external storage backend |
| Multi-instance | ⏳ | Redis/DB backend required |
| Session affinity | N/A | Stateless design goal |

### 7.3 Reliability

| Requirement | Status | Notes |
|-------------|--------|-------|
| Graceful degradation | ⏳ | Fallback when provider unavailable |
| Circuit breaker | ⏳ | For token refresh failures |
| Retry with backoff | ⏳ | For transient failures |

---

## 8. Glossary

| Term | Definition |
|------|------------|
| BFF | Backend-for-Frontend - server-side component handling OAuth for browser apps |
| PKCE | Proof Key for Code Exchange - RFC 7636 extension preventing authorization code interception |
| PAR | Pushed Authorization Requests - RFC 9126 for pre-registering authorization requests |
| JARM | JWT-Secured Authorization Response Mode - signed/encrypted authorization responses |
| DPoP | Demonstrating Proof of Possession - RFC 9449 for token binding |
| mTLS | Mutual TLS - client certificate authentication |

---

## 9. References

- [IETF draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps)
- [RFC 6749 - OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 - PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [RFC 9126 - Pushed Authorization Requests](https://datatracker.ietf.org/doc/html/rfc9126)
- [RFC 9449 - DPoP](https://datatracker.ietf.org/doc/html/rfc9449)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [Duende BFF Documentation](https://docs.duendesoftware.com/identityserver/v7/bff/)
- [Curity Token Handler](https://curity.io/resources/learn/token-handler-overview/)
