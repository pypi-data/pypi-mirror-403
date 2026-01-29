# BFFAuth

OAuth 2.1 + BFF (Backend-for-Frontend) Authentication Library for Python.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Table of Contents

- [What is the BFF Pattern?](#what-is-the-bff-pattern)
- [Why Use BFF Instead of Standard OAuth?](#why-use-bff-instead-of-standard-oauth)
- [Architecture](#architecture)
- [How BFFAuth Works](#how-bffauth-works)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Supported Providers](#supported-providers)
- [Security Features](#security-features)
- [API Reference](#api-reference)
- [Competitive Analysis](#competitive-analysis)
- [References](#references)

---

## What is the BFF Pattern?

**BFF (Backend-for-Frontend)** is a security architecture pattern for OAuth in browser-based applications. It is the **#1 recommended approach** in the [IETF draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps) specification (currently at version 18, on track to become an RFC).

### The Problem with Traditional SPA OAuth

In traditional Single Page Applications (SPAs), OAuth tokens are stored in the browser:

```
Traditional SPA OAuth (INSECURE for browsers)
═══════════════════════════════════════════════

┌─────────────┐                      ┌──────────────────┐
│   Browser   │◄─────────────────────│  OAuth Provider  │
│   (SPA)     │  Returns tokens      │  (Google, Azure) │
│             │  directly to browser │                  │
└─────────────┘                      └──────────────────┘
      │
      │ Tokens stored in:
      │ • localStorage (persists, vulnerable to XSS)
      │ • sessionStorage (cleared on tab close)
      │ • JavaScript memory (lost on refresh)
      │
      ▼
┌─────────────────────────────────────────────────┐
│  ⚠️  XSS VULNERABILITY                          │
│  Any JavaScript (including malicious scripts)   │
│  can read tokens and send them to attackers     │
└─────────────────────────────────────────────────┘
```

### The BFF Solution

The BFF pattern keeps tokens **server-side only**, using secure cookies for session management:

```
BFF Pattern (IETF Recommended)
══════════════════════════════

┌─────────────┐     Cookie Only      ┌───────────────────────────────────┐
│   Browser   │◄────────────────────►│              BFF Layer            │
│   (SPA)     │  (Secure, HttpOnly,  │                                   │
│             │   SameSite=Strict)   │  ┌─────────────────────────────┐  │
│             │                      │  │     Session Manager         │  │
│  NO tokens  │                      │  │  • Cookie ↔ Session binding │  │
│  in browser │                      │  │  • CSRF token validation    │  │
│             │                      │  └─────────────────────────────┘  │
└─────────────┘                      │               │                   │
                                     │               ▼                   │
                                     │  ┌─────────────────────────────┐  │
                                     │  │      Token Vault            │  │
                                     │  │  • Encrypted at rest        │  │
                                     │  │  • Per-user, per-provider   │  │
                                     │  │  • Auto-refresh             │  │
                                     │  └─────────────────────────────┘  │
                                     │               │                   │
                                     │               ▼                   │
                                     │  ┌─────────────────────────────┐  │
                                     │  │   OAuth Client (Authlib)    │  │
                                     │  │  • PKCE                     │  │
                                     │  │  • Token exchange           │  │
                                     │  └─────────────────────────────┘  │
                                     └───────────────────────────────────┘
                                                     │
                                                     ▼
                                     ┌───────────────────────────────────┐
                                     │    Resource Server Allowlist      │
                                     │  (Only approved APIs receive      │
                                     │   tokens - IETF 6.2.4)            │
                                     └───────────────────────────────────┘
```

---

## Why Use BFF Instead of Standard OAuth?

### Security Comparison

| Aspect | Traditional OAuth | BFF Pattern |
|--------|------------------|-------------|
| **Token Location** | Browser (localStorage/memory) | Server-side only |
| **XSS Vulnerability** | Tokens can be stolen | Tokens never exposed |
| **Session Management** | Token-based | Secure cookie-based |
| **CSRF Protection** | State parameter only | SameSite + CSRF tokens |
| **Token Refresh** | Client-side (complex) | Server-side (transparent) |
| **API Calls** | Browser → API (with token) | Browser → BFF → API |
| **Multi-Provider** | Complex client-side | Simple server-side vault |

### Key Benefits of BFF

1. **XSS Protection**: Even if an attacker injects malicious JavaScript, they cannot steal OAuth tokens because tokens never reach the browser.

2. **Simplified Frontend**: Your SPA doesn't need to manage tokens, refresh logic, or handle OAuth complexity.

3. **Centralized Security**: All security logic (token validation, refresh, allowlist) is in one place on the server.

4. **Multi-Provider Support**: Easily connect multiple OAuth providers (Google, Azure, GitHub) with tokens stored in a unified vault.

5. **Confidential Client**: BFF can use client secrets (unlike browser apps), providing stronger authentication with providers.

### User Experience Comparison

| Aspect | Traditional OAuth | BFF Pattern | User Notices? |
|--------|------------------|-------------|---------------|
| Click "Login" | Same | Same | No |
| Redirect to provider | Same | Same | No |
| Authenticate | Same | Same | No |
| Grant consent | Same | Same | No |
| Redirect back | Same | Same | No |
| Use features | Same | Same | No |

**The user experience is identical** - BFF is a transparent security enhancement.

### Protocol Compatibility

BFF is **fully compatible** with OAuth 2.0/2.1. It doesn't change the OAuth protocol - it changes *where* the OAuth client runs and *how* tokens are handled after issuance.

| Provider | Compatible? | Notes |
|----------|-------------|-------|
| Google | ✅ Yes | No changes needed |
| Azure AD / Entra ID | ✅ Yes | No changes needed |
| GitHub | ✅ Yes | No changes needed |
| Okta | ✅ Yes | No changes needed |
| Auth0 | ✅ Yes | No changes needed |
| Any OAuth 2.0 provider | ✅ Yes | Standard protocol |

---

## Architecture

### BFFAuth Component Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                              BFFAuth Library                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        BFFOAuthHandler                              │  │
│  │  • Orchestrates all components                                      │  │
│  │  • Manages OAuth flows                                              │  │
│  │  • Provides unified API                                             │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│          ┌─────────────────────────┼─────────────────────────┐            │
│          ▼                         ▼                         ▼            │
│  ┌───────────────┐       ┌─────────────────┐       ┌──────────────────┐   │
│  │SessionManager │       │   TokenVault    │       │    Allowlist     │   │
│  ├───────────────┤       ├─────────────────┤       │    Validator     │   │
│  │• __Host-      │       │• Fernet encrypt │       ├──────────────────┤   │
│  │  session      │       │  (AES-128-CBC)  │       │• URL pattern     │   │
│  │  cookies      │       │• Multi-provider │       │  matching        │   │
│  │• CSRF tokens  │       │• Auto-refresh   │       │• Method checks   │   │
│  │• Session      │       │  tracking       │       │• Scope validation│   │
│  │  expiration   │       │                 │       │• Per IETF 6.2.4  │   │
│  └───────────────┘       └─────────────────┘       └──────────────────┘   │
│                                    │                                      │
│                                    ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                     AuthlibBackend                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    Authlib (Dependency)                     │   │   │
│  │  │  • OAuth 2.0/2.1 protocol implementation                    │   │   │
│  │  │  • PKCE (RFC 7636)                                          │   │   │
│  │  │  • Token exchange & refresh                                 │   │   │
│  │  │  • OpenID Connect                                           │   │   │
│  │  │  • 20+ provider configurations                              │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                       Provider Configs                              │  │
│  │  • Google  • Azure AD  • GitHub  • Custom OIDC                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### How BFFAuth Wraps Authlib

BFFAuth is a **wrapper library** that adds BFF security layers on top of [Authlib](https://authlib.org/), the most popular Python OAuth library (5K+ GitHub stars).

```
Why Wrap Authlib Instead of Reimplementing?
════════════════════════════════════════════

┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   BFFAuth (Your Code)                    Authlib (Battle-tested)           │
│   ══════════════════                     ══════════════════════            │
│                                                                            │
│   ┌──────────────────────┐               ┌──────────────────────┐          │
│   │  BFF Security Layer  │               │  OAuth Protocol      │          │
│   │  ────────────────────│               │  ────────────────────│          │
│   │  • Session cookies   │    wraps      │  • Auth code flow    │          │
│   │  • Token encryption  │◄─────────────►│  • PKCE (RFC 7636)   │          │
│   │  • CSRF protection   │               │  • Token refresh     │          │
│   │  • Allowlist         │               │  • OIDC support      │          │
│   │  (UNIQUE VALUE)      │               │  • 20+ providers     │          │
│   └──────────────────────┘               │  (5K+ stars, tested) │          │
│                                          └──────────────────────┘          │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

Benefits:
✅ Battle-tested OAuth core (Authlib)
✅ Unique BFF security layer (BFFAuth)
✅ Rich feature set (OIDC, introspection, 20+ providers)
✅ Community trust and security audits
✅ Focused scope - we only maintain BFF logic
```

---

## OAuth Flows with BFF

### Flow A: User Login (SSO)

```
User Login Flow
═══════════════

┌─────────┐      ┌─────────────┐      ┌───────────────┐      ┌──────────┐
│ Browser │      │     BFF     │      │    BFFAuth    │      │ Provider │
│  (SPA)  │      │   (Your     │      │    Library    │      │ (Google) │
│         │      │   Server)   │      │               │      │          │
└────┬────┘      └──────┬──────┘      └───────┬───────┘      └────┬─────┘
     │                  │                     │                    │
     │ 1. GET /login    │                     │                    │
     │─────────────────►│                     │                    │
     │                  │                     │                    │
     │                  │ 2. start_authorization()                 │
     │                  │────────────────────►│                    │
     │                  │                     │                    │
     │                  │ 3. Create session,  │                    │
     │                  │    store PKCE       │                    │
     │                  │◄────────────────────│                    │
     │                  │    Return auth_url  │                    │
     │                  │                     │                    │
     │ 4. Redirect to   │                     │                    │
     │    auth_url      │                     │                    │
     │◄─────────────────│                     │                    │
     │                  │                     │                    │
     │ 5. User authenticates at provider      │                    │
     │────────────────────────────────────────────────────────────►│
     │                  │                     │                    │
     │ 6. Redirect with code + state          │                    │
     │◄────────────────────────────────────────────────────────────│
     │                  │                     │                    │
     │ 7. GET /callback?code=...&state=...    │                    │
     │─────────────────►│                     │                    │
     │                  │                     │                    │
     │                  │ 8. handle_callback()│                    │
     │                  │────────────────────►│                    │
     │                  │                     │ 9. Exchange code   │
     │                  │                     │    for tokens      │
     │                  │                     │───────────────────►│
     │                  │                     │◄───────────────────│
     │                  │                     │                    │
     │                  │ 10. Tokens stored   │                    │
     │                  │     in encrypted    │                    │
     │                  │     vault           │                    │
     │                  │◄────────────────────│                    │
     │                  │                     │                    │
     │ 11. Set-Cookie:  │                     │                    │
     │     __Host-session=...                 │                    │
     │     (Secure, HttpOnly, SameSite=Strict)│                    │
     │◄─────────────────│                     │                    │
     │                  │                     │                    │
     │  ✅ User logged in                     │                    │
     │  ✅ NO tokens in browser               │                    │
     │                  │                     │                    │
```

### Flow B: API Request (Token Injection)

```
API Request Flow (Browser → BFF → Resource Server)
══════════════════════════════════════════════════

┌─────────┐      ┌─────────────┐      ┌───────────────┐      ┌──────────┐
│ Browser │      │     BFF     │      │    BFFAuth    │      │   API    │
│  (SPA)  │      │   (Your     │      │    Library    │      │ (Google) │
│         │      │   Server)   │      │               │      │          │
└────┬────┘      └──────┬──────┘      └───────┬───────┘      └────┬─────┘
     │                  │                     │                    │
     │ 1. POST /api/search                    │                    │
     │    Cookie: __Host-session=...          │                    │
     │    Body: { query: "..." }              │                    │
     │─────────────────►│                     │                    │
     │                  │                     │                    │
     │                  │ 2. get_access_token()                    │
     │                  │────────────────────►│                    │
     │                  │                     │                    │
     │                  │ 3. Validate session │                    │
     │                  │    Decrypt token    │                    │
     │                  │    Auto-refresh if  │                    │
     │                  │    needed           │                    │
     │                  │◄────────────────────│                    │
     │                  │    Return token     │                    │
     │                  │                     │                    │
     │                  │ 4. Validate URL against allowlist        │
     │                  │                     │                    │
     │                  │ 5. Call API with token                   │
     │                  │    Authorization: Bearer <token>         │
     │                  │─────────────────────────────────────────►│
     │                  │◄─────────────────────────────────────────│
     │                  │                     │                    │
     │ 6. Return results│                     │                    │
     │    (NO token     │                     │                    │
     │     exposed)     │                     │                    │
     │◄─────────────────│                     │                    │
     │                  │                     │                    │
```

---

## Installation

```bash
pip install bffauth
```

With optional dependencies:

```bash
pip install bffauth[redis]    # Redis storage backend
pip install bffauth[fastapi]  # FastAPI integration (planned)
pip install bffauth[flask]    # Flask integration (planned)
pip install bffauth[all]      # All optional dependencies
```

## Quick Start

```python
from bffauth import BFFOAuthHandler, OAuthProvider
from bffauth.providers import create_google_config
from cryptography.fernet import Fernet

# Generate encryption key (store securely in production!)
encryption_key = Fernet.generate_key().decode()

# Create handler
handler = BFFOAuthHandler(
    encryption_key=encryption_key,
    redirect_base_uri="https://app.example.com",
)

# Register OAuth provider
handler.register_provider(create_google_config(
    client_id="your-google-client-id",
    client_secret="your-google-client-secret",
))

# Start OAuth flow
async def login():
    auth_url, session = await handler.start_authorization(OAuthProvider.GOOGLE)
    # Redirect user to auth_url
    # Set session cookie with session.session_id
    return auth_url, session

# Handle callback
async def callback(session_id: str, code: str, state: str):
    result = await handler.handle_callback(
        session_id=session_id,
        code=code,
        state=state,
    )
    # User is now authenticated
    return result.id_token_claims

# Get token for API calls (server-side only!)
async def call_api(session_id: str):
    token = await handler.get_access_token(session_id, OAuthProvider.GOOGLE)
    # Use token to call Google APIs - token NEVER sent to browser
    return token
```

## Supported Providers

### Google

```python
from bffauth.providers import create_google_config, GOOGLE_SCOPES

config = create_google_config(
    client_id="...",
    client_secret="...",
    scope=f"openid email {GOOGLE_SCOPES['calendar_readonly']}",
)
```

### Microsoft Azure AD / Entra ID

```python
from bffauth.providers import create_azure_config, AZURE_SCOPES

# Multi-tenant
config = create_azure_config(
    client_id="...",
    client_secret="...",
    tenant_id="common",
    scope=f"openid email {AZURE_SCOPES['user_read']}",
)

# Single-tenant
config = create_azure_config(
    client_id="...",
    client_secret="...",
    tenant_id="your-tenant-id",
)
```

### GitHub

```python
from bffauth.providers import create_github_config, GITHUB_SCOPES

config = create_github_config(
    client_id="...",
    client_secret="...",
    scope=f"{GITHUB_SCOPES['user_read']} {GITHUB_SCOPES['repo']}",
)
```

### Custom OIDC Provider

```python
from bffauth.providers import create_custom_config

config = create_custom_config(
    client_id="...",
    client_secret="...",
    authorization_endpoint="https://idp.example.com/authorize",
    token_endpoint="https://idp.example.com/token",
    userinfo_endpoint="https://idp.example.com/userinfo",
)

# Or auto-discover from OIDC metadata
from bffauth.providers import create_oidc_config_from_discovery_async

config = await create_oidc_config_from_discovery_async(
    client_id="...",
    client_secret="...",
    discovery_url="https://idp.example.com/.well-known/openid-configuration",
)
```

## Security Features

### Resource Server Allowlist (IETF 6.2.4)

Per IETF security requirements, BFF must validate that tokens are only sent to approved APIs:

```python
from bffauth import AllowlistValidator, AllowedResource, OAuthProvider

allowlist = AllowlistValidator([
    AllowedResource(
        name="google_apis",
        url_pattern=r"^https://.*\.googleapis\.com/.*$",
        provider=OAuthProvider.GOOGLE,
    ),
    AllowedResource(
        name="internal_api",
        url_pattern=r"^https://api\.example\.com/.*$",
        allowed_methods=["GET", "POST"],
    ),
])

handler = BFFOAuthHandler(
    encryption_key=key,
    allowlist=allowlist,
)
```

### Cookie Security

BFFAuth uses `__Host-` prefixed cookies by default:

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `HttpOnly` | true | Not accessible to JavaScript |
| `Secure` | true | Only sent over HTTPS |
| `SameSite` | Strict | CSRF protection |
| `Path` | `/` | Required for `__Host-` prefix |

### Token Encryption

Tokens are encrypted at rest using **Fernet** (AES-128-CBC + HMAC-SHA256):

```python
from cryptography.fernet import Fernet

# Generate key once, store in secrets manager
key = Fernet.generate_key()
# NEVER commit to version control
```

### CSRF Protection

Every session includes a CSRF token for form submissions:

```python
# Get CSRF token for forms
session = await handler.get_session(session_id)
csrf_token = session.csrf_token

# Validate on form submission
await handler.validate_csrf(session_id, submitted_token)
```

## Production Storage

Default in-memory storage is for development only. For production, use the built-in Redis storage:

```bash
pip install bffauth[redis]
```

```python
import redis.asyncio as redis
from bffauth import BFFOAuthHandler
from bffauth.storage import RedisSessionStorage, RedisVaultStorage

# Create Redis client
redis_client = redis.Redis.from_url("redis://localhost:6379/0")

# Use built-in Redis storage
handler = BFFOAuthHandler(
    encryption_key=key,
    session_storage=RedisSessionStorage(redis_client),
    token_storage=RedisVaultStorage(redis_client),
)
```

Redis storage features:
- Automatic TTL-based expiration aligned with session lifetimes
- Sliding session expiration support
- Custom key prefixes for multi-tenant deployments
- Session lookup by user_id for back-channel logout

For custom storage backends, implement the storage protocols:

```python
from bffauth import SessionStorageProtocol, VaultStorageProtocol

class CustomSessionStorage(SessionStorageProtocol):
    async def get(self, session_id: str) -> Optional[SessionData]: ...
    async def set(self, session: SessionData) -> None: ...
    async def delete(self, session_id: str) -> bool: ...
    async def find_by_user_id(self, user_id: str) -> list[SessionData]: ...
```

## API Reference

### BFFOAuthHandler

Main handler class for BFF authentication.

| Method | Description |
|--------|-------------|
| `register_provider(config)` | Register OAuth provider |
| `start_authorization(provider)` | Start OAuth flow, returns (url, session) |
| `handle_callback(session_id, code, state)` | Handle OAuth callback |
| `get_access_token(session_id, provider)` | Get valid access token |
| `logout(session_id, provider?)` | Logout user (local) |
| `get_logout_url(session_id, provider)` | Get IdP logout URL (RP-Initiated Logout) |
| `handle_backchannel_logout(logout_token)` | Process IdP back-channel logout |
| `get_session(session_id)` | Get session data |
| `refresh_session(session_id)` | Extend session (sliding expiration) |
| `validate_csrf(session_id, token)` | Validate CSRF token (form) |
| `validate_csrf_header(session_id, header)` | Validate CSRF header (API) |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `BFFAuthError` | Base exception for all BFFAuth errors |
| `AuthorizationError` | OAuth authorization failed |
| `TokenNotFoundError` | No token for provider |
| `TokenExpiredError` | Token expired, refresh needed |
| `SessionNotFoundError` | Session not found or expired |
| `CSRFValidationError` | CSRF token mismatch |
| `ResourceNotAllowedError` | URL not in allowlist |
| `LogoutTokenError` | Back-channel logout token invalid |
| `StateValidationError` | OAuth state parameter mismatch |

## Competitive Analysis

### Feature Comparison

BFFAuth provides feature parity with commercial and open-source BFF implementations:

| Feature | BFFAuth | Duende BFF | Curity | michaelvl |
|---------|---------|------------|--------|-----------|
| **Core OAuth** |
| OAuth 2.0/2.1 | ✅ | ✅ | ✅ | ✅ |
| PKCE (SHA256) | ✅ | ✅ | ✅ | ✅ |
| Multi-provider | ✅ | ✅ | ✅ | ❌ |
| Token refresh | ✅ | ✅ | ✅ | ✅ |
| **Session Security** |
| `__Host-` cookies | ✅ | ✅ | ✅ | ✅ |
| HttpOnly, Secure | ✅ | ✅ | ✅ | ✅ |
| SameSite | ✅ | ✅ | ✅ | ✅ |
| CSRF protection | ✅ | ✅ | ✅ | ✅ |
| **Token Security** |
| Encrypted at rest | ✅ | ✅ | ✅ | ❌ |
| Allowlist validation | ✅ | ✅ | ✅ | ❌ |
| Token rotation | ✅ | ✅ | ✅ | ❌ |
| **Advanced** |
| Back-channel logout | ✅ | ✅ | ✅ | ❌ |
| RP-Initiated logout | ✅ | ✅ | ✅ | ❌ |
| Sliding sessions | ✅ | ✅ | ✅ | ❌ |
| Redis storage | ✅ | ✅ | ✅ | ❌ |
| Silent login | ⏳ | ✅ | ✅ | ❌ |
| API proxy | ⏳ | ✅ | ✅ | ❌ |
| OpenTelemetry | ⏳ | ✅ | ✅ | ❌ |
| Financial-grade (FAPI) | ⏳ | ❌ | ✅ | ❌ |

### BFFAuth Advantages

| Advantage | Description |
|-----------|-------------|
| **Python-native** | First-class Python support with async/await, type hints, and Pydantic models |
| **Authlib foundation** | Built on battle-tested OAuth library (5K+ GitHub stars) |
| **Protocol-based** | Fully swappable components via Python Protocols |
| **Open source** | Apache 2.0 license (Duende is commercial) |
| **Framework agnostic** | Works with FastAPI, Flask, Django, or any ASGI/WSGI framework |
| **ADK integration** | Native support for Google Agent Development Kit |

### Release History

| Version | Status | Key Features |
|---------|--------|--------------|
| **v0.1.0** | ✅ Released | Core OAuth 2.1, PKCE, session management, token vault |
| **v0.2.0** | ✅ Released | Back-channel logout, RP-Initiated logout, Redis storage, sliding sessions, CSRF headers |
| **v0.2.1** | ✅ Released | Documentation updates, release process improvements |

### Planned Features (Roadmap)

Features planned for upcoming releases:

- **v0.3.0**: API proxy, silent login, OpenTelemetry
- **v1.0.0**: Full production hardening, database storage
- **v1.1.0**: Financial-grade OIDC (PAR, JARM, mTLS)

See [ROADMAP.md](docs/ROADMAP.md) for detailed timeline.

---

## References

### IETF Standards

- **[IETF draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps)** - OAuth 2.0 for Browser-Based Applications (BFF is the #1 recommended pattern, Section 6.2)
- **[RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636)** - Proof Key for Code Exchange (PKCE)
- **[RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)** - OAuth 2.0 Authorization Framework

### Dependencies

- **[Authlib](https://authlib.org/)** - The OAuth library powering BFFAuth's OAuth backend
- **[Cryptography](https://cryptography.io/)** - Fernet encryption for token storage
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation and models

### Related Projects

| Project | Language | License | Description |
|---------|----------|---------|-------------|
| [Duende BFF](https://docs.duendesoftware.com/bff/) | .NET | Commercial | Full-featured BFF for ASP.NET |
| [Curity Token Handler](https://curity.io/resources/learn/the-token-handler-pattern/) | Various | Commercial | Financial-grade OAuth proxy |
| [michaelvl/oidc-oauth2-bff](https://github.com/michaelvl/oidc-oauth2-bff) | Go | MIT | Lightweight OIDC BFF |
| [FusionAuth](https://fusionauth.io/) | Various | Commercial | Identity platform with BFF support |

BFFAuth is the **first open-source Python library** implementing the complete BFF pattern per IETF specifications.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
