# BFFAuth Badge Implementation Plan

This document outlines the GitHub badges we want to implement for BFFAuth to demonstrate code quality, security, and trustworthiness.

## Why Badges Matter

Badges serve as visual trust signals for potential users evaluating whether to adopt BFFAuth for their security-critical applications. For a BFF authentication library, demonstrating security best practices is especially important.

## Current Badges (v0.2.1)

```markdown
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
```

## Target Badges for v0.2.2

### Tier 1: Immediate (No External Setup Required)

These badges can be added immediately using shields.io with PyPI data:

| Badge | Purpose | Markdown |
|-------|---------|----------|
| **PyPI Version** | Shows latest release | `[![PyPI](https://img.shields.io/pypi/v/bffauth)](https://pypi.org/project/bffauth/)` |
| **PyPI Downloads** | Social proof | `[![Downloads](https://img.shields.io/pypi/dm/bffauth)](https://pypi.org/project/bffauth/)` |
| **Python Versions** | Compatibility | `[![Python](https://img.shields.io/pypi/pyversions/bffauth)](https://pypi.org/project/bffauth/)` |
| **License** | Open source status | `[![License](https://img.shields.io/pypi/l/bffauth)](https://opensource.org/licenses/Apache-2.0)` |

### Tier 2: CI/CD Status (Need GitHub Actions Workflow)

| Badge | Purpose | Setup Required |
|-------|---------|----------------|
| **CI Status** | Build passes | Create `.github/workflows/ci.yml` |
| **Tests** | Tests pass | Part of CI workflow |

Markdown (after workflow created):
```markdown
[![CI](https://github.com/ShadNygren/bffauth/actions/workflows/ci.yml/badge.svg)](https://github.com/ShadNygren/bffauth/actions/workflows/ci.yml)
```

### Tier 3: Code Quality (Need Integration)

| Badge | Purpose | Setup Required | Link |
|-------|---------|----------------|------|
| **Codecov** | Test coverage % | Integrate Codecov | https://about.codecov.io/ |
| **Ruff** | Code style | Already using, add badge | https://github.com/astral-sh/ruff |
| **Mypy** | Type safety | Already using, add badge | https://mypy-lang.org/ |
| **Pre-commit** | Code quality | Already using, add badge | https://pre-commit.com/ |

Markdown:
```markdown
[![codecov](https://codecov.io/gh/ShadNygren/bffauth/branch/main/graph/badge.svg)](https://codecov.io/gh/ShadNygren/bffauth)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
```

### Tier 4: Security (Critical for Auth Library)

| Badge | Purpose | Setup Required | Link |
|-------|---------|----------------|------|
| **Snyk** | Dependency vulnerabilities | Connect Snyk to repo | https://snyk.io/ |
| **OpenSSF Scorecard** | Security best practices | Add scorecard action | https://scorecard.dev/ |
| **OpenSSF Best Practices** | Comprehensive security | Register project | https://www.bestpractices.dev/ |

Markdown (after setup):
```markdown
[![Snyk](https://snyk.io/test/github/ShadNygren/bffauth/badge.svg)](https://snyk.io/test/github/ShadNygren/bffauth)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/ShadNygren/bffauth/badge)](https://scorecard.dev/viewer/?uri=github.com/ShadNygren/bffauth)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/XXXXX/badge)](https://www.bestpractices.dev/projects/XXXXX)
```

## Implementation Plan

### Phase 1: v0.2.2 (Immediate)

1. **Add Tier 1 badges** - No setup required
2. **Create CI workflow** - `.github/workflows/ci.yml`
3. **Add CI status badge** - After workflow created
4. **Add code style badges** - Ruff, Mypy, Pre-commit

### Phase 2: v0.2.3 or v0.3.0

1. **Integrate Codecov**
   - Sign up at https://about.codecov.io/
   - Add CODECOV_TOKEN to GitHub secrets
   - Update CI to upload coverage reports

2. **Set up Snyk**
   - Sign up at https://snyk.io/
   - Connect GitHub repository
   - Add Snyk badge

3. **Set up OpenSSF Scorecard**
   - Add scorecard-action to CI workflow
   - Enable publish_results: true
   - Add scorecard badge

### Phase 3: Future

1. **OpenSSF Best Practices Badge**
   - Register at https://www.bestpractices.dev/
   - Complete self-certification questionnaire
   - Aim for "passing" level initially

## Badge Order in README

Recommended badge order (top of README):

```markdown
# BFFAuth

OAuth 2.1 + BFF (Backend-for-Frontend) Authentication Library for Python.

<!-- Package Info -->
[![PyPI](https://img.shields.io/pypi/v/bffauth)](https://pypi.org/project/bffauth/)
[![Python](https://img.shields.io/pypi/pyversions/bffauth)](https://pypi.org/project/bffauth/)
[![Downloads](https://img.shields.io/pypi/dm/bffauth)](https://pypi.org/project/bffauth/)
[![License](https://img.shields.io/pypi/l/bffauth)](https://opensource.org/licenses/Apache-2.0)

<!-- CI/Quality -->
[![CI](https://github.com/ShadNygren/bffauth/actions/workflows/ci.yml/badge.svg)](https://github.com/ShadNygren/bffauth/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ShadNygren/bffauth/branch/main/graph/badge.svg)](https://codecov.io/gh/ShadNygren/bffauth)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

<!-- Code Style -->
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

<!-- Security -->
[![Snyk](https://snyk.io/test/github/ShadNygren/bffauth/badge.svg)](https://snyk.io/test/github/ShadNygren/bffauth)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/ShadNygren/bffauth/badge)](https://scorecard.dev/viewer/?uri=github.com/ShadNygren/bffauth)
```

## Resources

- [Shields.io](https://shields.io/) - Badge generation service
- [Naereen's Badge Collection](https://naereen.github.io/badges/) - Comprehensive badge list
- [dwyl/repo-badges](https://github.com/dwyl/repo-badges) - Badge setup guides
- [md-badges](https://github.com/inttter/md-badges) - Extensive badge collection
- [Codecov](https://about.codecov.io/) - Code coverage
- [Snyk](https://snyk.io/) - Security scanning
- [OpenSSF Scorecard](https://scorecard.dev/) - Security metrics
- [OpenSSF Best Practices](https://www.bestpractices.dev/) - Best practices certification

## References

- [Top 5 Badges That Will Show Your GitHub Repository is Well Tested & Trusted](https://medium.com/@i.egilmez/top-5-badges-that-will-show-your-github-repository-is-well-tested-trusted-4edd3bd132b3)
- [Readme Badges GitHub: Best Practices](https://daily.dev/blog/readme-badges-github-best-practices)
- [PyPI README badges](https://codeinthehole.com/tips/pypi-readme-badges/)
- [dwyl Snyk Security Scanning](https://github.com/dwyl/repo-badges/blob/main/snyk-security-scanning.md)
