# BFFAuth Requirements Document

**Document Version**: 1.0
**Last Updated**: January 2026
**Status**: Active Development (v0.2.0)

---

## 1. Introduction

### 1.1 Purpose

This document defines the functional and non-functional requirements for BFFAuth, a Python library implementing the Backend-for-Frontend (BFF) authentication pattern as specified in [IETF draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps).

### 1.2 Scope

BFFAuth provides server-side OAuth 2.0/2.1 authentication handling for browser-based applications. The library:

- Manages OAuth flows on behalf of frontend applications
- Stores tokens securely on the server (never exposed to browser)
- Provides session management with secure cookies
- Supports multiple OAuth providers per session
- Integrates with Python web frameworks (FastAPI, Flask, Django)

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| BFF | Backend-for-Frontend - A server-side component that handles authentication for SPAs |
| SPA | Single Page Application - Browser-based JavaScript application |
| PKCE | Proof Key for Code Exchange (RFC 7636) - Prevents authorization code interception |
| OIDC | OpenID Connect - Identity layer on top of OAuth 2.0 |
| CSRF | Cross-Site Request Forgery - Attack where malicious site tricks user's browser |
| Fernet | Symmetric encryption scheme using AES-128-CBC with HMAC-SHA256 |
| TTL | Time To Live - Duration before expiration |

### 1.4 References

- [IETF draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps)
- [RFC 6749 - OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 - PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [RFC 7009 - Token Revocation](https://datatracker.ietf.org/doc/html/rfc7009)
- [RFC 6265 - HTTP State Management (Cookies)](https://datatracker.ietf.org/doc/html/rfc6265)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OpenID Connect Back-Channel Logout 1.0](https://openid.net/specs/openid-connect-backchannel-1_0.html)

---

## 2. Overall Description

### 2.1 Product Perspective

BFFAuth is a library (not a standalone service) that integrates into Python web applications. It sits between the browser and OAuth providers:

```
┌─────────┐     Cookie      ┌─────────┐     Token      ┌─────────┐
│ Browser │ ◄────────────► │ BFFAuth │ ◄────────────► │   API   │
│  (SPA)  │   (no tokens)   │  (BFF)  │   (Bearer)     │ Server  │
└─────────┘                 └─────────┘                └─────────┘
                                 │
                                 ▼
                           ┌─────────┐
                           │  OAuth  │
                           │Provider │
                           └─────────┘
```

### 2.2 Product Functions

1. **Session Management**: Create, validate, and destroy user sessions
2. **OAuth Flow Handling**: Initiate and complete OAuth authorization code flows
3. **Token Storage**: Securely store and retrieve access/refresh tokens
4. **Token Lifecycle**: Automatic refresh, revocation, and expiration handling
5. **CSRF Protection**: Prevent cross-site request forgery attacks
6. **Multi-Provider Support**: Handle authentication with multiple OAuth providers

### 2.3 User Classes

| User Class | Description |
|------------|-------------|
| Application Developer | Integrates BFFAuth into their Python web application |
| End User | Authenticates via the application using OAuth providers |
| Security Auditor | Reviews security configuration and compliance |
| DevOps Engineer | Deploys and monitors BFFAuth in production |

### 2.4 Operating Environment

- **Python**: 3.10, 3.11, 3.12
- **Frameworks**: FastAPI, Flask, Django (via adapters)
- **Storage**: In-memory (development), Redis (production), Database (planned)
- **Platforms**: Linux, macOS, Windows

### 2.5 Design Constraints

1. **No Token Exposure**: Tokens MUST never be sent to or accessible by the browser
2. **PKCE Required**: All OAuth flows MUST use PKCE (RFC 7636)
3. **Secure Cookies**: Session cookies MUST use `__Host-` prefix with Secure, HttpOnly, SameSite
4. **Encryption at Rest**: All tokens MUST be encrypted when stored
5. **Protocol-Based**: All external dependencies MUST use protocol-based interfaces

---

## 3. Functional Requirements

### 3.1 Session Management

#### REQ-SM-001: Session Creation
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL create user sessions with:
- Cryptographically secure session ID (minimum 256 bits of entropy)
- CSRF token (minimum 256 bits of entropy)
- Creation timestamp (timezone-aware UTC)
- Expiration timestamp (configurable, default 24 hours)
- Last activity timestamp for session tracking

**Acceptance Criteria**:
- Session IDs are generated using `secrets.token_urlsafe(32)`
- Session IDs are unique across all sessions
- Sessions are stored in configured storage backend

#### REQ-SM-002: Session Retrieval
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL retrieve sessions by session ID with:
- Validation that session exists
- Validation that session has not expired
- Automatic deletion of expired sessions on retrieval attempt

**Acceptance Criteria**:
- Returns `SessionNotFoundError` for unknown session IDs
- Returns `SessionExpiredError` for expired sessions
- Updates last_activity timestamp on successful retrieval

#### REQ-SM-003: Session Destruction
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL destroy sessions with:
- Removal from storage backend
- Associated token vault cleanup
- Optional token revocation with OAuth provider

**Acceptance Criteria**:
- Session is no longer retrievable after destruction
- Returns boolean indicating if session existed

#### REQ-SM-004: Session Cookie Configuration
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL enforce secure cookie attributes:

| Attribute | Requirement |
|-----------|-------------|
| Name | MUST use `__Host-` prefix (e.g., `__Host-session`) |
| Secure | MUST be `true` (HTTPS only) |
| HttpOnly | MUST be `true` (no JavaScript access) |
| SameSite | MUST be `Strict` or `Lax` |
| Path | MUST be `/` when using `__Host-` prefix |

**Acceptance Criteria**:
- Raises `ValueError` if `__Host-` prefix used without `Secure=True`
- Raises `ValueError` if `__Host-` prefix used without `Path=/`

#### REQ-SM-005: Sliding Session Expiration
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL support sliding session expiration:
- Extend session lifetime on user activity
- Configurable extension duration
- Atomic update of expiration timestamp

**Acceptance Criteria**:
- `refresh_session()` extends session by configured lifetime
- Session storage TTL is updated accordingly (for Redis)

#### REQ-SM-006: Session Metadata Storage
**Priority**: P2 (High)
**Status**: ✅ Implemented

The system SHALL store arbitrary metadata with sessions:
- User ID (optional)
- User information dictionary
- Custom metadata dictionary
- List of authenticated providers

**Acceptance Criteria**:
- Metadata survives serialization/deserialization
- OAuth state is stored in metadata during authorization flow

---

### 3.2 CSRF Protection

#### REQ-CSRF-001: CSRF Token Generation
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL generate CSRF tokens with:
- Minimum 256 bits of entropy
- Unique per session
- Cryptographically secure random generation

**Acceptance Criteria**:
- CSRF tokens generated using `secrets.token_urlsafe(32)`
- Each session has exactly one active CSRF token

#### REQ-CSRF-002: CSRF Token Validation
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL validate CSRF tokens with:
- Constant-time comparison (prevent timing attacks)
- Session binding (token only valid for its session)
- Clear error messages on failure

**Acceptance Criteria**:
- Uses `secrets.compare_digest()` for comparison
- Raises `CSRFValidationError` on mismatch
- Optional token rotation after successful validation

#### REQ-CSRF-003: CSRF Header Validation
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL support CSRF token in HTTP headers:
- Configurable header name (default: `X-CSRF-Token`)
- Clear error for missing header
- Integration with existing CSRF validation

**Acceptance Criteria**:
- `validate_csrf_header()` method available on handler
- Raises `CSRFValidationError` with descriptive message if header missing

#### REQ-CSRF-004: CSRF Token Rotation
**Priority**: P2 (High)
**Status**: ✅ Implemented

The system SHALL support CSRF token rotation:
- Generate new token after sensitive operations
- Invalidate previous token
- Atomic token update

**Acceptance Criteria**:
- `rotate_csrf_token()` returns new token
- Previous token no longer valid

---

### 3.3 OAuth Flow Handling

#### REQ-OAUTH-001: Authorization URL Generation
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL generate OAuth authorization URLs with:
- PKCE code verifier (43-128 characters, RFC 7636)
- PKCE code challenge (S256 method)
- State parameter (minimum 256 bits)
- Configured scopes
- Redirect URI

**Acceptance Criteria**:
- Code verifier uses unreserved characters only
- Code challenge is base64url-encoded SHA-256 of verifier
- State is cryptographically random

#### REQ-OAUTH-002: State Parameter Management
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL manage OAuth state parameters:
- Store state with session (not in handler memory)
- Associate state with provider and PKCE verifier
- Enforce state expiration (configurable, default 10 minutes)
- One-time use (delete after callback)

**Acceptance Criteria**:
- State stored in `session.metadata["oauth_state"]`
- State validated on callback
- State removed after successful callback
- `StateValidationError` raised for mismatch or expiration

#### REQ-OAUTH-003: Authorization Code Exchange
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL exchange authorization codes for tokens:
- Include PKCE code verifier
- Validate response from provider
- Handle error responses from provider
- Parse token response (access_token, refresh_token, expires_in)

**Acceptance Criteria**:
- Raises `TokenExchangeError` on failure
- Parses ID token claims if present
- Calculates token expiration from `expires_in` or `expires_at`

#### REQ-OAUTH-004: Token Refresh
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL refresh expired tokens:
- Use refresh token to obtain new access token
- Handle refresh token rotation
- Update stored tokens atomically
- Raise appropriate error if refresh fails

**Acceptance Criteria**:
- Automatic refresh when accessing expired token (configurable)
- Raises `TokenRefreshError` on failure
- Updates both access and refresh tokens if rotated

#### REQ-OAUTH-005: Token Revocation
**Priority**: P2 (High)
**Status**: ✅ Implemented

The system SHALL revoke tokens with OAuth provider:
- Revoke access token
- Revoke refresh token (if present)
- Handle providers that don't support revocation
- Non-blocking (failures don't prevent logout)

**Acceptance Criteria**:
- Uses RFC 7009 token revocation endpoint
- Gracefully handles revocation failures
- Optional (configurable per logout)

#### REQ-OAUTH-006: Multi-Provider Support
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL support multiple OAuth providers:
- Register multiple provider configurations
- Store tokens per provider per session
- Independent token lifecycle per provider
- Provider-specific logout

**Acceptance Criteria**:
- Same session can have tokens for Google, Azure, GitHub, etc.
- `list_providers()` returns authenticated providers
- Logout can target specific provider or all

---

### 3.4 Token Storage

#### REQ-TS-001: Token Encryption
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL encrypt tokens at rest:
- Use Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)
- Encryption key provided by application
- Validate encryption key format on initialization

**Acceptance Criteria**:
- Raises `InvalidEncryptionKeyError` for invalid keys
- Stored data is not readable without key
- Different keys cannot decrypt each other's data

#### REQ-TS-002: Token Storage Protocol
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL use protocol-based token storage:
- `TokenVaultStorageProtocol` interface
- In-memory implementation for development
- Redis implementation for production
- Swappable without code changes

**Acceptance Criteria**:
- Storage backend injected via constructor
- Default to in-memory if not specified
- All implementations pass same test suite

#### REQ-TS-003: Token Expiration Tracking
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL track token expiration:
- Store `expires_at` timestamp with token
- Pre-emptive refresh buffer (default 5 minutes)
- `is_expired()` check with buffer consideration

**Acceptance Criteria**:
- `get_valid_token()` returns None for expired tokens
- Refresh buffer configurable per vault instance

#### REQ-TS-004: Token Record Structure
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL store complete token records:

| Field | Type | Required |
|-------|------|----------|
| provider | OAuthProvider | Yes |
| access_token | str | Yes |
| refresh_token | str | No |
| token_type | str | Yes (default: "Bearer") |
| expires_at | datetime | No |
| scope | str | No |
| id_token | str | No |
| issued_at | datetime | Yes |
| metadata | dict | No |

---

### 3.5 Storage Backends

#### REQ-SB-001: In-Memory Storage
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL provide in-memory storage for development:
- `InMemorySessionStorage` for sessions
- `InMemoryVaultStorage` for tokens
- Automatic expired session cleanup
- NOT suitable for production (no persistence, single-instance only)

**Acceptance Criteria**:
- Default storage when none specified
- Implements all protocol methods
- Warning in documentation about production use

#### REQ-SB-002: Redis Session Storage
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL provide Redis session storage:
- Automatic TTL aligned with session expiration
- Custom key prefix for multi-tenant deployments
- Sliding expiration support
- Connection via `redis.asyncio.Redis`

**Acceptance Criteria**:
- TTL set to remaining session lifetime on store
- Expired sessions automatically removed by Redis
- Key format: `{prefix}{session_id}`

#### REQ-SB-003: Redis Vault Storage
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL provide Redis vault storage:
- Configurable default TTL (default: 24 hours)
- Custom key prefix support
- Custom TTL per operation
- TTL querying for monitoring

**Acceptance Criteria**:
- Encrypted data stored as bytes
- TTL configurable or disabled (None)
- `get_ttl()` returns remaining seconds

#### REQ-SB-004: Storage Protocol Interface
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL define abstract storage protocols:

**SessionStorageProtocol**:
```python
async def get(session_id: str) -> SessionData | None
async def set(session: SessionData) -> None
async def delete(session_id: str) -> bool
async def cleanup_expired() -> int
```

**TokenVaultStorageProtocol**:
```python
async def get(session_id: str) -> bytes | None
async def set(session_id: str, data: bytes) -> None
async def delete(session_id: str) -> bool
async def exists(session_id: str) -> bool
```

---

### 3.6 Provider Configuration

#### REQ-PC-001: Google OAuth Configuration
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL support Google OAuth:
- Authorization endpoint: `https://accounts.google.com/o/oauth2/v2/auth`
- Token endpoint: `https://oauth2.googleapis.com/token`
- Revocation endpoint: `https://oauth2.googleapis.com/revoke`
- Userinfo endpoint: `https://openidconnect.googleapis.com/v1/userinfo`
- Default scopes: `openid`, `email`, `profile`

#### REQ-PC-002: Azure AD Configuration
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL support Azure AD / Entra ID:
- Support for single-tenant and multi-tenant
- Support for Azure AD B2C
- Configurable tenant ID
- Default scopes: `openid`, `email`, `profile`

#### REQ-PC-003: GitHub OAuth Configuration
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL support GitHub OAuth:
- Authorization endpoint: `https://github.com/login/oauth/authorize`
- Token endpoint: `https://github.com/login/oauth/access_token`
- Userinfo endpoint: `https://api.github.com/user`
- Support for GitHub Enterprise (custom base URL)

#### REQ-PC-004: Generic OIDC Configuration
**Priority**: P2 (High)
**Status**: ✅ Implemented

The system SHALL support generic OIDC providers:
- Manual endpoint configuration
- OIDC discovery support (planned)
- Custom scope configuration
- Provider-specific parameters

---

### 3.7 Resource Server Allowlist

#### REQ-AL-001: Allowlist Configuration
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL validate resource servers before token injection:
- URL pattern matching (regex-based)
- HTTP method restrictions
- Required scope validation
- Provider restrictions

**Acceptance Criteria**:
- Token NOT injected if URL doesn't match allowlist
- Raises `ResourceNotAllowedError` for denied requests

#### REQ-AL-002: Allowlist Entry Structure
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

Each allowlist entry SHALL contain:

| Field | Type | Description |
|-------|------|-------------|
| name | str | Human-readable identifier |
| url_pattern | str | Regex pattern for URL matching |
| methods | list[str] | Allowed HTTP methods (empty = all) |
| required_scopes | list[str] | Scopes required for access |
| allowed_providers | list[OAuthProvider] | Providers allowed (empty = all) |
| enabled | bool | Whether entry is active |

---

### 3.8 Logout Handling

#### REQ-LO-001: Single Provider Logout
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL support logout from single provider:
- Remove token from vault
- Optionally revoke token with provider
- Update session to remove provider
- Session remains valid for other providers

#### REQ-LO-002: Full Logout
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL support full logout:
- Revoke all tokens (optional)
- Clear token vault for session
- Destroy session
- Clear session cookie

#### REQ-LO-003: Back-Channel Logout
**Priority**: P1 (Critical)
**Status**: ✅ Implemented (v0.2.0)

The system SHALL support OIDC back-channel logout:
- ✅ `handler.handle_backchannel_logout(logout_token)` method
- ✅ Validate logout token claims (iss, aud, iat, jti, events)
- ✅ Terminate sessions matching `sub` claim
- ✅ Return session count; raises `LogoutTokenError` on validation failure
- ⏳ Full JWT signature verification with JWKS (planned enhancement)

#### REQ-LO-004: RP-Initiated Logout
**Priority**: P1 (Critical)
**Status**: ✅ Implemented (v0.2.0)

The system SHALL support OIDC RP-Initiated Logout:
- ✅ `handler.get_logout_url(session_id, provider)` method
- ✅ Include `id_token_hint` when ID token available
- ✅ Support `post_logout_redirect_uri` parameter
- ✅ Support `state` parameter for redirect verification
- ✅ Fall back to `client_id` when ID token unavailable
- ✅ Return `None` if provider has no `end_session_endpoint`

---

## 4. Non-Functional Requirements

### 4.1 Performance

#### REQ-PERF-001: Session Operations
**Priority**: P2 (High)

Session operations SHALL meet these performance targets:

| Operation | Target Latency (p99) |
|-----------|---------------------|
| Create session | < 5ms (in-memory), < 20ms (Redis) |
| Get session | < 2ms (in-memory), < 10ms (Redis) |
| Update session | < 5ms (in-memory), < 20ms (Redis) |
| Delete session | < 2ms (in-memory), < 10ms (Redis) |

#### REQ-PERF-002: Token Operations
**Priority**: P2 (High)

Token vault operations SHALL meet these performance targets:

| Operation | Target Latency (p99) |
|-----------|---------------------|
| Store token | < 10ms (in-memory), < 30ms (Redis) |
| Get token | < 5ms (in-memory), < 15ms (Redis) |
| Encrypt/decrypt | < 5ms |

#### REQ-PERF-003: Memory Usage
**Priority**: P2 (High)

Memory usage SHALL be bounded:
- Session object: < 2KB typical
- Token vault entry: < 4KB per provider
- In-memory storage: Configurable maximum sessions

---

### 4.2 Scalability

#### REQ-SCALE-001: Horizontal Scaling
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL support horizontal scaling:
- Stateless handler design (no in-memory state)
- OAuth state stored in session (not handler)
- External storage backends (Redis)
- Load balancer compatible

#### REQ-SCALE-002: Multi-Instance Deployment
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL work with multiple instances:
- Any instance can handle any request
- Session affinity NOT required
- Shared storage backend required

---

### 4.3 Reliability

#### REQ-REL-001: Graceful Degradation
**Priority**: P2 (High)

The system SHALL degrade gracefully:
- Storage backend unavailable: Clear error, no data loss
- OAuth provider unavailable: Token refresh fails gracefully
- Encryption key rotation: Planned migration path

#### REQ-REL-002: Error Handling
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL provide comprehensive error handling:
- Typed exception hierarchy
- Descriptive error messages
- No sensitive data in error messages
- Proper HTTP status code mapping

---

### 4.4 Security

#### REQ-SEC-001: Token Confidentiality
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

Tokens SHALL never be exposed to untrusted parties:
- Never sent to browser in any form
- Never logged in plain text
- Encrypted at rest in storage
- Encrypted in transit (HTTPS required)

#### REQ-SEC-002: Cookie Security
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

Session cookies SHALL be protected:
- `__Host-` prefix enforced
- `Secure` flag required
- `HttpOnly` flag required
- `SameSite=Strict` or `Lax` required

#### REQ-SEC-003: Cryptographic Requirements
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL use strong cryptography:
- Session IDs: 256 bits of entropy (via `secrets`)
- CSRF tokens: 256 bits of entropy
- PKCE verifiers: 256 bits of entropy
- Token encryption: AES-128-CBC with HMAC-SHA256 (Fernet)

#### REQ-SEC-004: Timing Attack Prevention
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL prevent timing attacks:
- Constant-time CSRF comparison (`secrets.compare_digest`)
- Constant-time state validation
- No early exit on partial match

#### REQ-SEC-005: Input Validation
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

All inputs SHALL be validated:
- Pydantic models for data validation
- URL validation for redirect URIs
- Enum validation for providers
- Length limits on all string fields

---

### 4.5 Maintainability

#### REQ-MAINT-001: Code Quality
**Priority**: P2 (High)
**Status**: ✅ Implemented

The codebase SHALL maintain quality standards:
- Type annotations (mypy strict mode)
- Code formatting (Black)
- Linting (Ruff)
- Pre-commit hooks enforced

#### REQ-MAINT-002: Test Coverage
**Priority**: P2 (High)
**Status**: ✅ Implemented

The system SHALL have comprehensive tests:
- Unit tests for all components
- Integration tests with real Redis
- Mock consistency tests
- Target: 90% code coverage

#### REQ-MAINT-003: Documentation
**Priority**: P2 (High)
**Status**: ✅ Implemented

Documentation SHALL be maintained:
- API documentation (docstrings)
- Architecture documentation
- Testing guide
- Changelog

---

### 4.6 Compatibility

#### REQ-COMPAT-001: Python Version Support
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The system SHALL support:
- Python 3.10 (minimum)
- Python 3.11
- Python 3.12

#### REQ-COMPAT-002: Framework Compatibility
**Priority**: P2 (High)
**Status**: ⏳ Planned

The system SHALL provide adapters for:
- FastAPI (with middleware and dependencies)
- Flask (with extension)
- Django (with middleware)

#### REQ-COMPAT-003: Async Support
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

All I/O operations SHALL be async:
- Storage operations
- OAuth HTTP requests
- Token operations

---

## 5. Interface Requirements

### 5.1 API Interface

#### REQ-API-001: Handler Interface
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

The main handler SHALL provide:

```python
class BFFOAuthHandler:
    # Initialization
    def __init__(encryption_key, session_storage, token_storage, ...)

    # Provider management
    def register_provider(config: ProviderConfig) -> None
    def get_provider(provider: OAuthProvider) -> ProviderConfig

    # OAuth flow
    async def start_authorization(provider, scope, ...) -> tuple[str, SessionData]
    async def handle_callback(session_id, code, state, ...) -> AuthorizationResult

    # Token access
    async def get_access_token(session_id, provider, auto_refresh) -> str

    # Session management
    async def get_session(session_id) -> SessionData
    async def refresh_session(session_id) -> SessionData
    async def logout(session_id, provider, revoke_tokens) -> None

    # CSRF protection
    async def validate_csrf(session_id, csrf_token) -> bool
    async def validate_csrf_header(session_id, header_value) -> bool

    # Utilities
    def get_cookie_options() -> dict
    async def get_authenticated_providers(session_id) -> list[OAuthProvider]
    async def close() -> None
```

### 5.2 Data Models

#### REQ-DM-001: Pydantic Models
**Priority**: P1 (Critical)
**Status**: ✅ Implemented

All data models SHALL use Pydantic:
- `SessionData` - Session state
- `TokenRecord` - Token information
- `ProviderConfig` - OAuth provider settings
- `OAuthState` - Authorization flow state
- `AllowedResource` - Allowlist entry

---

## 6. Constraints and Assumptions

### 6.1 Constraints

1. **HTTPS Required**: Production deployments MUST use HTTPS
2. **Browser Compatibility**: Requires browser support for `__Host-` cookies
3. **Storage Required**: Production deployments require external storage (Redis)
4. **Key Management**: Application responsible for encryption key security

### 6.2 Assumptions

1. OAuth providers are compliant with OAuth 2.0/OIDC specifications
2. Network connectivity to OAuth providers is available
3. Clock synchronization between BFF and providers (for token expiration)
4. Application handles encryption key rotation

---

## 7. Acceptance Criteria

### 7.1 Phase 1 Acceptance (v0.1.0) ✅

- [ ] Session creation with secure IDs
- [ ] CSRF token generation and validation
- [ ] OAuth authorization flow with PKCE
- [ ] Token storage with encryption
- [ ] Multi-provider support
- [ ] In-memory storage backend
- [ ] Unit test coverage > 80%

### 7.2 Phase 2 Acceptance (v0.2.0) 🔄

- [x] Redis storage backends
- [x] Sliding session expiration
- [x] CSRF header validation
- [x] OAuth state in session storage
- [x] Integration tests with Redis
- [ ] Back-channel logout endpoint

### 7.3 Phase 3 Acceptance (v0.3.0)

- [ ] API proxy with token injection
- [ ] Silent login support
- [ ] OpenTelemetry integration
- [ ] Health/ready endpoints

### 7.4 v1.0.0 Release Criteria

- [ ] All Phase 1-3 features complete
- [ ] Framework integrations (FastAPI, Flask)
- [ ] Production deployment documentation
- [ ] Security audit completed
- [ ] Performance benchmarks documented

---

## 8. Appendices

### A. Exception Hierarchy

```
BFFAuthError
├── ConfigurationError
│   └── ProviderNotConfiguredError
├── SessionError
│   ├── SessionNotFoundError
│   ├── SessionExpiredError
│   └── CSRFValidationError
├── TokenError
│   ├── TokenNotFoundError
│   ├── TokenExpiredError
│   ├── TokenRefreshError
│   └── TokenRevocationError
├── EncryptionError
│   ├── InvalidEncryptionKeyError
│   └── DecryptionError
├── OAuthError
│   ├── AuthorizationError
│   ├── StateValidationError
│   ├── TokenExchangeError
│   └── PKCEError
├── AllowlistError
│   └── ResourceNotAllowedError
└── StorageError
    ├── StorageUnavailableError
    ├── StorageWriteError
    └── StorageReadError
```

### B. Configuration Reference

```python
# Handler configuration
BFFOAuthHandler(
    encryption_key="base64-encoded-fernet-key",
    redirect_base_uri="https://app.example.com",
    callback_path="/auth/callback",
    session_lifetime=timedelta(hours=24),
    token_refresh_buffer=300,  # seconds
    session_storage=RedisSessionStorage(...),
    token_storage=RedisVaultStorage(...),
    cookie_name="__Host-session",
    cookie_secure=True,
    cookie_samesite="strict",
)

# Redis storage configuration
RedisSessionStorage(
    redis_client=redis.Redis(...),
    key_prefix="myapp:session:",
)

RedisVaultStorage(
    redis_client=redis.Redis(...),
    key_prefix="myapp:vault:",
    default_ttl=86400,  # 24 hours
)
```

### C. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | BFFAuth Team | Initial requirements document |
