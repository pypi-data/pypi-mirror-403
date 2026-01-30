"""
OpenBao Settings Source for pydantic-settings.

This module provides a custom settings source that reads secrets from OpenBao.

Supports:
- OpenBao Namespaces (team/tenant level isolation)
- AppRole authentication
- Nested secret structures
- Automatic token renewal via TokenManager (for TTL-based tokens)
- Multiple credentials support (different namespace/role combinations)

Architecture with Namespaces:
- Namespace = team/tenant (e.g.: exam-crm, sro-agent)
- Inside namespace: kv/{project}/secrets, kv/{project}/supersecrets
- Full path: {namespace}/kv/{project}/secrets

Secrets architecture:
- kv/{BAO_SECRET_PATH}/secrets - regular secrets (devs can view/edit)
- kv/{BAO_SECRET_PATH}/supersecrets - super secrets (admin only)

Application reads BOTH paths and merges data. SecretStr in models prevents
accidental output of sensitive values to logs.

Token Lifecycle (TokenManager):
- Tokens are cached per (namespace, role_id) combination
- Automatic renewal at 75% of TTL (configurable via BAO_TOKEN_RENEWAL_THRESHOLD)
- Graceful degradation: uses existing token if OpenBao is temporarily unavailable
- Thread-safe for multi-threaded applications
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Self, cast, get_args, get_origin

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

# Load .env file into os.environ for local development.
# In Docker, env vars are injected via env_file directive, so this is a no-op.
# load_dotenv() won't overwrite existing env vars.
load_dotenv()

from .client import OpenBaoClient
from .models import (
    ForbiddenError,
    InvalidPathError,
    InvalidRequestError,
    OpenBaoError,
    SecurityMisconfigurationError,
    SourceInfo,
)

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

logger = logging.getLogger(__name__)

# Moscow timezone (UTC+3) for timestamps
MOSCOW_TZ = timezone(timedelta(hours=3))


# ===== Type checking helpers for SecretStr validation =====


def _is_secret_str_type(annotation: Any) -> bool:
    """
    Check if annotation is or contains SecretStr.

    Handles:
    - Direct SecretStr
    - Optional[SecretStr] (SecretStr | None)
    - Union types containing SecretStr
    - list[SecretStr]

    Args:
        annotation: Type annotation to check

    Returns:
        True if the type is or contains SecretStr

    """
    if annotation is None:
        return False

    # Direct match
    if annotation is SecretStr:
        return True

    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)

        # Handle list[SecretStr]
        if origin is list:
            return len(args) > 0 and _is_secret_str_type(args[0])

        # Handle Optional/Union types (e.g., SecretStr | None)
        return any(_is_secret_str_type(arg) for arg in args)

    return False


def _get_model_from_annotation(annotation: Any) -> type[BaseModel] | None:
    """
    Extract BaseModel class from annotation.

    Handles:
    - Direct BaseModel subclass
    - Optional[Model] (Model | None)

    Args:
        annotation: Type annotation to extract model from

    Returns:
        BaseModel subclass or None if not a model

    """
    if annotation is None:
        return None

    # Direct BaseModel subclass
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation

    # Handle Optional/Union types
    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)
        for arg in args:
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                return arg

    return None


def _is_list_of_models(annotation: Any) -> tuple[bool, type[BaseModel] | None]:
    """
    Check if annotation is list[BaseModel].

    Handles:
    - list[Model]
    - list[Model] | None (Optional)

    Args:
        annotation: Type annotation to check

    Returns:
        Tuple of (is_list_of_models, model_class)

    """
    origin = get_origin(annotation)

    # Handle Optional/Union (e.g., list[Model] | None)
    if origin is not list and origin is not None:
        args = get_args(annotation)
        for arg in args:
            result, model = _is_list_of_models(arg)
            if result:
                return result, model
        return False, None

    if origin is not list:
        return False, None

    args = get_args(annotation)
    if not args:
        return False, None

    # Check if list element is a BaseModel
    element_type = args[0]
    model = _get_model_from_annotation(element_type)
    return model is not None, model


def _collect_non_secret_str_fields(
    model_cls: type[BaseModel],
    data: dict[str, Any],
    path_prefix: str = "",
) -> list[str]:
    """
    Recursively collect fields that should use SecretStr but don't.

    Checks all string fields in the model against the data.
    For nested models, recurses into them.

    Handles:
    - Direct string fields (must be SecretStr)
    - Nested models (recurses into them)
    - list[Model] (checks each element)
    - list[str] (must be list[SecretStr])

    Args:
        model_cls: Pydantic model class to check
        data: Data dict from OpenBao supersecrets
        path_prefix: Current path for nested fields (e.g., "token.")

    Returns:
        List of field paths that should use SecretStr (e.g., ["token.key", "token.secret"])

    """
    violations: list[str] = []

    for field_name, field_info in model_cls.model_fields.items():
        if field_name not in data:
            continue

        field_value = data[field_name]
        annotation = field_info.annotation
        full_path = f"{path_prefix}{field_name}"

        # Check for nested model (dict)
        nested_model = _get_model_from_annotation(annotation)
        if nested_model is not None and isinstance(field_value, dict):
            nested_violations = _collect_non_secret_str_fields(
                nested_model,
                field_value,
                f"{full_path}.",
            )
            violations.extend(nested_violations)

        # Check for list[Model]
        elif isinstance(field_value, list):
            is_list_of_models, list_model = _is_list_of_models(annotation)
            if is_list_of_models and list_model is not None:
                # Check each element in list
                for idx, item in enumerate(field_value):
                    if isinstance(item, dict):
                        nested_violations = _collect_non_secret_str_fields(
                            list_model,
                            item,
                            f"{full_path}[{idx}].",
                        )
                        violations.extend(nested_violations)
            elif (
                field_value
                and isinstance(field_value[0], str)
                and not _is_secret_str_type(annotation)
            ):
                # list[str] - must be list[SecretStr]
                violations.append(full_path)

        # Check for string field
        elif isinstance(field_value, str) and not _is_secret_str_type(annotation):
            violations.append(full_path)

    return violations


# Minimum seconds remaining before token is considered unhealthy
MIN_HEALTHY_TOKEN_SECONDS = int(os.getenv("BAO_MIN_HEALTHY_TOKEN_SECONDS", "60"))

# Global storage for last source info (updated by _load_data)
_last_source_info: SourceInfo | None = None


def get_last_source_info() -> SourceInfo:
    """
    Get information about the last settings load source.

    This function returns information about where settings were loaded from
    during the most recent Settings() creation or reload.

    Returns:
        SourceInfo with:
        - status: Whether settings were loaded from OpenBao
        - timestamp: When the check was performed
        - source: "openbao" or "env"
        - details: Human-readable description
        - openbao_keys_loaded: Number of keys from OpenBao (0 if not used)

    Example:
        >>> from openbao_settings import get_last_source_info
        >>> info = get_last_source_info()
        >>> print(info.source)  # "env"
        >>> print(info.details)  # "OpenBao at http://... not available"

    """
    if _last_source_info is None:
        return SourceInfo(
            status=False,
            timestamp=datetime.now(MOSCOW_TZ),
            source="env",
            details="Settings not yet loaded",
            openbao_keys_loaded=0,
        )
    return _last_source_info


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merge two dictionaries.

    override takes priority over base for same keys.
    Nested dictionaries are merged recursively.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@dataclass
class TokenEntry:
    """Cached token entry with metadata."""

    token: str
    expires_at: float
    ttl: int
    role_id: str
    secret_id: str


class TokenManager:
    """
    Manages OpenBao token lifecycle with automatic renewal.

    Features:
    - Caches tokens per (namespace, role_id) combination
    - Automatically renews token before expiration (at 75% of TTL)
    - Thread-safe for multi-threaded applications
    - Graceful degradation when OpenBao is unavailable
    - Validates credentials before using cached token

    Usage:
        manager = TokenManager()
        token = manager.get_token(client, role_id, secret_id, namespace)
    """

    _instance: TokenManager | None = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> Self:
        """Singleton pattern for shared token cache across all Settings instances."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False  # noqa: SLF001
        return cast("Self", cls._instance)

    def __init__(self) -> None:
        """Initialize token manager (only once due to singleton)."""
        # Double-check locking to prevent race condition during initialization
        if self._initialized:
            return

        with self._instance_lock:
            if self._initialized:
                return

            # Cache tokens by (namespace, role_id) key
            self._tokens: dict[str, TokenEntry] = {}
            self._token_lock = threading.RLock()
            self._renewal_threshold = float(
                os.getenv("BAO_TOKEN_RENEWAL_THRESHOLD", "0.75")
            )
            self._initialized = True
            logger.debug(
                "TokenManager initialized (renewal threshold: %.0f%%)",
                self._renewal_threshold * 100,
            )

    def _make_cache_key(self, namespace: str | None, role_id: str) -> str:
        """Create cache key from namespace and role_id."""
        return f"{namespace or ''}:{role_id}"

    def get_token(
        self,
        client: OpenBaoClient,
        role_id: str,
        secret_id: str,
        namespace: str | None = None,
    ) -> str | None:
        """
        Get a valid token, renewing if necessary.

        Args:
            client: OpenBaoClient instance
            role_id: AppRole role ID
            secret_id: AppRole secret ID
            namespace: OpenBao namespace (optional)

        Returns:
            Valid token string or None if authentication fails

        """
        cache_key = self._make_cache_key(namespace, role_id)

        with self._token_lock:
            entry = self._tokens.get(cache_key)

            # Check if we need to authenticate
            if self._should_renew(entry, secret_id):
                self._authenticate(client, role_id, secret_id, namespace)
                entry = self._tokens.get(cache_key)

            return entry.token if entry else None

    def _should_renew(self, entry: TokenEntry | None, secret_id: str) -> bool:
        """
        Check if token needs renewal.

        Returns True if:
        - No token exists
        - Credentials changed (different secret_id)
        - More than renewal_threshold of TTL has elapsed (e.g., 45 min of 1h)

        Returns False if:
        - Token exists with same credentials and TTL=0 (permanent token)
        - Token exists with same credentials and less than threshold elapsed
        """
        if not entry:
            return True

        # Check if credentials changed
        if entry.secret_id != secret_id:
            logger.debug("Credentials changed, will re-authenticate")
            return True

        # TTL=0 means permanent token, no renewal needed
        if entry.ttl == 0:
            return False

        time_elapsed = time.time() - (entry.expires_at - entry.ttl)
        threshold_seconds = entry.ttl * self._renewal_threshold

        should_renew = time_elapsed >= threshold_seconds
        if should_renew:
            remaining = entry.expires_at - time.time()
            logger.debug(
                "Token renewal needed (%.0fs remaining of %ds TTL)",
                remaining,
                entry.ttl,
            )
        return should_renew

    def _authenticate(
        self,
        client: OpenBaoClient,
        role_id: str,
        secret_id: str,
        namespace: str | None,
    ) -> bool:
        """
        Authenticate via AppRole and cache the token.

        Returns:
            True if authentication succeeded, False otherwise

        """
        cache_key = self._make_cache_key(namespace, role_id)

        try:
            response = client.approle_login(role_id=role_id, secret_id=secret_id)
            token = response.auth.client_token
            ttl = response.auth.lease_duration
            expires_at = time.time() + ttl
            client.token = token

            # Cache the token with credentials info
            self._tokens[cache_key] = TokenEntry(
                token=token,
                expires_at=expires_at,
                ttl=ttl,
                role_id=role_id,
                secret_id=secret_id,
            )

            ns_info = f"[{namespace}] " if namespace else ""
            if ttl == 0:
                logger.info("%sAuthenticated via AppRole (token: permanent)", ns_info)
            else:
                renewal_after = int(ttl * self._renewal_threshold)
                logger.info(
                    "%sAuthenticated via AppRole (TTL: %ds, will renew after: %ds)",
                    ns_info,
                    ttl,
                    renewal_after,
                )
        except httpx.ConnectError:
            # OpenBao is unavailable - this is expected during development
            # or when OpenBao is not yet deployed
            entry = self._tokens.get(cache_key)
            if entry and entry.secret_id == secret_id and entry.expires_at > time.time():
                remaining = entry.expires_at - time.time()
                logger.warning(
                    "OpenBao unavailable, using cached token (%.0fs remaining)",
                    remaining,
                )
                return True

            bao_addr = os.getenv("BAO_ADDR", "unknown")
            logger.warning(
                "OpenBao unavailable at %s, falling back to .env configuration",
                bao_addr,
            )
            self._tokens.pop(cache_key, None)
            return False
        except InvalidPathError as e:
            # Namespace or AppRole path not found
            bao_addr = os.getenv("BAO_ADDR", "unknown")
            logger.warning(
                "OpenBao configuration error at %s: %s. "
                "Check BAO_NAMESPACE and AppRole setup. Falling back to .env",
                bao_addr,
                e,
            )
            self._tokens.pop(cache_key, None)
            return False
        except InvalidRequestError as e:
            # Invalid credentials (role_id/secret_id)
            logger.warning(
                "Invalid AppRole credentials: %s. "
                "Check BAO_APPROLE_ROLE_ID and BAO_APPROLE_SECRET_ID. Falling back to .env",
                e,
            )
            self._tokens.pop(cache_key, None)
            return False
        except ForbiddenError as e:
            # Permission denied
            logger.warning(
                "OpenBao access denied: %s. "
                "Check AppRole permissions. Falling back to .env",
                e,
            )
            self._tokens.pop(cache_key, None)
            return False
        except Exception:
            # Graceful degradation: use existing token only if credentials match
            entry = self._tokens.get(cache_key)
            if entry and entry.secret_id == secret_id and entry.expires_at > time.time():
                remaining = entry.expires_at - time.time()
                logger.warning(
                    "AppRole re-authentication failed, using existing token (%.0fs remaining)",
                    remaining,
                    exc_info=True,
                )
                return True

            logger.exception("AppRole authentication failed")
            # Remove invalid entry
            self._tokens.pop(cache_key, None)
            return False
        else:
            return True

    def invalidate(self, namespace: str | None = None, role_id: str | None = None) -> None:
        """
        Force token renewal on next get_token() call.

        Args:
            namespace: Specific namespace to invalidate (None = all)
            role_id: Specific role_id to invalidate (None = all matching namespace)

        Note:
            If both are None, invalidates all cached tokens.

        """
        with self._token_lock:
            if namespace is None and role_id is None:
                # Invalidate all
                self._tokens.clear()
                logger.debug("All tokens invalidated")
            elif role_id is not None:
                # Invalidate specific key
                cache_key = self._make_cache_key(namespace, role_id)
                if cache_key in self._tokens:
                    del self._tokens[cache_key]
                    logger.debug("Token invalidated for %s", cache_key)
            else:
                # Invalidate all for namespace
                prefix = f"{namespace or ''}:"
                keys_to_remove = [k for k in self._tokens if k.startswith(prefix)]
                for key in keys_to_remove:
                    del self._tokens[key]
                logger.debug("Tokens invalidated for namespace %s (%d tokens)", namespace, len(keys_to_remove))

    def is_healthy(self, namespace: str | None = None, role_id: str | None = None) -> bool:
        """
        Check if token is valid and has reasonable time remaining.

        Args:
            namespace: Namespace to check
            role_id: Role ID to check

        Returns:
            True if token exists and has > MIN_HEALTHY_TOKEN_SECONDS remaining (or is permanent)

        """
        with self._token_lock:
            if role_id is None:
                # Check if any token is healthy
                return any(
                    self._is_entry_healthy(entry)
                    for entry in self._tokens.values()
                )

            cache_key = self._make_cache_key(namespace, role_id)
            entry = self._tokens.get(cache_key)
            return self._is_entry_healthy(entry)

    def _is_entry_healthy(self, entry: TokenEntry | None) -> bool:
        """Check if a token entry is healthy."""
        if not entry:
            return False
        if entry.ttl == 0:
            return True  # Permanent token
        remaining = entry.expires_at - time.time()
        return remaining > MIN_HEALTHY_TOKEN_SECONDS


class OpenBaoSettingsSource(PydanticBaseSettingsSource):
    """
    Custom settings source that reads values from OpenBao.

    Loads data from path kv/{BAO_SECRET_PATH}.
    Data is returned as a flat dictionary with nested objects.

    Environment variables:

    Namespace (for team/tenant isolation):
    - BAO_NAMESPACE: Namespace in OpenBao (e.g.: exam-crm, app)
    - BAO_NAMESPACE_FILE: Path to file with namespace

    AppRole authentication:
    - BAO_APPROLE_ROLE_ID: Role ID for AppRole
    - BAO_APPROLE_ROLE_ID_FILE: Path to file with Role ID
    - BAO_APPROLE_SECRET_ID: Secret ID for AppRole
    - BAO_APPROLE_SECRET_ID_FILE: Path to file with Secret ID

    General:
    - BAO_ADDR: OpenBao server address (e.g., http://localhost:8200)
    - BAO_SECRET_PATH: Path to secrets inside namespace (e.g.: docx-pdf-convert)
    - BAO_MOUNT_POINT: Mount point KV engine (default: kv)
    - BAO_TIMEOUT: Connection timeout in seconds (default: 30)

    Token lifecycle (TokenManager):
    - BAO_TOKEN_RENEWAL_THRESHOLD: When to renew token (default: 0.75 = at 75% of TTL)
    """

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        super().__init__(settings_cls)
        self._data: dict[str, Any] | None = None

        # Source tracking for diagnostics
        self._source: Literal["openbao", "env"] = "env"
        self._source_details: str = ""  # Details about the source (error message, file path, etc.)
        self._openbao_keys_loaded: int = 0  # Number of keys loaded from OpenBao

    def get_source_info(self) -> SourceInfo:
        """
        Get information about the settings source.

        Returns:
            SourceInfo with:
            - status: Whether settings were loaded from OpenBao
            - timestamp: When the check was performed
            - source: "openbao" or "env"
            - details: Human-readable details about the source
            - openbao_keys_loaded: Number of keys loaded from OpenBao (0 if not used)

        """
        return SourceInfo(
            status=self._source == "openbao",
            timestamp=datetime.now(MOSCOW_TZ),
            source=self._source,
            details=self._source_details,
            openbao_keys_loaded=self._openbao_keys_loaded,
        )

    def _get_namespace(self) -> str | None:
        """Get namespace from environment variable or file."""
        # Priority 1: BAO_NAMESPACE environment variable
        namespace = os.getenv("BAO_NAMESPACE")
        if namespace:
            return namespace.strip()

        # Priority 2: BAO_NAMESPACE_FILE file (for Docker)
        namespace_file = os.getenv("BAO_NAMESPACE_FILE")
        if namespace_file:
            namespace_path = Path(namespace_file)
            if namespace_path.exists():
                try:
                    return namespace_path.read_text(encoding="utf-8").strip()
                except OSError as e:
                    logger.warning("Failed to read namespace file %s: %s", namespace_file, e)

        return None

    def _get_client(self) -> OpenBaoClient | None:
        """Create and authenticate OpenBao client."""
        bao_addr = os.getenv("BAO_ADDR")
        if not bao_addr:
            logger.debug("BAO_ADDR not set, skipping OpenBao")
            return None

        timeout = int(os.getenv("BAO_TIMEOUT", "30"))
        namespace = self._get_namespace()

        # Create client with namespace (if specified)
        client = OpenBaoClient(url=bao_addr, timeout=timeout, namespace=namespace)

        if namespace:
            logger.debug("Using namespace: %s", namespace)

        authenticated = self._authenticate_client(client)
        if authenticated:
            return client

        logger.debug("No valid authentication method found")
        return None

    def _authenticate_client(self, client: OpenBaoClient) -> bool:
        """
        Authenticate client via AppRole using TokenManager.

        TokenManager caches the token and handles automatic renewal
        when TTL is approaching expiration.
        """
        role_id = self._read_credential("BAO_APPROLE_ROLE_ID", "BAO_APPROLE_ROLE_ID_FILE")
        secret_id = self._read_credential("BAO_APPROLE_SECRET_ID", "BAO_APPROLE_SECRET_ID_FILE")

        if not role_id or not secret_id:
            logger.debug("AppRole credentials not configured")
            return False

        # Use TokenManager for token lifecycle management
        namespace = self._get_namespace()
        token_manager = TokenManager()
        token = token_manager.get_token(client, role_id, secret_id, namespace)

        if token:
            # Set token on client (needed when token is returned from cache
            # without calling _authenticate, which sets it internally)
            client.token = token
            return True

        return False

    def _read_credential(self, env_var: str, file_env_var: str) -> str | None:
        """Read credential from environment variable or file."""
        # Priority 1: direct value
        value = os.getenv(env_var)
        if value:
            return value.strip()

        # Priority 2: file
        file_path = os.getenv(file_env_var)
        if file_path:
            path = Path(file_path)
            if path.exists():
                try:
                    return path.read_text(encoding="utf-8").strip()
                except OSError as e:
                    logger.warning("Failed to read %s: %s", file_path, e)

        return None

    def _load_from_openbao(self, client: OpenBaoClient, path: str) -> dict[str, Any]:
        """Load secrets from OpenBao at specified path."""
        mount_point = os.getenv("BAO_MOUNT_POINT", "kv")
        namespace = self._get_namespace()
        try:
            response = client.kv_v2_read(path=path, mount_point=mount_point)
            data = response.data.data
            ns_info = f"[{namespace}]" if namespace else ""
            logger.debug("Loaded %d keys from %s%s/%s", len(data), ns_info, mount_point, path)
        except httpx.ConnectError:
            bao_addr = os.getenv("BAO_ADDR", "unknown")
            logger.warning(
                "OpenBao unavailable at %s while loading secrets from %s",
                bao_addr,
                path,
            )
            return {}
        except OpenBaoError as e:
            ns_info = f"[{namespace}]" if namespace else ""
            logger.warning("Failed to load from %s%s/%s: %s", ns_info, mount_point, path, e)
            return {}
        else:
            return data

    def _load_data(self) -> dict[str, Any]:
        """Load all data (with caching)."""
        if self._data is not None:
            return self._data

        bao_addr = os.getenv("BAO_ADDR")

        # Try to load from OpenBao
        client = self._get_client()
        if client:
            base_path = os.getenv("BAO_SECRET_PATH", "")
            if base_path:
                # Read both paths
                secrets = self._load_from_openbao(client, f"{base_path}/secrets")
                supersecrets = self._load_from_openbao(client, f"{base_path}/supersecrets")

                # Validate and log key sources
                self._validate_and_log_keys(secrets, supersecrets)

                # Validate that supersecrets fields use SecretStr
                self._validate_supersecrets_types(supersecrets)

                # Merge (supersecrets has priority for nested dicts)
                self._data = deep_merge(secrets, supersecrets)

                # Track source
                total_keys = len(self._data)
                if total_keys > 0:
                    self._source = "openbao"
                    self._source_details = f"Loaded {total_keys} keys from {base_path}"
                    self._openbao_keys_loaded = total_keys
                else:
                    self._source = "env"
                    self._source_details = "OpenBao returned no secrets, using .env fallback"
                    self._openbao_keys_loaded = 0

                # Update global source info
                self._update_global_source_info()
                return self._data

        # OpenBao not available - fallback to .env
        self._source = "env"
        if bao_addr:
            self._source_details = f"OpenBao at {bao_addr} not available, using .env fallback"
        else:
            self._source_details = "BAO_ADDR not set, using .env configuration"
        self._openbao_keys_loaded = 0
        self._data = {}

        # Update global source info
        self._update_global_source_info()
        return self._data

    def _update_global_source_info(self) -> None:
        """Update the global _last_source_info with current instance data."""
        global _last_source_info  # noqa: PLW0603
        _last_source_info = SourceInfo(
            status=self._source == "openbao",
            timestamp=datetime.now(MOSCOW_TZ),
            source=self._source,
            details=self._source_details,
            openbao_keys_loaded=self._openbao_keys_loaded,
        )

    def _validate_and_log_keys(
        self,
        secrets: dict[str, Any],
        supersecrets: dict[str, Any],
    ) -> None:
        """
        Validate that secrets and supersecrets have compatible keys for merging.

        Allows overlapping keys if BOTH values are dicts (deep_merge will combine them).
        Raises error if overlapping key has non-dict value (would be overwritten).

        Args:
            secrets: Data loaded from secrets path
            supersecrets: Data loaded from supersecrets path

        Raises:
            ValueError: If overlapping keys have non-dict values (merge conflict)

        Logs:
            DEBUG: Lists keys from each source for transparency

        """
        secrets_keys = set(secrets.keys())
        supersecrets_keys = set(supersecrets.keys())

        # Log key sources for transparency
        if secrets_keys:
            logger.debug("Keys from secrets: %s", ", ".join(sorted(secrets_keys)))
        if supersecrets_keys:
            logger.debug("Keys from supersecrets: %s", ", ".join(sorted(supersecrets_keys)))

        # Check for overlapping keys
        overlapping = secrets_keys & supersecrets_keys
        if overlapping:
            # Check each overlapping key - allow if both are dicts (deep_merge handles it)
            conflicts: list[str] = []
            mergeable: list[str] = []

            for key in overlapping:
                secrets_val = secrets[key]
                supersecrets_val = supersecrets[key]

                if isinstance(secrets_val, dict) and isinstance(supersecrets_val, dict):
                    # Both are dicts - deep_merge will combine them
                    mergeable.append(key)
                else:
                    # At least one is not a dict - conflict (value would be overwritten)
                    conflicts.append(key)

            if mergeable:
                logger.debug(
                    "Keys [%s] exist in both but will be deep-merged (both are dicts)",
                    ", ".join(sorted(mergeable)),
                )

            if conflicts:
                conflicts_list = ", ".join(sorted(conflicts))
                msg = (
                    f"Configuration error: keys [{conflicts_list}] exist in both "
                    "secrets and supersecrets with non-dict values. "
                    "Cannot merge - supersecrets would overwrite secrets. "
                    "Move these keys to either secrets OR supersecrets, not both."
                )
                logger.error(msg)
                raise ValueError(msg)

        # Log summary
        unique_secrets = len(secrets_keys - supersecrets_keys)
        unique_supersecrets = len(supersecrets_keys - secrets_keys)
        merged_keys = len(overlapping) if overlapping else 0
        logger.debug(
            "Key validation passed: %d unique from secrets, %d unique from supersecrets, "
            "%d merged keys",
            unique_secrets,
            unique_supersecrets,
            merged_keys,
        )

    def _validate_supersecrets_types(self, supersecrets: dict[str, Any]) -> None:
        """
        Validate that supersecrets fields use SecretStr in Pydantic models.

        This is a security check to prevent accidental exposure of sensitive data
        in logs, repr, or JSON serialization. All string fields loaded from
        supersecrets path MUST use SecretStr type annotation.

        Args:
            supersecrets: Data loaded from supersecrets path

        Raises:
            TypeError: If any string field from supersecrets doesn't use SecretStr

        Example error::

            TypeError: Security misconfiguration: fields from supersecrets must use
            SecretStr type to prevent accidental exposure in logs.

            Affected fields:
              - token.key: currently 'str', should be 'SecretStr'
              - token.secret: currently 'str', should be 'SecretStr'

            Fix your Pydantic model:
              class TokenConfig(BaseModel):
                  key: SecretStr = Field(...)  # not 'str'

        """
        if not supersecrets:
            return

        all_violations: list[str] = []

        for key, value in supersecrets.items():
            field_info = self.settings_cls.model_fields.get(key)
            if not field_info:
                continue

            annotation = field_info.annotation

            # Check if it's a nested model (dict)
            nested_model = _get_model_from_annotation(annotation)
            if nested_model is not None and isinstance(value, dict):
                violations = _collect_non_secret_str_fields(
                    nested_model,
                    value,
                    f"{key}.",
                )
                all_violations.extend(violations)

            # Check if it's a list (list[Model] or list[str])
            elif isinstance(value, list):
                is_list_of_models, list_model = _is_list_of_models(annotation)
                if is_list_of_models and list_model is not None:
                    # Check each element in list[Model]
                    for idx, item in enumerate(value):
                        if isinstance(item, dict):
                            violations = _collect_non_secret_str_fields(
                                list_model,
                                item,
                                f"{key}[{idx}].",
                            )
                            all_violations.extend(violations)
                elif (
                    value
                    and isinstance(value[0], str)
                    and not _is_secret_str_type(annotation)
                ):
                    # list[str] - must be list[SecretStr]
                    all_violations.append(key)

            # Check if it's a top-level string field
            elif isinstance(value, str) and not _is_secret_str_type(annotation):
                all_violations.append(key)

        if all_violations:
            fields_list = "\n".join(f"  - {field}" for field in sorted(all_violations))
            msg = (
                "Security misconfiguration: fields from supersecrets must use "
                "SecretStr type to prevent accidental exposure in logs.\n\n"
                f"Affected fields:\n{fields_list}\n\n"
                "Fix your Pydantic model:\n"
                "  class YourModel(BaseModel):\n"
                "      field: SecretStr = Field(...)  # not 'str'"
            )
            logger.error(msg)
            raise SecurityMisconfigurationError(msg)

        if supersecrets:
            logger.debug(
                "Supersecrets type validation passed: %d top-level keys checked",
                len(supersecrets),
            )

    def reload(self) -> dict[str, Any]:
        """
        Force reload secrets from OpenBao.

        Use this method when secrets have been updated in OpenBao
        and you need to refresh the cached data without restarting.

        Returns:
            Reloaded data dictionary

        Example::

            source = OpenBaoSettingsSource(Settings)
            source.reload()  # Clears cache and reloads from OpenBao

        """
        self._data = None
        logger.debug("Data cache invalidated, will reload on next access")
        return self._load_data()

    def invalidate(self, *, invalidate_tokens: bool = True) -> None:
        """
        Invalidate cached data and optionally tokens.

        Use this method when you need to clear all caches and force
        fresh data on next access.

        Args:
            invalidate_tokens: If True, also invalidate TokenManager cache.
                              If False, only invalidate data cache.

        Example::

            source = OpenBaoSettingsSource(Settings)

            # Invalidate both data and token cache
            source.invalidate()

            # Invalidate data cache only (keep tokens)
            source.invalidate(invalidate_tokens=False)

        """
        self._data = None
        logger.debug("Data cache invalidated")

        if invalidate_tokens:
            # Invalidate tokens for current namespace
            namespace = self._get_namespace()
            TokenManager().invalidate(namespace=namespace)
            logger.debug("Token cache invalidated for namespace: %s", namespace or "root")

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:  # noqa: ARG002
        """
        Get field value from loaded data.

        Returns:
            Tuple (value, field_name, is_complex).
            pydantic automatically converts string to SecretStr.

        """
        data = self._load_data()
        value = data.get(field_name)

        if value is not None:
            # If value is dict, it's a nested model
            is_complex = isinstance(value, dict)
            return value, field_name, is_complex

        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        """
        Return all data as dictionary.

        Called by pydantic-settings to get all values.
        """
        data = self._load_data()

        result = {}
        for field_name, field_info in self.settings_cls.model_fields.items():
            # Try field name first
            value = data.get(field_name)
            # If not found, try alias (for fields like hash_config with alias="hash")
            if value is None and field_info.alias:
                value = data.get(field_info.alias)
            if value is not None:
                result[field_name] = value

        return result
