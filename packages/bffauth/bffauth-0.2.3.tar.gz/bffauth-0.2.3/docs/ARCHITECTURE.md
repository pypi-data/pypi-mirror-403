# BFFAuth Architecture

## Overview

BFFAuth implements the Backend-for-Frontend (BFF) pattern for OAuth 2.0/2.1, providing a secure server-side component that handles all OAuth operations on behalf of browser-based applications.

---

## 1. System Context

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              External Systems                               │
│                                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Google    │  │   Azure AD   │  │    Okta      │  │   Custom     │  │
│  │    OAuth     │  │    OIDC      │  │    OIDC      │  │    OIDC      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│          ▲                ▲                ▲                ▲              │
└──────────┼────────────────┼────────────────┼────────────────┼──────────────┘
           │                │                │                │
           │    OAuth 2.0 Authorization Code + PKCE           │
           │                │                │                │
┌──────────┼────────────────┼────────────────┼────────────────┼──────────────┐
│          │                │                │                │              │
│          ▼                ▼                ▼                ▼              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                           BFFAuth                                    │  │
│  │                                                                      │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │
│  │  │ Session  │  │  Token   │  │  OAuth   │  │   API    │            │  │
│  │  │ Manager  │  │  Vault   │  │ Handler  │  │  Proxy   │            │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │  │
│  │                                                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│          ▲                                              │                  │
│          │ __Host-session cookie                       │ Bearer Token     │
│          │ (HttpOnly, Secure, SameSite)                ▼                  │
│  ┌─────────────────────────────┐            ┌─────────────────────────┐  │
│  │        Browser/SPA          │            │      Backend APIs       │  │
│  │  (No token access)          │            │  (Resource Servers)     │  │
│  └─────────────────────────────┘            └─────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BFFAuth Core                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Public API Layer                              │   │
│  │                                                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │  /login  │  │/callback │  │ /logout  │  │ /userinfo│            │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │   │
│  │       │             │             │             │                   │   │
│  └───────┼─────────────┼─────────────┼─────────────┼───────────────────┘   │
│          │             │             │             │                        │
│          ▼             ▼             ▼             ▼                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Core Components                               │   │
│  │                                                                      │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │   │
│  │  │                 │    │                 │    │                 │ │   │
│  │  │  SessionManager │◀──▶│   TokenVault    │◀──▶│  OAuthHandler   │ │   │
│  │  │                 │    │                 │    │                 │ │   │
│  │  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘ │   │
│  │           │                      │                      │          │   │
│  │           │    ┌─────────────────┼──────────────────┐  │          │   │
│  │           │    │                 │                  │  │          │   │
│  │           ▼    ▼                 ▼                  ▼  ▼          │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │   │
│  │  │                 │    │                 │    │                 │ │   │
│  │  │ AllowlistValid. │    │   Encryption    │    │  ProviderConfig │ │   │
│  │  │                 │    │   (Fernet)      │    │                 │ │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘ │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│          │                      │                                           │
│          ▼                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Storage Layer                                 │   │
│  │                                                                      │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │   │
│  │  │   InMemory      │    │     Redis       │    │    Database     │ │   │
│  │  │   (Default)     │    │   (Production)  │    │   (Production)  │ │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘ │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility | Key Operations |
|-----------|---------------|----------------|
| **SessionManager** | Session lifecycle | create, get, update, delete, validate_csrf |
| **TokenVault** | Encrypted token storage | store, get, update, delete, refresh |
| **OAuthHandler** | OAuth flow orchestration | login, callback, logout, userinfo |
| **AllowlistValidator** | API destination validation | validate_url, get_provider |
| **Encryption** | Token encryption/decryption | encrypt, decrypt (Fernet) |
| **ProviderConfig** | Provider settings | OIDC discovery, endpoints |

---

## 3. Data Flow Architecture

### 3.1 Login Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Browser │     │  BFFAuth │     │ Session  │     │  OAuth   │     │   IdP    │
│          │     │  Server  │     │ Manager  │     │ Handler  │     │ (Google) │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │  GET /login    │                │                │                │
     │───────────────▶│                │                │                │
     │                │                │                │                │
     │                │ create_session │                │                │
     │                │───────────────▶│                │                │
     │                │                │                │                │
     │                │    session     │                │                │
     │                │◀───────────────│                │                │
     │                │                │                │                │
     │                │        generate_auth_url        │                │
     │                │───────────────────────────────▶│                │
     │                │                │                │                │
     │                │      auth_url (with PKCE)      │                │
     │                │◀───────────────────────────────│                │
     │                │                │                │                │
     │  302 Redirect  │                │                │                │
     │  Set-Cookie    │                │                │                │
     │◀───────────────│                │                │                │
     │                │                │                │                │
     │                        GET /authorize            │                │
     │─────────────────────────────────────────────────────────────────▶│
     │                │                │                │                │
```

### 3.2 Callback Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Browser │     │  BFFAuth │     │  OAuth   │     │  Token   │     │   IdP    │
│          │     │  Server  │     │ Handler  │     │  Vault   │     │ (Google) │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ GET /callback  │                │                │                │
     │ ?code=xxx      │                │                │                │
     │───────────────▶│                │                │                │
     │                │                │                │                │
     │                │ validate_state │                │                │
     │                │───────────────▶│                │                │
     │                │                │                │                │
     │                │                │    POST /token (code+PKCE)      │
     │                │                │───────────────────────────────▶│
     │                │                │                │                │
     │                │                │         tokens                  │
     │                │                │◀───────────────────────────────│
     │                │                │                │                │
     │                │                │  store_token   │                │
     │                │                │───────────────▶│                │
     │                │                │                │                │
     │                │                │   (encrypted)  │                │
     │                │                │◀───────────────│                │
     │                │                │                │                │
     │  302 Redirect  │                │                │                │
     │  to app        │                │                │                │
     │◀───────────────│                │                │                │
     │                │                │                │                │
```

### 3.3 API Proxy Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Browser │     │  BFFAuth │     │ Allowlist│     │  Token   │     │ Backend  │
│          │     │  Proxy   │     │ Validator│     │  Vault   │     │   API    │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ GET /api/users │                │                │                │
     │ Cookie: sess   │                │                │                │
     │───────────────▶│                │                │                │
     │                │                │                │                │
     │                │ validate_url   │                │                │
     │                │───────────────▶│                │                │
     │                │                │                │                │
     │                │   provider     │                │                │
     │                │◀───────────────│                │                │
     │                │                │                │                │
     │                │       get_valid_token           │                │
     │                │───────────────────────────────▶│                │
     │                │                │                │                │
     │                │           token                │                │
     │                │◀───────────────────────────────│                │
     │                │                │                │                │
     │                │         GET /users             │                │
     │                │         Authorization: Bearer  │                │
     │                │───────────────────────────────────────────────▶│
     │                │                │                │                │
     │                │              response          │                │
     │                │◀───────────────────────────────────────────────│
     │                │                │                │                │
     │    response    │                │                │                │
     │◀───────────────│                │                │                │
     │                │                │                │                │
```

---

## 4. Security Architecture

### 4.1 Defense Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Defense in Depth                                  │
│                                                                             │
│  Layer 1: Transport Security                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • HTTPS only (TLS 1.2+)                                              │ │
│  │  • HSTS headers                                                        │ │
│  │  • Certificate validation                                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Layer 2: Cookie Security                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • __Host- prefix (prevents cookie tossing)                           │ │
│  │  • Secure flag (HTTPS only)                                           │ │
│  │  • HttpOnly flag (no JavaScript access)                               │ │
│  │  • SameSite=Strict (CSRF protection)                                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Layer 3: CSRF Protection                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • SameSite cookie (primary)                                          │ │
│  │  • CSRF token per session (secondary)                                 │ │
│  │  • Custom header requirement (X-CSRF-Token)                           │ │
│  │  • Constant-time comparison                                            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Layer 4: Token Security                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Tokens never sent to browser                                        │ │
│  │  • Fernet encryption at rest (AES-128-CBC + HMAC-SHA256)              │ │
│  │  • Session-bound token storage                                         │ │
│  │  • Allowlist validation for token injection                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Layer 5: OAuth Security                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • PKCE required (SHA256)                                              │ │
│  │  • State parameter for CSRF                                            │ │
│  │  • Nonce for replay protection                                         │ │
│  │  • Exact redirect URI matching                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Token Flow Security

```
                     ┌─────────────────────────────────────────┐
                     │           SECURITY BOUNDARY              │
                     │                                         │
┌──────────┐         │  ┌──────────────────────────────────┐  │         ┌──────────┐
│          │  Cookie │  │                                  │  │ Bearer  │          │
│ Browser  │◀───────▶│  │          BFFAuth Server          │  │◀───────▶│   API    │
│          │  only   │  │                                  │  │  Token  │          │
└──────────┘         │  └──────────────────────────────────┘  │         └──────────┘
                     │         │                   ▲          │
     NO TOKENS       │         │  store            │  get     │     TOKENS
     CROSS THIS      │         ▼                   │          │     INJECTED
     BOUNDARY        │  ┌──────────────────────────────────┐  │     HERE
                     │  │         Token Vault               │  │
                     │  │    (Fernet Encrypted Storage)     │  │
                     │  └──────────────────────────────────┘  │
                     │                                         │
                     └─────────────────────────────────────────┘
```

### 4.3 Session Security Model

```python
# Security properties enforced by SessionData model

class SessionData(BaseModel):
    # Cryptographically secure identifiers
    session_id: str = Field(min_length=32)  # 256-bit minimum
    csrf_token: str = Field(min_length=32)  # 256-bit minimum

    # Temporal controls
    created_at: datetime
    expires_at: datetime
    last_activity: datetime

    # Binding
    user_id: Optional[str]  # Links session to user
    user_agent_hash: Optional[str]  # Optional browser binding

    def is_expired(self) -> bool:
        return utc_now() >= self.expires_at
```

---

## 5. Deployment Architecture

### 5.1 Single Instance (Development)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Development Setup                                │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                       Python Process                              │  │
│  │                                                                   │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │  │
│  │  │   BFFAuth   │    │   FastAPI   │    │  InMemory Storage   │  │  │
│  │  │   Core      │◀──▶│   Server    │    │  (Sessions+Tokens)  │  │  │
│  │  └─────────────┘    └─────────────┘    └─────────────────────┘  │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Note: InMemory storage loses data on restart                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Multi-Instance (Production)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Production Setup                                    │
│                                                                             │
│                        ┌──────────────────┐                                 │
│                        │   Load Balancer  │                                 │
│                        │  (sticky not     │                                 │
│                        │   required)      │                                 │
│                        └────────┬─────────┘                                 │
│                                 │                                           │
│              ┌──────────────────┼──────────────────┐                        │
│              │                  │                  │                        │
│              ▼                  ▼                  ▼                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│  │   Instance 1    │ │   Instance 2    │ │   Instance 3    │               │
│  │                 │ │                 │ │                 │               │
│  │  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │               │
│  │  │  BFFAuth  │  │ │  │  BFFAuth  │  │ │  │  BFFAuth  │  │               │
│  │  └─────┬─────┘  │ │  └─────┬─────┘  │ │  └─────┬─────┘  │               │
│  └────────┼────────┘ └────────┼────────┘ └────────┼────────┘               │
│           │                   │                   │                        │
│           └───────────────────┼───────────────────┘                        │
│                               │                                             │
│                               ▼                                             │
│                 ┌─────────────────────────────┐                             │
│                 │       Redis Cluster         │                             │
│                 │                             │                             │
│                 │  • Session Storage          │                             │
│                 │  • Token Vault Storage      │                             │
│                 │  • Automatic TTL            │                             │
│                 │  • High Availability        │                             │
│                 │                             │                             │
│                 └─────────────────────────────┘                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Kubernetes Deployment

```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bffauth
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bffauth
  template:
    metadata:
      labels:
        app: bffauth
    spec:
      containers:
      - name: bffauth
        image: myregistry/bffauth:latest
        ports:
        - containerPort: 8080
        env:
        - name: BFFAUTH_ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: bffauth-secrets
              key: encryption-key
        - name: BFFAUTH_STORAGE_BACKEND
          value: "redis"
        - name: BFFAUTH_REDIS_URL
          valueFrom:
            secretKeyRef:
              name: bffauth-secrets
              key: redis-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
```

---

## 6. Integration Patterns

### 6.1 FastAPI Integration

```python
from fastapi import FastAPI, Depends, Request, Response
from bffauth import BFFAuth, SessionManager, TokenVault
from bffauth.fastapi import BFFAuthMiddleware, get_session

app = FastAPI()

# Configure BFFAuth
bff = BFFAuth(
    encryption_key=os.environ["BFFAUTH_ENCRYPTION_KEY"],
    providers={
        "google": GoogleOAuthConfig(...),
        "azure": AzureOAuthConfig(...),
    },
)

# Add middleware
app.add_middleware(BFFAuthMiddleware, bff=bff)


@app.get("/api/protected")
async def protected_route(
    session: SessionData = Depends(get_session),
):
    """Route that requires valid session."""
    return {"user": session.user_info}


@app.get("/api/google-data")
async def google_data(
    request: Request,
    session: SessionData = Depends(get_session),
):
    """Route that needs Google API access."""
    # BFFAuth automatically injects token
    response = await bff.proxy(
        request,
        target="https://www.googleapis.com/oauth2/v1/userinfo",
        provider="google",
    )
    return response.json()
```

### 6.2 Flask Integration

```python
from flask import Flask
from bffauth.flask import BFFAuthExtension

app = Flask(__name__)
bff = BFFAuthExtension(app)


@app.route("/api/protected")
@bff.require_session
def protected_route():
    """Route that requires valid session."""
    return {"user": bff.current_session.user_info}
```

---

## 7. Extensibility Points

### 7.1 Storage Backend Protocol

```python
class StorageBackendProtocol(Protocol):
    """
    Implement this protocol for custom storage backends.

    Built-in implementations:
    - InMemoryStorage (development)
    - RedisStorage (production)
    - SQLAlchemyStorage (production)
    """

    async def get(self, key: str) -> Optional[bytes]: ...
    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> None: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
```

### 7.2 Provider Protocol

```python
class OAuthProviderProtocol(Protocol):
    """
    Implement this protocol for custom OAuth providers.

    Built-in implementations:
    - GoogleOAuthProvider
    - AzureOAuthProvider
    - GenericOIDCProvider
    """

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        code_challenge: str,
        scope: list[str],
    ) -> str: ...

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> TokenResponse: ...

    async def refresh_tokens(
        self,
        refresh_token: str,
    ) -> TokenResponse: ...
```

---

## 8. Observability Architecture (Planned)

### 8.1 Metrics

```
bffauth_sessions_active           # Gauge: active sessions
bffauth_sessions_created_total    # Counter: total sessions created
bffauth_sessions_expired_total    # Counter: total sessions expired

bffauth_tokens_stored_total       # Counter: tokens stored
bffauth_tokens_refreshed_total    # Counter: token refresh operations
bffauth_tokens_refresh_failed     # Counter: failed refresh attempts

bffauth_oauth_logins_total        # Counter: OAuth login initiations
bffauth_oauth_callbacks_total     # Counter: OAuth callbacks processed
bffauth_oauth_errors_total        # Counter: OAuth errors by type

bffauth_proxy_requests_total      # Counter: proxied API requests
bffauth_proxy_duration_seconds    # Histogram: proxy request duration
```

### 8.2 Tracing

```
bffauth.login
├── bffauth.session.create
├── bffauth.oauth.generate_url
└── bffauth.cookie.set

bffauth.callback
├── bffauth.oauth.validate_state
├── bffauth.oauth.exchange_code
├── bffauth.vault.store_token
└── bffauth.session.update

bffauth.proxy
├── bffauth.session.validate
├── bffauth.allowlist.check
├── bffauth.vault.get_token
├── bffauth.token.refresh (conditional)
└── bffauth.http.request
```

---

## 9. Future Architecture Considerations

### 9.1 Financial-Grade Security (PAR, JARM, mTLS)

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Financial-Grade OAuth (FAPI)                         │
│                                                                        │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐            │
│  │   Browser   │      │   BFFAuth   │      │     IdP     │            │
│  └──────┬──────┘      └──────┬──────┘      └──────┬──────┘            │
│         │                    │                    │                    │
│         │  1. Login request  │                    │                    │
│         │───────────────────▶│                    │                    │
│         │                    │                    │                    │
│         │                    │  2. PAR (mTLS)     │                    │
│         │                    │───────────────────▶│                    │
│         │                    │                    │                    │
│         │                    │  request_uri       │                    │
│         │                    │◀───────────────────│                    │
│         │                    │                    │                    │
│         │  3. Redirect       │                    │                    │
│         │◀───────────────────│                    │                    │
│         │                    │                    │                    │
│         │  4. Authorize (request_uri)            │                    │
│         │───────────────────────────────────────▶│                    │
│         │                    │                    │                    │
│         │  5. JARM response (signed JWT)         │                    │
│         │◀───────────────────────────────────────│                    │
│         │                    │                    │                    │
│                                                                        │
│  Security enhancements:                                                │
│  • PAR: Pre-registers auth request, prevents parameter tampering       │
│  • JARM: Signed authorization response, prevents code injection        │
│  • mTLS: Client certificate auth, prevents client impersonation        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Multi-Tenant Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Multi-Tenant BFFAuth                              │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      Tenant Router                                  │ │
│  │  • Extract tenant from subdomain/header                            │ │
│  │  • Load tenant-specific configuration                              │ │
│  │  • Isolate sessions and tokens per tenant                          │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│         │                    │                    │                     │
│         ▼                    ▼                    ▼                     │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐            │
│  │  Tenant A   │      │  Tenant B   │      │  Tenant C   │            │
│  │  Config     │      │  Config     │      │  Config     │            │
│  │             │      │             │      │             │            │
│  │  Providers: │      │  Providers: │      │  Providers: │            │
│  │  - Google   │      │  - Azure    │      │  - Okta     │            │
│  │  - GitHub   │      │  - Google   │      │  - Custom   │            │
│  └─────────────┘      └─────────────┘      └─────────────┘            │
│                                                                         │
│  Storage key structure:                                                 │
│  • Session: bffauth:{tenant}:session:{session_id}                      │
│  • Vault: bffauth:{tenant}:vault:{session_id}                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. References

- [IETF draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps)
- [RFC 6749 - OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 - PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OIDC Back-Channel Logout](https://openid.net/specs/openid-connect-backchannel-1_0.html)
- [FAPI Security Profile](https://openid.net/specs/openid-financial-api-part-2-1_0.html)
