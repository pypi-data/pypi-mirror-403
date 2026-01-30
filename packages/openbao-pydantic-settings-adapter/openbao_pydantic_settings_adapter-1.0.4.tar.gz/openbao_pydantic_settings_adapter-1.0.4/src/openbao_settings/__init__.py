"""OpenBao settings source for pydantic-settings."""

__version__ = "1.0.4"

from .client import OpenBaoClient
from .models import (
    # Exceptions
    ForbiddenError,
    InvalidPathError,
    InvalidRequestError,
    InvalidResponseError,
    OpenBaoError,
    SecurityMisconfigurationError,
    # Response models
    AppRoleLoginResponse,
    AuthInfo,
    KvV2ReadResponse,
    SecretDataWrapper,
    SourceInfo,
)
from .source import (
    OpenBaoSettingsSource,
    TokenEntry,
    TokenManager,
    deep_merge,
    get_last_source_info,
)

__all__ = [
    "AppRoleLoginResponse",
    "AuthInfo",
    "ForbiddenError",
    "InvalidPathError",
    "InvalidRequestError",
    "InvalidResponseError",
    "KvV2ReadResponse",
    "OpenBaoClient",
    "OpenBaoError",
    "OpenBaoSettingsSource",
    "SecretDataWrapper",
    "SecurityMisconfigurationError",
    "SourceInfo",
    "TokenEntry",
    "TokenManager",
    "deep_merge",
    "get_last_source_info",
]
