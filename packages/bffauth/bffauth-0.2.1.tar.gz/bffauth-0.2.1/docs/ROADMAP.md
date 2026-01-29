# BFFAuth Roadmap

## Overview

This roadmap outlines the development plan for BFFAuth, organized into phases based on priority and dependencies. Features are prioritized based on:

1. **Core functionality** - Essential for BFF operation
2. **Competitive parity** - Features present in competitor implementations
3. **Advanced features** - Differentiating capabilities

---

## Project Goal

**Primary Objective**: Publish BFFAuth to PyPI as the first Python-native BFF authentication library implementing the IETF draft-ietf-oauth-browser-based-apps specification.

**Package Name**: `bffauth` (confirmed available on PyPI)

**Repository**: https://github.com/ShadNygren/bffauth (public, accepting beta testers)

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 0.1.0 | Jan 2025 | Core session management, token vault, basic OAuth - **Released on PyPI** |
| 0.2.0 | In Progress | Back-channel logout, Redis storage, sliding sessions |
| 0.3.0 | Planned | API proxy, OpenTelemetry, silent login |
| 1.0.0 | Planned | Production-ready, full competitive parity, **PyPI stable release** |
| 1.1.0 | Future | Financial-grade OIDC (PAR, JARM, mTLS) |

---

## Phase 1: Core Foundation (Complete)

**Status**: ✅ Complete

### 1.1 Session Management
- [x] Cryptographically secure session IDs (256-bit)
- [x] `__Host-` prefixed cookies
- [x] CSRF token generation and validation
- [x] Session expiration tracking
- [x] Session activity tracking (last_activity)
- [x] In-memory session storage

### 1.2 Token Vault
- [x] Fernet encryption (AES-128-CBC + HMAC-SHA256)
- [x] Multi-provider token storage per session
- [x] Token expiration tracking
- [x] Token refresh buffer (pre-emptive refresh)
- [x] In-memory vault storage

### 1.3 OAuth Core
- [x] Authorization code flow with PKCE
- [x] State parameter generation and validation
- [x] Token exchange
- [x] Token refresh
- [x] Provider abstraction (Google, Azure, Generic OIDC)

### 1.4 Security Fundamentals
- [x] Cookie security (Secure, HttpOnly, SameSite)
- [x] CSRF protection
- [x] Constant-time token comparison
- [x] Resource server allowlist

---

## Phase 2: Production Essentials (Complete)

**Status**: ✅ Complete
**Target**: v0.2.0
**Completed**: January 2025

### Completed Features

1. **Redis Storage Backend** ✅
   - `RedisSessionStorage` implementing `SessionStorageProtocol`
   - `RedisVaultStorage` implementing `TokenVaultStorageProtocol`
   - Automatic TTL-based expiration aligned with session lifetime
   - Custom key prefix support for multi-tenant deployments
   - 15 integration tests against real Redis server

2. **OAuth State Migration** ✅
   - Moved `_pending_states` from handler memory to session metadata
   - State is session-bound and serialized for storage compatibility
   - Enables stateless handler for horizontal scaling
   - Automatic cleanup after successful callback (one-time use)

3. **Sliding Session Expiration** ✅
   - `handler.refresh_session(session_id)` method
   - `storage.extend_session(session_id, timedelta)` for direct TTL extension
   - Example middleware usage documented in docstrings

4. **CSRF Header Validation** ✅
   - `handler.validate_csrf_header(session_id, header_value)` method
   - Validates `X-CSRF-Token` header (configurable name)
   - Clear error messages for missing or invalid tokens

5. **Back-channel Logout** ✅
   - `handler.handle_backchannel_logout(logout_token)` method
   - Validates logout token per OIDC Back-Channel Logout 1.0 spec
   - Session termination by `sub` claim
   - New `LogoutTokenError` exception for validation failures
   - `find_by_user_id()` method in session storage protocol

### 2.1 Session Enhancements

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Sliding session expiration | P1 | 2h | ✅ Complete |
| Session revocation (logout all) | P2 | 3h | ⏳ Planned |
| User session listing | P2 | 2h | ⏳ Planned |

**Implementation**:

```python
# Sliding expiration - call on each request
await handler.refresh_session(session_id)

# Or use storage directly
await storage.extend_session(session_id, timedelta(hours=2))
```

### 2.2 Logout Enhancements

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| ID token hint in logout | P1 | 1h | ✅ Complete |
| Post-logout redirect URI | P1 | 1h | ✅ Complete |
| Back-channel logout endpoint | P1 | 4h | ✅ Complete |
| Logout token JWT validation | P1 | 2h | ✅ Complete |
| Front-channel logout support | P2 | 3h | ⏳ Planned |

**Back-Channel Logout Implementation**:

```python
@router.post("/backchannel-logout/{provider}")
async def backchannel_logout(
    provider: str,
    logout_token: str = Form(...),
):
    """
    OIDC back-channel logout endpoint.

    Validates logout token and terminates matching sessions.
    """
    claims = validate_logout_token(logout_token, provider)
    sessions_terminated = await terminate_sessions(
        provider=provider,
        sid=claims.get("sid"),
        sub=claims.get("sub"),
    )
    return Response(status_code=200)
```

### 2.3 Redis Storage Backend

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Redis session storage | P1 | 3h | ✅ Complete |
| Redis vault storage | P1 | 2h | ✅ Complete |
| User ID indexing for revocation | P1 | 2h | ⏳ Planned |
| TTL-based expiration | P1 | 1h | ✅ Complete |
| Connection pooling | P2 | 1h | ✅ Via redis-py |

**Usage**:

```python
import redis.asyncio as redis
from bffauth.storage import RedisSessionStorage, RedisVaultStorage

client = redis.Redis(host="localhost", port=6379, db=0)
session_storage = RedisSessionStorage(client, key_prefix="myapp:")
vault_storage = RedisVaultStorage(client, key_prefix="myapp:")

handler = BFFOAuthHandler(
    encryption_key=key,
    session_storage=session_storage,
    token_storage=vault_storage,
)
```

### 2.4 CSRF Enhancements

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Custom header validation (X-CSRF-Token) | P1 | 2h | ✅ Complete |
| Double-submit cookie pattern | P2 | 2h | ⏳ Planned |
| CSRF token in meta tag | P2 | 1h | ⏳ Planned |

**Usage**:

```python
# Validate CSRF header in API endpoints
await handler.validate_csrf_header(
    session_id,
    request.headers.get("X-CSRF-Token"),
)
```

---

## Phase 3: API Integration (Planned)

**Status**: ⏳ Planned
**Target**: v0.3.0

### 3.1 API Proxy

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Basic proxy with token injection | P1 | 4h | ⏳ Planned |
| Allowlist URL validation | P1 | 2h | ⏳ Planned |
| Request/response streaming | P2 | 3h | ⏳ Planned |
| Header filtering | P1 | 1h | ⏳ Planned |
| Error handling and retries | P2 | 2h | ⏳ Planned |

**Proxy Design**:

```python
# FastAPI integration example
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(
    request: Request,
    path: str,
    session: SessionData = Depends(get_session),
):
    target_url = f"https://api.example.com/{path}"
    return await bff.proxy(request, target_url, provider="google")
```

### 3.2 Silent Login

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Silent login endpoint | P2 | 3h | ⏳ Planned |
| iframe response page | P2 | 1h | ⏳ Planned |
| Origin validation | P1 | 1h | ⏳ Planned |
| Session keepalive | P2 | 2h | ⏳ Planned |
| prompt=none support | P2 | 1h | ⏳ Planned |

### 3.3 Additional Endpoints

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| /auth/claims endpoint | P2 | 2h | ⏳ Planned |
| /auth/session status endpoint | P2 | 1h | ⏳ Planned |
| /auth/providers list endpoint | P3 | 1h | ⏳ Planned |
| /.well-known/bff-config discovery | P3 | 2h | ⏳ Planned |

---

## Phase 4: Observability (Planned)

**Status**: ⏳ Planned
**Target**: v0.3.0

### 4.1 OpenTelemetry Integration

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Trace instrumentation | P2 | 4h | ⏳ Planned |
| Span attributes | P2 | 2h | ⏳ Planned |
| Metric collection | P2 | 3h | ⏳ Planned |
| Error tracking | P2 | 2h | ⏳ Planned |

**Trace Structure**:

```
bffauth.login
├── bffauth.session.create
├── bffauth.oauth.authorize_url
└── bffauth.cookie.set

bffauth.callback
├── bffauth.state.validate
├── bffauth.oauth.exchange
├── bffauth.vault.store
└── bffauth.session.update
```

### 4.2 Health and Diagnostics

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| /health endpoint | P1 | 1h | ⏳ Planned |
| /ready endpoint | P1 | 1h | ⏳ Planned |
| Storage connectivity check | P1 | 1h | ⏳ Planned |
| Provider connectivity check | P2 | 2h | ⏳ Planned |
| Diagnostics endpoint (dev mode) | P3 | 2h | ⏳ Planned |

---

## Phase 5: Framework Integrations (Planned)

**Status**: ⏳ Planned
**Target**: v0.4.0

### 5.1 FastAPI Integration

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Middleware class | P1 | 3h | ⏳ Planned |
| Dependency injection helpers | P1 | 2h | ⏳ Planned |
| Router with auth endpoints | P1 | 2h | ⏳ Planned |
| Example application | P2 | 2h | ⏳ Planned |

### 5.2 Flask Integration

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Extension class | P2 | 3h | ⏳ Planned |
| Decorator helpers | P2 | 2h | ⏳ Planned |
| Blueprint with auth routes | P2 | 2h | ⏳ Planned |
| Example application | P2 | 2h | ⏳ Planned |

### 5.3 Django Integration

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Middleware class | P3 | 3h | ⏳ Planned |
| View decorators | P3 | 2h | ⏳ Planned |
| URL configuration | P3 | 2h | ⏳ Planned |
| Example application | P3 | 2h | ⏳ Planned |

---

## Phase 6: Production Hardening (Planned)

**Status**: ⏳ Planned
**Target**: v1.0.0

### 6.1 Database Storage Backend

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| SQLAlchemy models | P2 | 3h | ⏳ Planned |
| Session storage implementation | P2 | 2h | ⏳ Planned |
| Vault storage implementation | P2 | 2h | ⏳ Planned |
| Migration scripts | P2 | 2h | ⏳ Planned |
| Async support (asyncpg) | P2 | 2h | ⏳ Planned |

### 6.2 Token Refresh Coordination

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Refresh lock mechanism | P1 | 2h | ⏳ Planned |
| Thundering herd prevention | P1 | 2h | ⏳ Planned |
| Refresh failure handling | P1 | 2h | ⏳ Planned |
| Token rotation support | P1 | 2h | ⏳ Planned |

### 6.3 Security Hardening

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Encryption key rotation | P2 | 4h | ⏳ Planned |
| Rate limiting | P2 | 3h | ⏳ Planned |
| Session binding (fingerprint) | P3 | 3h | ⏳ Planned |
| Audit logging | P2 | 3h | ⏳ Planned |

### 6.4 Additional Providers

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| GitHub OAuth | P2 | 2h | ⏳ Planned |
| Auth0 | P2 | 2h | ⏳ Planned |
| Okta | P2 | 2h | ⏳ Planned |
| Keycloak | P2 | 2h | ⏳ Planned |

---

## Phase 7: Advanced Features (Future)

**Status**: 📋 Future
**Target**: v1.1.0+

### 7.1 Financial-Grade OIDC (FAPI)

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Pushed Authorization Requests (PAR) | P3 | 6h | 📋 Future |
| JWT-Secured Authorization Response (JARM) | P3 | 6h | 📋 Future |
| Mutual TLS client authentication | P3 | 8h | 📋 Future |
| DPoP token binding | P3 | 6h | 📋 Future |

**FAPI Use Cases**:
- Financial services applications
- Healthcare applications
- Government services

### 7.2 Multi-Tenant Support

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Tenant extraction (subdomain/header) | P3 | 2h | 📋 Future |
| Tenant-specific configuration | P3 | 3h | 📋 Future |
| Tenant isolation in storage | P3 | 3h | 📋 Future |
| Tenant management API | P3 | 4h | 📋 Future |

### 7.3 API Gateway Integration

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Kong plugin | P3 | 8h | 📋 Future |
| NGINX auth_request module | P3 | 4h | 📋 Future |
| Traefik middleware | P3 | 4h | 📋 Future |
| AWS API Gateway authorizer | P3 | 6h | 📋 Future |

### 7.4 Mobile App Support

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| App-to-web handoff | P3 | 6h | 📋 Future |
| Deep link handling | P3 | 4h | 📋 Future |
| Native app redirect | P3 | 4h | 📋 Future |

---

## Milestones

### v0.1.0 - Initial Release ✅
**Released**: January 2025

- [x] Core session management with `__Host-` cookies
- [x] Token vault with Fernet encryption
- [x] OAuth 2.0/2.1 with PKCE
- [x] Provider configurations (Google, Azure, GitHub)
- [x] Published to PyPI: `pip install bffauth`

### v0.1.1 - Beta Polish ✅
**Released**: January 2025

- [x] Fix deprecated datetime.utcnow() usage
- [x] Update package metadata for PyPI
- [x] Add tests for BFFOAuthHandler (27 tests)
- [x] Add tests for AuthlibBackend (36 tests)
- [x] Add tests for provider configurations (22 tests)
- [x] Create GitHub Actions CI workflow
- [x] Create CHANGELOG.md
- [x] Fix mypy strict mode compliance

### v0.2.0 - Production Essentials (Complete)
**Target Date**: Q1 2025

- [x] Redis session storage backend
- [x] Redis vault storage backend
- [x] Sliding session expiration
- [x] Custom CSRF header validation (X-CSRF-Token)
- [x] OAuth state moved to session storage
- [x] Integration tests with real Redis (15 tests)
- [x] Testing documentation (docs/TESTING.md)
- [x] Back-channel logout endpoint (OIDC Back-Channel Logout 1.0)
- [x] Session lookup by user_id for logout
- [x] ID token hint in RP-Initiated Logout
- [x] Post-logout redirect URI support

### v0.3.0 - API Integration
**Target Date**: Q2 2025

- [ ] API proxy with token injection
- [ ] Silent login
- [ ] OpenTelemetry integration
- [ ] Health endpoints
- [ ] /auth/claims endpoint

### v0.4.0 - Framework Integrations
**Target Date**: Q2 2025

- [ ] FastAPI middleware and router
- [ ] Flask extension
- [ ] Example applications

### v1.0.0 - Production Ready
**Target Date**: Q3 2025

- [ ] Full competitive parity
- [ ] Database storage backend
- [ ] Token refresh coordination
- [ ] Audit logging
- [ ] Documentation complete

### v1.1.0 - Advanced Features
**Target Date**: Q4 2025

- [ ] Financial-grade OIDC (PAR, JARM)
- [ ] Multi-tenant support
- [ ] API gateway integrations

---

## Contributing

We welcome contributions. Priority areas:

1. **Storage backends** - Redis, PostgreSQL, MongoDB
2. **Provider integrations** - GitHub, Okta, Keycloak
3. **Framework integrations** - Django, Starlette
4. **Documentation** - Examples, tutorials

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## Competitive Analysis Summary

### Features Matching Competitors

| Feature | Duende | Curity | BFFAuth |
|---------|--------|--------|---------|
| PKCE | ✅ | ✅ | ✅ |
| __Host- cookies | ✅ | ✅ | ✅ |
| Multi-provider | ✅ | ✅ | ✅ |
| Token encryption | ✅ | ✅ | ✅ |
| Redis storage | ✅ | ✅ | ✅ |
| Sliding sessions | ✅ | ✅ | ✅ |
| CSRF header validation | ✅ | ✅ | ✅ |
| Back-channel logout | ✅ | ✅ | ✅ |
| Silent login | ✅ | ✅ | ⏳ v0.3 |
| API proxy | ✅ | ✅ | ⏳ v0.3 |
| OpenTelemetry | ✅ | ✅ | ⏳ v0.3 |

### BFFAuth Unique Advantages

1. **Python-native** - First-class Python support with Pydantic models
2. **Authlib foundation** - Built on battle-tested OAuth library
3. **Protocol-based** - Fully swappable components via protocols
4. **Open source** - Apache 2.0 license (Duende is commercial)
5. **ADK integration** - Native support for Google ADK agents
