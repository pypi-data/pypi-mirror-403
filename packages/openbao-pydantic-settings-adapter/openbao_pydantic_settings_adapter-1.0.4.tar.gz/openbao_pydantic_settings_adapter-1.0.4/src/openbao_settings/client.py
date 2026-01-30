"""Minimal OpenBao HTTP client with Pydantic validation."""

from __future__ import annotations

import logging
import httpx
from http import HTTPStatus

from pydantic import ValidationError

from .models import (
    AppRoleLoginResponse,
    ForbiddenError,
    InvalidPathError,
    InvalidRequestError,
    InvalidResponseError,
    KvV2ReadResponse,
    OpenBaoError,
)

logger = logging.getLogger(__name__)


class OpenBaoClient:
    """
    Minimal OpenBao HTTP client with Pydantic validation.

    Features:
    - Pure httpx-based HTTP client (sync)
    - Pydantic validation of all API responses
    - Automatic header injection (token, namespace)
    - Typed exceptions for error handling
    """

    def __init__(
        self,
        url: str,
        timeout: int = 30,
        namespace: str | None = None,
    ) -> None:
        """
        Initialize OpenBao client.

        Args:
            url: OpenBao server URL (e.g., http://localhost:8200)
            timeout: Request timeout in seconds
            namespace: OpenBao namespace for isolation

        """
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.namespace = namespace
        self.token: str | None = None
        self._client = httpx.Client(timeout=timeout)

    def _headers(self) -> dict[str, str]:
        """Build request headers with token and namespace."""
        headers: dict[str, str] = {}
        if self.token:
            headers["X-Vault-Token"] = self.token
        if self.namespace:
            headers["X-Vault-Namespace"] = self.namespace
        return headers

    def _handle_http_error(self, response: httpx.Response) -> None:
        """Raise appropriate exception based on HTTP status code."""
        if response.status_code == HTTPStatus.NOT_FOUND:
            msg = f"Path not found: {response.text}"
            raise InvalidPathError(msg)
        if response.status_code == HTTPStatus.BAD_REQUEST:
            msg = f"Invalid request: {response.text}"
            raise InvalidRequestError(msg)
        if response.status_code == HTTPStatus.FORBIDDEN:
            msg = f"Access denied: {response.text}"
            raise ForbiddenError(msg)
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise OpenBaoError(response.text, status_code=response.status_code)

    def approle_login(
        self,
        role_id: str,
        secret_id: str,
        mount_point: str = "approle",
    ) -> AppRoleLoginResponse:
        """
        Authenticate via AppRole method.

        Args:
            role_id: AppRole role ID
            secret_id: AppRole secret ID
            mount_point: AppRole auth method mount point (default: "approle")

        Returns:
            Validated AppRoleLoginResponse with auth.client_token

        Raises:
            InvalidPathError: AppRole path not found (check namespace)
            InvalidRequestError: Invalid credentials
            ForbiddenError: Permission denied
            InvalidResponseError: Unexpected response structure

        """
        url = f"{self.url}/v1/auth/{mount_point}/login"
        headers = self._headers()
        # Log request details for debugging
        logger.info(
            "AppRole login: POST %s (namespace: %s, role_id len: %d, secret_id len: %d)",
            url,
            self.namespace or "none",
            len(role_id) if role_id else 0,
            len(secret_id) if secret_id else 0,
        )
        logger.info("Request headers: %s", headers)

        response = self._client.post(
            url,
            json={"role_id": role_id, "secret_id": secret_id},
            headers=headers,
        )
        logger.info("AppRole response: %d %s", response.status_code, response.reason_phrase)
        self._handle_http_error(response)

        try:
            return AppRoleLoginResponse.model_validate(response.json())
        except ValidationError as e:
            msg = f"Unexpected AppRole login response structure: {e}"
            raise InvalidResponseError(msg) from e

    def kv_v2_read(self, path: str, mount_point: str = "kv") -> KvV2ReadResponse:
        """
        Read secret from KV v2 secrets engine.

        Args:
            path: Secret path (e.g., "myapp/config")
            mount_point: KV engine mount point (default: "kv")

        Returns:
            Validated KvV2ReadResponse with data.data containing secrets

        Raises:
            InvalidPathError: Secret path not found
            ForbiddenError: Permission denied
            InvalidResponseError: Unexpected response structure

        """
        url = f"{self.url}/v1/{mount_point}/data/{path}"
        headers = self._headers()
        logger.info(
            "KV read: GET %s (token: %s, namespace: %s)",
            url,
            "set" if self.token else "NOT SET",
            self.namespace or "none",
        )

        response = self._client.get(url, headers=headers)
        logger.info("KV response: %d %s", response.status_code, response.reason_phrase)

        self._handle_http_error(response)

        try:
            return KvV2ReadResponse.model_validate(response.json())
        except ValidationError as e:
            logger.warning("Response body: %s", response.text[:500])
            msg = f"Unexpected KV v2 read response structure: {e}"
            raise InvalidResponseError(msg) from e
