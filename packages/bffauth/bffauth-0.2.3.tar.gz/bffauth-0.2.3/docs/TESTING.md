# BFFAuth Testing Guide

This document describes the testing strategy, test organization, and how to run tests for BFFAuth.

## Test Summary

| Category | Count | Description |
|----------|-------|-------------|
| Unit Tests | 180 | Fast, isolated tests using mocks |
| Integration Tests | 15 | Tests against real Redis server |
| **Total** | **195** | All tests |

## Test Organization

```
tests/
├── unit/                      # Fast, isolated unit tests (no external dependencies)
│   ├── test_session.py        # SessionManager and InMemorySessionStorage
│   ├── test_vault.py          # TokenVault and InMemoryVaultStorage
│   ├── test_models.py         # Pydantic models and validation
│   ├── test_handler.py        # BFFOAuthHandler
│   ├── test_backend.py        # AuthlibBackend and PKCEGenerator
│   ├── test_providers.py      # Provider configurations (Google, Azure, GitHub)
│   ├── test_redis_storage.py  # Redis storage with mock client
│   └── test_allowlist.py      # AllowlistValidator
├── integration/               # Tests requiring external services
│   ├── conftest.py            # Redis fixtures and skip markers
│   └── test_redis_integration.py  # Real Redis server tests
└── conftest.py                # Shared fixtures
```

## Running Tests

### Prerequisites

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dev dependencies
pip install -e ".[dev]"
```

### Unit Tests (No External Dependencies)

Unit tests use mocks and run without any external services:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_session.py -v

# Run with coverage
pytest tests/unit/ --cov=bffauth --cov-report=html
```

### Integration Tests (Requires Redis)

Integration tests validate behavior against a real Redis server:

```bash
# Start Redis container
docker run -d --name bffauth-redis -p 6379:6379 redis:7-alpine

# Run integration tests
pytest tests/integration/ -v

# Stop Redis when done
docker stop bffauth-redis && docker rm bffauth-redis
```

If Redis is not available, integration tests are automatically skipped.

### Full Test Suite

```bash
# Run everything
pytest tests/ -v

# With coverage report
pytest tests/ --cov=bffauth --cov-report=html --cov-report=term-missing
```

## Test Categories

### Session Management Tests (`test_session.py`)

| Test | Description |
|------|-------------|
| `test_create_session` | Validates session creation with proper IDs and timestamps |
| `test_get_session` | Retrieves session by ID |
| `test_get_session_not_found` | Raises `SessionNotFoundError` for unknown sessions |
| `test_delete_session` | Removes session from storage |
| `test_validate_csrf_success` | Validates correct CSRF token |
| `test_validate_csrf_failure` | Raises `CSRFValidationError` for invalid token |
| `test_rotate_csrf_token` | Generates new CSRF token for session |
| `test_refresh_session` | Extends session expiration (sliding expiration) |
| `test_cookie_options` | Returns correct cookie configuration |
| `test_host_cookie_validation` | Enforces `__Host-` prefix requirements |

### Token Vault Tests (`test_vault.py`)

| Test | Description |
|------|-------------|
| `test_invalid_encryption_key` | Raises `InvalidEncryptionKeyError` for bad keys |
| `test_store_and_get_token` | Stores and retrieves encrypted tokens |
| `test_get_token_not_found` | Raises `TokenNotFoundError` for missing tokens |
| `test_get_valid_token` | Returns token only if not expired |
| `test_get_valid_token_expired` | Returns `None` for expired tokens |
| `test_delete_token` | Removes token from vault |
| `test_list_providers` | Lists all providers with stored tokens |
| `test_clear_vault` | Removes all tokens for session |
| `test_update_token` | Updates existing token (for refresh) |
| `test_encryption_works` | Verifies data is actually encrypted |
| `test_wrong_key_fails` | Cannot decrypt with different key |

### OAuth Handler Tests (`test_handler.py`)

**Core OAuth Tests:**

| Test | Description |
|------|-------------|
| `test_start_authorization` | Generates authorization URL with PKCE |
| `test_handle_callback_success` | Exchanges code for tokens |
| `test_handle_callback_state_mismatch` | Rejects invalid state parameter |
| `test_handle_callback_no_pending_state` | Raises `StateValidationError` when no OAuth state in session |
| `test_handle_callback_expired_state` | Rejects expired OAuth state |
| `test_get_access_token_valid` | Retrieves valid token for API calls |
| `test_get_access_token_auto_refresh` | Refreshes expired access token automatically |
| `test_get_access_token_expired_no_refresh` | Raises `TokenExpiredError` when no refresh token |
| `test_logout_single_provider` | Clears single provider's tokens |
| `test_logout_all_providers` | Clears all tokens and deletes session |
| `test_refresh_session` | Extends session expiration (sliding expiration) |
| `test_validate_csrf_header_success` | Validates CSRF token from X-CSRF-Token header |
| `test_validate_csrf_header_missing` | Raises `CSRFValidationError` for missing header |
| `test_validate_csrf_header_invalid` | Raises `CSRFValidationError` for invalid token |

**Back-Channel Logout Tests (OIDC Back-Channel Logout 1.0):**

| Test | Description |
|------|-------------|
| `test_backchannel_logout_success` | Invalidates user sessions on valid logout token |
| `test_backchannel_logout_multiple_sessions` | Invalidates all sessions for user (2+ sessions) |
| `test_backchannel_logout_no_matching_sessions` | Returns 0 when no sessions match `sub` claim |
| `test_backchannel_logout_invalid_jwt` | Raises `LogoutTokenError` for malformed JWT |
| `test_backchannel_logout_missing_required_claim` | Raises `LogoutTokenError` for missing `iss` claim |
| `test_backchannel_logout_missing_event` | Raises `LogoutTokenError` when events claim missing |
| `test_backchannel_logout_missing_sub_and_sid` | Raises `LogoutTokenError` when both claims missing |
| `test_backchannel_logout_unrecognized_issuer` | Raises `LogoutTokenError` for unknown issuer |
| `test_backchannel_logout_wrong_audience` | Raises `LogoutTokenError` for wrong client_id |
| `test_backchannel_logout_expired_token` | Raises `LogoutTokenError` for expired token |
| `test_backchannel_logout_token_too_old` | Raises `LogoutTokenError` for token >10 min old |
| `test_backchannel_logout_with_sid_only` | Documents sid-only lookup limitation (returns 0) |

**RP-Initiated Logout Tests (ID Token Hint):**

| Test | Description |
|------|-------------|
| `test_get_logout_url_with_id_token` | Returns logout URL with `id_token_hint` |
| `test_get_logout_url_without_id_token` | Returns logout URL with `client_id` as fallback |
| `test_get_logout_url_no_token` | Returns logout URL with `client_id` when no token stored |
| `test_get_logout_url_with_state` | Includes `state` parameter when provided |
| `test_get_logout_url_no_end_session_endpoint` | Returns `None` when provider has no logout endpoint |
| `test_get_logout_url_provider_not_registered` | Returns `None` for unregistered provider |

### Backend Tests (`test_backend.py`)

| Test | Description |
|------|-------------|
| `test_pkce_verifier_generation` | Generates 43-128 character verifiers |
| `test_pkce_challenge_generation` | Creates S256 code challenge |
| `test_build_authorization_url` | Constructs proper authorization URL |
| `test_exchange_code` | Exchanges authorization code for tokens |
| `test_refresh_token` | Uses refresh token to get new access token |
| `test_revoke_token` | Calls revocation endpoint |

### Provider Tests (`test_providers.py`)

| Test | Description |
|------|-------------|
| `test_google_provider_config` | Validates Google OAuth endpoints |
| `test_azure_provider_config` | Validates Azure AD endpoints |
| `test_azure_b2c_config` | Validates Azure B2C tenant format |
| `test_github_provider_config` | Validates GitHub OAuth endpoints |
| `test_github_enterprise_config` | Validates GitHub Enterprise URLs |

### Redis Storage Tests (`test_redis_storage.py`)

Unit tests using mock Redis client:

| Test | Description |
|------|-------------|
| `test_set_and_get_session` | Basic session storage operations |
| `test_get_expired_session` | Returns `None` for expired sessions |
| `test_set_with_ttl` | Sets Redis TTL from session expiration |
| `test_cleanup_expired` | Removes stale sessions |
| `test_extend_session` | Sliding expiration support |
| `test_set_and_get_vault` | Basic vault storage operations |
| `test_default_ttl` | Applies default TTL to vault data |
| `test_custom_key_prefix` | Supports multi-tenant key prefixes |

### Redis Integration Tests (`test_redis_integration.py`)

Tests against real Redis server:

| Test | Description |
|------|-------------|
| `test_session_lifecycle` | Complete create/get/update/delete flow |
| `test_session_expiration_with_ttl` | Validates Redis TTL matches session expiry |
| `test_csrf_validation` | CSRF validation with real storage |
| `test_multiple_concurrent_sessions` | Handles 10+ concurrent sessions |
| `test_extend_session` | Sliding expiration updates TTL |
| `test_token_lifecycle` | Complete token CRUD operations |
| `test_multi_provider_tokens` | Multiple providers per session |
| `test_encryption_isolation` | Different keys can't read each other's data |
| `test_vault_ttl` | Vault data has proper TTL |

### Mock Consistency Tests

These tests verify the mock Redis client behaves like real Redis:

| Test | Description |
|------|-------------|
| `test_get_nonexistent_key` | Returns `None` |
| `test_delete_nonexistent_key` | Returns `0` |
| `test_exists_behavior` | Returns count of existing keys |
| `test_setex_behavior` | Sets value with TTL |
| `test_ttl_nonexistent_key` | Returns `-2` |
| `test_keys_pattern` | Pattern matching works correctly |

## Test Fixtures

### Common Fixtures (`conftest.py`)

```python
@pytest.fixture
def encryption_key():
    """Generate valid Fernet key."""
    return Fernet.generate_key().decode()

@pytest.fixture
def valid_session():
    """Create a valid, non-expired session."""
    now = utc_now()
    return SessionData(
        session_id="test-session-id-...",
        csrf_token="csrf-token-...",
        expires_at=now + timedelta(hours=24),
        ...
    )

@pytest.fixture
def token_record():
    """Create a valid token record."""
    return TokenRecord(
        provider=OAuthProvider.GOOGLE,
        access_token="access-token-...",
        ...
    )
```

### Integration Fixtures (`integration/conftest.py`)

```python
@pytest.fixture
async def redis_client():
    """Create async Redis client, cleanup after test."""
    client = redis.Redis.from_url("redis://localhost:6379/0")
    yield client
    await client.flushdb()  # Clean up test data
    await client.aclose()
```

## Writing New Tests

### Unit Test Example

```python
import pytest
from bffauth.core.session import SessionManager

class TestSessionManager:
    @pytest.mark.asyncio
    async def test_create_session_with_user_info(self):
        """Should store user info in session."""
        manager = SessionManager()

        session = await manager.create_session(
            user_id="user-123",
            user_info={"email": "test@example.com"},
        )

        assert session.user_id == "user-123"
        assert session.user_info["email"] == "test@example.com"
```

### Integration Test Example

```python
import pytest
from .conftest import requires_redis

@requires_redis
class TestRedisFeature:
    @pytest.mark.asyncio
    async def test_feature_with_redis(self, redis_client):
        """Test something that needs real Redis."""
        # Test code here
        pass
```

## Code Coverage

Current coverage targets:

| Module | Target | Current |
|--------|--------|---------|
| `bffauth.core.session` | 90% | ✅ |
| `bffauth.core.vault` | 90% | ✅ |
| `bffauth.core.models` | 85% | ✅ |
| `bffauth.handler` | 85% | ✅ |
| `bffauth.backends.authlib` | 80% | ✅ |
| `bffauth.storage.redis` | 90% | ✅ |

Generate coverage report:

```bash
pytest tests/ --cov=bffauth --cov-report=html
open htmlcov/index.html  # View in browser
```

## CI/CD Integration

### GitHub Actions

The project includes a GitHub Actions workflow (`.github/workflows/test.yml`) that:

1. Runs tests on Python 3.10, 3.11, and 3.12
2. Runs linting (black, ruff, mypy)
3. Builds the package
4. (Optional) Runs integration tests with Redis service

To add Redis to CI:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - 6379:6379
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

## Troubleshooting

### Tests Fail with "Session not found"

Ensure you're using timezone-aware datetimes:

```python
# Wrong
from datetime import datetime
now = datetime.utcnow()  # Naive datetime

# Correct
from bffauth.core.models import utc_now
now = utc_now()  # Timezone-aware
```

### Redis Integration Tests Skipped

Start the Redis container:

```bash
docker run -d --name bffauth-redis -p 6379:6379 redis:7-alpine
```

### Mock vs Real Redis Behavior Differences

If you find a case where the mock behaves differently from real Redis, add a test to `TestMockConsistency` and fix the mock implementation.

### Pre-commit Hooks Fail

Run formatters manually:

```bash
black bffauth/ tests/
ruff check --fix bffauth/ tests/
```
