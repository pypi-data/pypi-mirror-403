# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-01-24

### Changed
- **Documentation Updates** - Comprehensive update to reflect v0.2.0 features
  - Updated README.md competitive analysis table with implemented features (✅ for back-channel logout, RP-Initiated logout, sliding sessions, Redis storage)
  - Added Release History section showing v0.1.0 and v0.2.0 releases
  - Updated API Reference with new methods (`get_logout_url`, `handle_backchannel_logout`, `refresh_session`, `validate_csrf_header`)
  - Updated Exceptions table with `LogoutTokenError`, `StateValidationError`
  - Updated Production Storage section with built-in Redis storage examples
  - Updated Installation section with `bffauth[redis]` optional dependency

- **Release Process** - Added comprehensive release checklist to CLAUDE.md
  - Documentation review checklist before version bump
  - Test PyPI verification before git tag (prevents releasing broken packages)
  - Reordered steps: Test PyPI → Git Tag → GitHub Release → Production PyPI

## [0.2.0] - 2026-01-24

### Added
- **Redis Storage Backends**
  - `RedisSessionStorage` - Production-ready session storage with automatic TTL
  - `RedisVaultStorage` - Encrypted token vault storage with Redis backend
  - Automatic TTL-based expiration aligned with session/token lifetimes
  - Custom key prefix support for multi-tenant deployments
  - Protocol-based design allowing easy swap between storage backends
  - Install with: `pip install bffauth[redis]`

- **Sliding Session Expiration**
  - `handler.refresh_session(session_id)` - Extends session lifetime on activity
  - `storage.extend_session(session_id, timedelta)` - Direct storage extension
  - Designed for middleware integration in FastAPI/Flask/Django

- **CSRF Header Validation**
  - `handler.validate_csrf_header(session_id, header_value)` - API endpoint protection
  - Validates `X-CSRF-Token` header (configurable name)
  - Clear error messages for missing or invalid tokens

- **Back-Channel Logout (OpenID Connect)**
  - `handler.handle_backchannel_logout(logout_token)` - Process IdP logout notifications
  - Validates logout token claims per OIDC Back-Channel Logout 1.0 specification
  - Invalidates all sessions for the user (by `sub` claim)
  - New `LogoutTokenError` exception for validation failures
  - `session_storage.find_by_user_id()` method for session lookup
  - `session_manager.delete_user_sessions()` for bulk session invalidation

- **RP-Initiated Logout with ID Token Hint**
  - `handler.get_logout_url(session_id, provider)` - Generate IdP logout URL
  - Includes `id_token_hint` when available for secure session matching
  - Supports `post_logout_redirect_uri` and `state` parameters
  - Falls back to `client_id` when ID token not available
  - Azure AD/Entra ID `end_session_endpoint` added to provider configs

- **Integration Testing Infrastructure**
  - 15 integration tests against real Redis server
  - Mock consistency tests validating mock behavior matches real Redis
  - `@requires_redis` decorator for graceful skip when Redis unavailable
  - Docker-based Redis setup: `docker run -d -p 6379:6379 redis:7-alpine`

- **Testing Documentation**
  - `docs/TESTING.md` - Comprehensive testing guide
  - Test organization and categories
  - Fixture documentation
  - CI/CD integration guidance

### Changed
- **OAuth State Storage** - Moved from handler memory to session metadata
  - Enables multi-instance deployments behind load balancers
  - State is session-bound for improved security
  - Automatic cleanup after successful callback (one-time use)
  - State expiration enforced on callback

- **Type Annotations** - Fixed mypy strict mode compliance
  - Added proper generic types (`dict[str, Any]`, `Pattern[str]`)
  - Added `cast()` for external library returns
  - Proper `# type: ignore` for third-party libraries without stubs
  - All modules now pass `mypy --strict`

## [0.1.0] - 2025-01-21

### Added
- **Core Session Management**
  - Cryptographically secure session IDs (256-bit)
  - `__Host-` prefixed cookies with Secure, HttpOnly, SameSite attributes
  - CSRF token generation and constant-time validation
  - Session expiration and activity tracking
  - In-memory session storage with protocol-based interface

- **Token Vault**
  - Fernet encryption (AES-128-CBC + HMAC-SHA256) for tokens at rest
  - Multi-provider token storage per session
  - Token expiration tracking with pre-emptive refresh buffer
  - In-memory vault storage with protocol-based interface

- **OAuth 2.0/2.1 Support**
  - Authorization code flow with PKCE (RFC 7636)
  - State parameter generation and validation
  - Token exchange and refresh with rotation support
  - Token revocation (RFC 7009)
  - OpenID Connect ID token decoding

- **Provider Configurations**
  - Google OAuth configuration
  - Azure AD / Entra ID configuration (including B2C)
  - GitHub OAuth configuration (including Enterprise)
  - Generic OIDC provider support with discovery

- **Security Features**
  - Resource server allowlist validation
  - URL pattern matching with regex
  - HTTP method and scope-based access control
  - Provider-specific restrictions

- **Exception Hierarchy**
  - Comprehensive exception types for all error conditions
  - Session, token, OAuth, encryption, and storage errors

- **Documentation**
  - SPECIFICATION.md - Functional and security requirements
  - DESIGN.md - Component architecture and implementation details
  - ARCHITECTURE.md - System design and deployment patterns
  - ROADMAP.md - Development timeline and milestones
  - CLAUDE.md - Developer guidelines and best practices

### Security
- All tokens encrypted at rest using Fernet
- CSRF protection with constant-time comparison
- Secure cookie defaults enforced for `__Host-` prefix
- PKCE required for all OAuth flows

[Unreleased]: https://github.com/ShadNygren/bffauth/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/ShadNygren/bffauth/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/ShadNygren/bffauth/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ShadNygren/bffauth/releases/tag/v0.1.0
