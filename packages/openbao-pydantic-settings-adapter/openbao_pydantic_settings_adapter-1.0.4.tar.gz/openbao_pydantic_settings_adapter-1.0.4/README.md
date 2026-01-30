# openbao-pydantic-settings-adapter

[![PyPI version](https://badge.fury.io/py/openbao-pydantic-settings-adapter.svg)](https://pypi.org/project/openbao-pydantic-settings-adapter/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: PolyForm Noncommercial](https://img.shields.io/badge/License-PolyForm%20Noncommercial-blue.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0/)

OpenBao/Vault secrets source for [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) with AppRole authentication, automatic token renewal, and graceful fallback to environment variables.

## Features

- **AppRole Authentication** - Secure machine-to-machine authentication
- **Automatic Token Renewal** - TokenManager handles TTL-based token lifecycle
- **Namespace Support** - Multi-tenant isolation (team/project level)
- **Two-Path Architecture** - Separate `secrets` and `supersecrets` paths with deep merge
- **SecretStr Validation** - Enforces `SecretStr` for supersecrets to prevent log exposure
- **Graceful Degradation** - Falls back to `.env` when OpenBao is unavailable
- **Type Safety** - Full type annotations with `py.typed` marker (PEP 561)

## Installation

```bash
pip install openbao-pydantic-settings-adapter
```

**Note:** The import name is `openbao_settings`:

```python
from openbao_settings import OpenBaoSettingsSource
```

## Quick Start

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from openbao_settings import OpenBaoSettingsSource


class Settings(BaseSettings):
    database_url: str
    api_key: SecretStr  # Fields from supersecrets MUST use SecretStr

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            OpenBaoSettingsSource(settings_cls),  # OpenBao has priority
            env_settings,
            dotenv_settings,
        )


settings = Settings()
```

## Configuration

Configure via environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `BAO_ADDR` | OpenBao server URL (e.g., `http://localhost:8200`) | Yes |
| `BAO_SECRET_PATH` | Base path to secrets (e.g., `myapp`) | Yes |
| `BAO_APPROLE_ROLE_ID` | AppRole Role ID | Yes |
| `BAO_APPROLE_SECRET_ID` | AppRole Secret ID | Yes |
| `BAO_NAMESPACE` | OpenBao namespace for multi-tenant isolation | No |
| `BAO_MOUNT_POINT` | KV engine mount point (default: `kv`) | No |
| `BAO_TIMEOUT` | Connection timeout in seconds (default: `30`) | No |
| `BAO_TOKEN_RENEWAL_THRESHOLD` | When to renew token (default: `0.75` = at 75% of TTL) | No |

For Docker/Kubernetes, you can use file-based credentials:
- `BAO_APPROLE_ROLE_ID_FILE`
- `BAO_APPROLE_SECRET_ID_FILE`
- `BAO_NAMESPACE_FILE`

## Secrets Architecture

The library reads from two paths and merges them:

```
kv/{BAO_SECRET_PATH}/secrets      - Regular secrets (developers can view/edit)
kv/{BAO_SECRET_PATH}/supersecrets - Sensitive secrets (admin only)
```

**Important:** Fields loaded from `supersecrets` MUST use `SecretStr` type annotation. The library validates this at runtime and raises `SecurityMisconfigurationError` if violated.

```python
# Wrong - will raise SecurityMisconfigurationError
class Settings(BaseSettings):
    api_key: str  # Loaded from supersecrets but not SecretStr!

# Correct
class Settings(BaseSettings):
    api_key: SecretStr  # Properly protected
```

## Token Lifecycle

`TokenManager` automatically handles token renewal:

1. Caches tokens per `(namespace, role_id)` combination
2. Renews at 75% of TTL (configurable via `BAO_TOKEN_RENEWAL_THRESHOLD`)
3. Thread-safe for multi-threaded applications
4. Graceful degradation if OpenBao becomes unavailable

```python
from openbao_settings import TokenManager

# Manual token invalidation (e.g., for credential rotation)
TokenManager().invalidate()

# Check token health
TokenManager().is_healthy(namespace="myapp", role_id="...")
```

## Diagnostics

Track where settings were loaded from:

```python
from openbao_settings import get_last_source_info, SourceInfo

info: SourceInfo = get_last_source_info()
print(info.status)              # True if loaded from OpenBao
print(info.source)              # "openbao" or "env"
print(info.details)             # Human-readable description
print(info.openbao_keys_loaded) # Number of keys from OpenBao
print(info.timestamp)           # When the check was performed
```

## API Reference

### Classes

- `OpenBaoSettingsSource` - Main settings source for pydantic-settings
- `OpenBaoClient` - Low-level HTTP client for OpenBao API
- `TokenManager` - Singleton for token lifecycle management

### Exceptions

- `OpenBaoError` - Base exception for all OpenBao errors
- `InvalidPathError` - Path not found (HTTP 404)
- `InvalidRequestError` - Invalid request/credentials (HTTP 400)
- `ForbiddenError` - Access denied (HTTP 403)
- `InvalidResponseError` - Unexpected API response structure
- `SecurityMisconfigurationError` - SecretStr validation failed

### Response Models

- `AppRoleLoginResponse` - AppRole authentication response
- `KvV2ReadResponse` - KV v2 read response
- `SourceInfo` - Settings source diagnostic info

## Development

### Syncing with Remote

```bash
# Fetch commits and tags
git pull origin main --tags

# If local branch is behind remote
git reset --hard origin/main
```

### Verify sync status

```bash
git log --oneline origin/main -5
git diff origin/main
```

## CI/CD

The pipeline consists of two stages:

1. **auto_tag** — on push to `main`, reads `__version__` from `__init__.py` and automatically creates a tag (if it doesn't exist)

2. **mirror_to_github** — on tag creation, mirrors the repository to GitHub (removing `.gitlab-ci.yml`)

### Release flow

1. Update `__version__` in `src/openbao_settings/__init__.py`
2. Push to main
3. CI creates tag → mirrors to GitHub → publishes to PyPI

## Versioning

This project follows [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **PATCH** — bug fixes, documentation, metadata
- **MINOR** — new features (backwards compatible)
- **MAJOR** — breaking changes

## License

This project is licensed under the **PolyForm Noncommercial License 1.0.0**.

**You may use this software for noncommercial purposes only.**

See [LICENSE](LICENSE) for the full license text, or visit [polyformproject.org](https://polyformproject.org/licenses/noncommercial/1.0.0/).
