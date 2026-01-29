# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the BFFAuth codebase.

## Project Overview

BFFAuth is a Python library implementing the Backend-for-Frontend (BFF) pattern for OAuth 2.0/2.1 as specified in [IETF draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps).

**Core Purpose**: Provide a secure server-side component that handles all OAuth operations on behalf of browser-based applications, ensuring tokens never reach the browser.

**Key Differentiators**:
- Python-native with Pydantic models
- Built on Authlib (battle-tested OAuth library)
- Protocol-based interfaces (fully swappable components)
- Apache 2.0 license (unlike commercial alternatives)

## Architecture

### Component Structure

```
bffauth/
├── core/                  # Core BFF components
│   ├── models.py          # Pydantic data models
│   ├── session.py         # Session management
│   ├── vault.py           # Encrypted token storage
│   ├── exceptions.py      # Custom exceptions
│   └── oauth.py           # OAuth client wrapper
├── integrations/          # Framework integrations (planned)
│   ├── fastapi/
│   ├── flask/
│   └── django/
└── storage/               # Storage backends (planned)
    ├── memory.py          # In-memory (current)
    ├── redis.py           # Redis backend (planned)
    └── database.py        # SQLAlchemy backend (planned)
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| SessionManager | `core/session.py` | Secure session lifecycle management |
| TokenVault | `core/vault.py` | Encrypted multi-provider token storage |
| SessionData | `core/models.py` | Session state Pydantic model |
| TokenRecord | `core/models.py` | Token data Pydantic model |

### Security Architecture

```
Browser ──cookie──▶ BFFAuth ──token──▶ API
         │                    │
         │ No tokens          │ Bearer token
         │ cross this         │ injected
         │ boundary           │ here
         ▼                    ▼
    __Host-session       Authorization: Bearer
    HttpOnly, Secure     (from encrypted vault)
    SameSite=Strict
```

## Development Environment

### Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

### ALWAYS Use Virtual Environment

**CRITICAL**: Always activate the virtual environment before running any Python commands:

```bash
source venv/bin/activate && pytest tests/
source venv/bin/activate && python -c "from bffauth import ..."
```

### Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# With coverage
pytest tests/ --cov=bffauth --cov-report=html

# Specific test file
pytest tests/unit/test_session.py -v
```

## Collaborative Git Workflow (Multi-User/Multi-Agent)

### ⚠️ CRITICAL: Working in Distributed Development Environments

This repository may have multiple contributors working simultaneously:
- Human developers editing directly on GitHub or locally
- Multiple AI agents (Claude Code sessions) working on different tasks
- CI/CD systems making automated commits
- Other tools or integrations modifying files

**With great power comes great responsibility.** AI agents have significant capability to make changes quickly, but must exercise caution to avoid overwriting others' work.

### When a `git push` is Rejected

If `git push` fails with "Updates were rejected because the remote contains work that you do not have locally":

**DO NOT** immediately run `git pull --rebase` or `git pull` without investigation.

**INSTEAD, follow this protocol:**

1. **Fetch and examine remote changes first:**
   ```bash
   git fetch origin
   git log HEAD..origin/main --oneline  # See what commits are on remote
   git log origin/main --oneline -5     # See recent remote history
   git diff HEAD..origin/main --stat    # See which files changed
   ```

2. **Understand what changed:**
   - Read the commit messages
   - Check which files were modified
   - If unclear, ask the user what changes were made

3. **Ask the user for guidance:**
   - Explain what you found on the remote
   - Ask how they want to integrate the changes
   - Get explicit permission before any merge or rebase

4. **Only then proceed with the user's chosen approach:**
   - `git pull` (merge) - preserves both histories, creates merge commit
   - `git pull --rebase` - replays local commits on top of remote (cleaner history but riskier)
   - Manual conflict resolution if needed

### Preventing Conflicts Proactively

1. **Pull before starting work:**
   ```bash
   git pull origin main
   ```

2. **Communicate about file ownership:**
   - If working on specific files, mention it
   - Avoid editing files that others are actively modifying

3. **Make small, focused commits:**
   - Easier to merge and resolve conflicts
   - Clear commit messages help others understand changes

4. **Check remote status periodically during long tasks:**
   ```bash
   git fetch origin
   git status  # Shows if branch has diverged
   ```

### Resolving Merge Conflicts

If conflicts occur:

1. **Never auto-resolve without understanding:**
   - Read both versions of conflicting code
   - Understand the intent of both changes

2. **Ask for help when uncertain:**
   - Show the user the conflict
   - Let them decide which version to keep or how to merge

3. **Test after resolution:**
   - Run tests to ensure merged code works
   - Verify no functionality was lost

### Example: Safe Push Workflow

```bash
# Before pushing, check if remote has changes
git fetch origin
git status

# If "Your branch is ahead" - safe to push
git push

# If "Your branch and 'origin/main' have diverged" - STOP and investigate
git log HEAD..origin/main --oneline
git diff HEAD..origin/main --stat
# Then ASK the user how to proceed
```

## Critical Design Principles

### 1. Protocol-Based Interfaces

All external dependencies use Protocol-based interfaces for swappability:

```python
# CORRECT - Protocol-based
class SessionStorageProtocol(Protocol):
    async def get(self, session_id: str) -> Optional[SessionData]: ...
    async def set(self, session: SessionData) -> None: ...

class SessionManager:
    def __init__(self, storage: SessionStorageProtocol):
        self.storage = storage  # Injected dependency

# WRONG - Tight coupling
class SessionManager:
    def __init__(self):
        self.storage = RedisStorage()  # Hardcoded dependency
```

### 2. No Mock Data in Business Logic

Mock implementations belong ONLY in `tests/mocks/`, never in production code:

```python
# WRONG - Mock in business logic
class TokenVault:
    def get_token(self, session_id: str, use_mock=False):
        if use_mock:
            return self._mock_token()  # BAD!
        return self._real_token()

# CORRECT - Dependency injection
class TokenVault:
    def __init__(self, storage: VaultStorageProtocol):
        self.storage = storage  # Mock injected via tests

# In tests:
vault = TokenVault(storage=MockVaultStorage())
```

### 3. Timezone-Aware Datetimes

Always use timezone-aware datetimes to avoid comparison errors:

```python
# WRONG - Naive datetime (deprecated in Python 3.12+)
from datetime import datetime
now = datetime.utcnow()  # BAD!

# CORRECT - Timezone-aware
from datetime import datetime, timezone

def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)

# Or use the helper from models.py
from bffauth.core.models import utc_now
```

### 4. Pydantic Model Validation

All data models use Pydantic with strict validation:

```python
from pydantic import BaseModel, Field

class SessionData(BaseModel):
    session_id: str = Field(min_length=32)  # Enforce 256-bit minimum
    csrf_token: str = Field(min_length=32)
    expires_at: datetime
```

### 5. Security-First Defaults

Always default to the most secure option:

```python
class SessionManager:
    def __init__(
        self,
        cookie_name: str = "__Host-session",  # Secure prefix
        cookie_secure: bool = True,            # HTTPS only
        cookie_samesite: str = "strict",       # CSRF protection
    ):
        # Validate __Host- requirements
        if cookie_name.startswith("__Host-"):
            if not cookie_secure:
                raise ValueError("__Host- cookies require Secure=True")
```

## Code Patterns

### Async Pattern

All I/O operations are async:

```python
class TokenVault:
    async def store_token(self, session_id: str, token: TokenRecord) -> None:
        vault = await self.get_vault(session_id)
        vault.set_token(token)
        await self.save_vault(session_id, vault)

    async def get_token(self, session_id: str, provider: OAuthProvider) -> TokenRecord:
        vault = await self.get_vault(session_id)
        token = vault.get_token(provider)
        if token is None:
            raise TokenNotFoundError(provider.value)
        return token
```

### Exception Hierarchy

Custom exceptions inherit from base classes:

```python
# Base exceptions
class BFFAuthError(Exception):
    """Base exception for BFFAuth."""
    pass

class SessionError(BFFAuthError):
    """Session-related errors."""
    pass

class TokenError(BFFAuthError):
    """Token-related errors."""
    pass

# Specific exceptions
class SessionNotFoundError(SessionError):
    """Session does not exist."""
    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id[:8]}...")

class TokenNotFoundError(TokenError):
    """Token not found for provider."""
    def __init__(self, provider: str):
        super().__init__(f"No token for provider: {provider}")
```

### Encryption Pattern

Tokens are always encrypted at rest using Fernet:

```python
from cryptography.fernet import Fernet

class TokenVault:
    def __init__(self, encryption_key: str):
        try:
            self._cipher = Fernet(encryption_key.encode())
        except (ValueError, TypeError) as e:
            raise InvalidEncryptionKeyError() from e

    def _encrypt(self, data: dict) -> bytes:
        json_bytes = json.dumps(data, default=str).encode("utf-8")
        return self._cipher.encrypt(json_bytes)

    def _decrypt(self, encrypted_data: bytes) -> dict:
        decrypted_bytes = self._cipher.decrypt(encrypted_data)
        return json.loads(decrypted_bytes.decode("utf-8"))
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_session.py
│   ├── test_vault.py
│   └── test_models.py
├── integration/             # Integration tests (with mocked external services)
│   └── test_oauth_flow.py
├── mocks/                   # Mock implementations
│   ├── mock_storage.py
│   └── mock_oauth_provider.py
└── conftest.py              # Shared fixtures
```

### Test Fixtures

```python
import pytest
from cryptography.fernet import Fernet

@pytest.fixture
def encryption_key():
    """Generate valid Fernet key."""
    return Fernet.generate_key().decode()

@pytest.fixture
def vault(encryption_key):
    """Create token vault."""
    return TokenVault(encryption_key=encryption_key)

@pytest.fixture
def valid_session_id():
    """Generate valid session ID (32+ chars)."""
    return "a" * 32 + "-test-session"
```

### Test Patterns

```python
import pytest
from datetime import datetime, timedelta, timezone

class TestTokenVault:
    @pytest.mark.asyncio
    async def test_store_and_get_token(self, vault, token_record):
        """Should store and retrieve token."""
        await vault.store_token("session-123" + "x" * 20, token_record)
        retrieved = await vault.get_token("session-123" + "x" * 20, OAuthProvider.GOOGLE)
        assert retrieved.access_token == token_record.access_token

    @pytest.mark.asyncio
    async def test_get_token_not_found(self, vault):
        """Should raise TokenNotFoundError for unknown provider."""
        with pytest.raises(TokenNotFoundError):
            await vault.get_token("session-123" + "x" * 20, OAuthProvider.GOOGLE)
```

## Common Tasks

### Adding a New Provider

1. Add provider enum in `core/models.py`:
```python
class OAuthProvider(str, Enum):
    GOOGLE = "google"
    AZURE = "azure"
    GITHUB = "github"  # New provider
```

2. Create provider configuration:
```python
# In provider configs
GITHUB_CONFIG = ProviderConfig(
    client_id=os.environ["GITHUB_CLIENT_ID"],
    authorize_endpoint="https://github.com/login/oauth/authorize",
    token_endpoint="https://github.com/login/oauth/access_token",
    scopes=["user", "repo"],
)
```

### Adding a New Storage Backend

1. Implement the storage protocol:
```python
class RedisSessionStorage(SessionStorageProtocol):
    def __init__(self, redis_client):
        self.redis = redis_client

    async def get(self, session_id: str) -> Optional[SessionData]:
        data = await self.redis.get(f"session:{session_id}")
        if data is None:
            return None
        return SessionData.model_validate_json(data)

    async def set(self, session: SessionData) -> None:
        ttl = int((session.expires_at - utc_now()).total_seconds())
        await self.redis.setex(
            f"session:{session.session_id}",
            ttl,
            session.model_dump_json(),
        )
```

2. Add tests in `tests/unit/test_redis_storage.py`

### Adding a New Endpoint

1. Define handler in appropriate module
2. Add tests
3. Document in SPECIFICATION.md

## Release Process

### ⚠️ CRITICAL: Follow This Process for Every Release

Releasing to PyPI is a one-way operation - once a version is published, it cannot be replaced. To maintain code quality and avoid releasing bugs to production, **always follow this process in order**:

### Pre-Release Checklist

1. **Run Full Test Suite**
   ```bash
   source venv/bin/activate
   pytest tests/ -v                                    # All tests pass
   pytest tests/ --cov=bffauth --cov-report=term      # Check coverage
   mypy bffauth/ --strict --ignore-missing-imports    # Type checking passes
   ```

2. **Update Documentation** (BEFORE version bump)

   Review and update ALL public-facing documentation to reflect current status:

   - [ ] **README.md** - This appears on PyPI and GitHub
     - [ ] Feature comparison table (✅ vs ⏳) reflects implemented features
     - [ ] API Reference table includes all public methods
     - [ ] Exceptions table includes all public exceptions
     - [ ] Installation section is accurate
     - [ ] Release History table shows all versions
     - [ ] Planned Features shows correct future versions
   - [ ] **CHANGELOG.md** - Release notes
     - [ ] All new features documented
     - [ ] All breaking changes documented
     - [ ] All bug fixes documented
   - [ ] **docs/ROADMAP.md** - Phase status
     - [ ] Completed phases marked with ✅
     - [ ] Current phase milestones accurate
   - [ ] **docs/TESTING.md** - Test documentation
     - [ ] Test counts are accurate
     - [ ] New test categories documented

   **Why this matters**: README.md is displayed on PyPI (https://pypi.org/project/bffauth/).
   Outdated feature indicators (⏳ instead of ✅) damage project credibility.

3. **Update Version Number** (BEFORE creating git tag)
   ```bash
   # Edit pyproject.toml
   version = "X.Y.Z"

   # Update CHANGELOG.md
   # Change "[Unreleased]" to "[X.Y.Z] - YYYY-MM-DD"
   # Update comparison links at bottom
   ```

4. **Commit Documentation and Version Bump**
   ```bash
   git add README.md CHANGELOG.md pyproject.toml docs/
   git commit -m "chore: Bump version to X.Y.Z"
   git push origin main
   ```

### Test PyPI First (Required)

5. **Build Package**
   ```bash
   source venv/bin/activate
   pip install build twine
   rm -rf dist/
   python -m build
   ```

6. **Upload to Test PyPI**
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

7. **Verify Test PyPI Release**
   ```bash
   # Create a fresh virtual environment
   python -m venv /tmp/test-bffauth
   source /tmp/test-bffauth/bin/activate

   # Install from Test PyPI
   pip install --index-url https://test.pypi.org/simple/ \
       --extra-index-url https://pypi.org/simple/ \
       bffauth==X.Y.Z

   # Verify it works
   python -c "from bffauth import BFFOAuthHandler; print('OK')"
   python -c "import bffauth; print(bffauth.__version__)"

   # Clean up
   deactivate
   rm -rf /tmp/test-bffauth
   ```

### Git Tag and GitHub Release (Only After Test PyPI Verification)

8. **Create Git Tag**
   ```bash
   git tag -a vX.Y.Z -m "BFFAuth vX.Y.Z - Release description"
   git push origin vX.Y.Z
   ```

9. **Create GitHub Release**
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z - Title" --notes "Release notes..."
   ```

### Production PyPI

10. **Upload to Production PyPI**
    ```bash
    python -m twine upload dist/*
    ```

11. **Verify Production Release**
    ```bash
    pip install bffauth==X.Y.Z
    python -c "from bffauth import BFFOAuthHandler; print('OK')"
    ```

### Why This Process Matters

- **Test PyPI catches packaging issues** before they affect real users
- **Version numbers must be set before tagging** - tags are permanent
- **GitHub releases reference specific commits** - version should match
- **PyPI versions are immutable** - a buggy release requires a new version number
- **Reputation matters** - users trust packages that "just work"

### Package URLs

- **Test PyPI**: https://test.pypi.org/project/bffauth/
- **Production PyPI**: https://pypi.org/project/bffauth/
- **GitHub Releases**: https://github.com/ShadNygren/bffauth/releases

## Security Checklist

When reviewing PRs, verify:

- [ ] No tokens logged or exposed in errors
- [ ] Timezone-aware datetimes used
- [ ] Session IDs are 32+ characters
- [ ] CSRF tokens validated for state-changing operations
- [ ] Encryption keys validated before use
- [ ] Allowlist checked before token injection
- [ ] Cookie security attributes enforced

## Documentation

| Document | Purpose |
|----------|---------|
| `docs/SPECIFICATION.md` | Feature requirements and API contracts |
| `docs/DESIGN.md` | Component designs and implementation details |
| `docs/ARCHITECTURE.md` | System architecture and deployment |
| `docs/ROADMAP.md` | Development timeline and milestones |

## References

- [IETF draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps)
- [RFC 6749 - OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 - PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [Authlib Documentation](https://docs.authlib.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
