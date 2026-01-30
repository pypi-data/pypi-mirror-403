"""Pydantic models for OpenBao API response validation."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from typing import Any, Literal

from pydantic import BaseModel, Field


# ===== Exceptions =====


class OpenBaoError(Exception):
    """
    Base exception for all OpenBao-related errors.

    All specific OpenBao exceptions inherit from this class,
    allowing you to catch all OpenBao errors with a single except clause.

    Example:
        try:
            client.kv_v2_read("path/to/secret")
        except OpenBaoError as e:
            logger.error("OpenBao operation failed: %s", e)

    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """
        Initialize OpenBaoError.

        Args:
            message: Human-readable error description
            status_code: HTTP status code that caused the error (if applicable)

        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        """Return error message with status code if available."""
        if self.status_code:
            return f"[HTTP {self.status_code}] {self.message}"
        return self.message


class InvalidPathError(OpenBaoError):
    """
    Path not found in OpenBao (HTTP 404).

    This error occurs when:
    - The secret path does not exist
    - The mount point is incorrect
    - The namespace does not exist or is misspelled

    Example:
        try:
            client.kv_v2_read("nonexistent/path")
        except InvalidPathError as e:
            logger.warning("Secret not found: %s", e)

    """

    def __init__(self, message: str) -> None:
        """Initialize InvalidPathError with HTTP 404 status."""
        super().__init__(message, status_code=HTTPStatus.NOT_FOUND)


class InvalidRequestError(OpenBaoError):
    """
    Invalid request parameters (HTTP 400).

    This error occurs when:
    - AppRole credentials (role_id/secret_id) are invalid
    - Request body has incorrect format
    - Required parameters are missing

    Example:
        try:
            client.approle_login(role_id="invalid", secret_id="wrong")
        except InvalidRequestError as e:
            logger.error("Invalid credentials: %s", e)

    """

    def __init__(self, message: str) -> None:
        """Initialize InvalidRequestError with HTTP 400 status."""
        super().__init__(message, status_code=HTTPStatus.BAD_REQUEST)


class ForbiddenError(OpenBaoError):
    """
    Access denied by OpenBao (HTTP 403).

    This error occurs when:
    - Token lacks required permissions (policy)
    - Token has expired
    - IP address is not in allowed list

    Example:
        try:
            client.kv_v2_read("admin/secrets")
        except ForbiddenError as e:
            logger.error("Access denied: %s", e)

    """

    def __init__(self, message: str) -> None:
        """Initialize ForbiddenError with HTTP 403 status."""
        super().__init__(message, status_code=HTTPStatus.FORBIDDEN)


class InvalidResponseError(OpenBaoError):
    """
    Response validation failed - unexpected structure from OpenBao.

    This error occurs when:
    - OpenBao returns a response that doesn't match expected Pydantic model
    - Required fields are missing in the response
    - Field types don't match (e.g., string instead of int)

    This typically indicates:
    - OpenBao version incompatibility
    - Custom OpenBao plugin with non-standard response
    - Network/proxy corruption of response

    Example:
        try:
            response = client.approle_login(role_id, secret_id)
        except InvalidResponseError as e:
            logger.error("Unexpected API response: %s", e)

    """

    def __init__(self, message: str) -> None:
        """Initialize InvalidResponseError (no HTTP status - validation error)."""
        super().__init__(message, status_code=None)


class SecurityMisconfigurationError(OpenBaoError):
    """
    Security misconfiguration detected in Pydantic model.

    This error occurs when fields from supersecrets path are not
    properly typed with SecretStr in Pydantic models, which could
    lead to accidental exposure of sensitive data in logs.

    Example:
        # Wrong - will raise SecurityMisconfigurationError
        class TokenConfig(BaseModel):
            key: str  # ← Should be SecretStr!

        # Correct
        class TokenConfig(BaseModel):
            key: SecretStr  # ← Properly protected

    """

    def __init__(self, message: str) -> None:
        """Initialize SecurityMisconfigurationError with HTTP 422 status."""
        super().__init__(message, status_code=HTTPStatus.UNPROCESSABLE_ENTITY)


# ===== AppRole Login Response Models =====


class AuthInfo(BaseModel):
    """Validated auth block from AppRole login response."""

    client_token: str = Field(..., min_length=1)
    """Token for subsequent API requests."""

    lease_duration: int = Field(..., ge=0)
    """Token TTL in seconds. 0 = permanent token."""

    renewable: bool = False
    """Whether token can be renewed."""

    accessor: str | None = None
    """Token accessor for management operations."""

    policies: list[str] = []
    """Policies attached to this token."""

    token_type: str | None = None
    """Type of token (service, batch, etc.)."""


class AppRoleLoginResponse(BaseModel):
    """Validated response from POST /v1/auth/approle/login."""

    auth: AuthInfo
    """Authentication information with token."""

    request_id: str | None = None
    """Unique request identifier for debugging."""

    warnings: list[str] | None = None
    """Any warnings from the server."""


# ===== KV v2 Read Response Models =====


class SecretDataWrapper(BaseModel):
    """Inner data wrapper for KV v2 secrets."""

    data: dict[str, Any]
    """Actual secret key-value pairs."""

    metadata: dict[str, Any] | None = None
    """Secret metadata (version, created_time, etc.)."""


class KvV2ReadResponse(BaseModel):
    """Validated response from GET /v1/{mount}/data/{path}."""

    data: SecretDataWrapper
    """Secret data wrapper."""

    request_id: str | None = None
    """Unique request identifier."""

    lease_id: str = ""
    """Lease ID if applicable."""

    warnings: list[str] | None = None
    """Any warnings from the server."""


# ===== Source Info Model =====


class SourceInfo(BaseModel):
    """
    Standardized source information for API responses.

    This model provides a consistent format for reporting where settings
    were loaded from, compatible with health-check patterns used across services.

    Example response:
        {
            "status": true,
            "timestamp": "2026-01-24T14:30:45.123Z",
            "source": "openbao",
            "details": "Loaded 6 keys from docx-pdf-convert",
            "openbao_keys_loaded": 6
        }

    """

    status: bool
    """Whether settings were successfully loaded from OpenBao."""

    timestamp: datetime
    """When the source check was performed."""

    source: Literal["openbao", "env"]
    """Where settings were loaded from: 'openbao' or 'env' (fallback)."""

    details: str
    """Human-readable description of the source."""

    openbao_keys_loaded: int = 0
    """Number of keys loaded from OpenBao (0 if using env fallback)."""
