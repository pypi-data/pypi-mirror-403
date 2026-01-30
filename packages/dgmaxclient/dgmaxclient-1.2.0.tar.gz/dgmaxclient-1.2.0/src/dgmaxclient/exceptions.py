"""
Custom exceptions for the DGMax client.

This module provides a comprehensive exception hierarchy for handling
various error scenarios when interacting with the DGMax API.
"""

from __future__ import annotations

import json
from typing import Any


class DGMaxError(Exception):
    """Base exception for DGMax client errors.

    All DGMax-specific exceptions inherit from this class.

    Attributes:
        message: Human-readable error message
        info: Raw response data or additional context

    Examples:
        >>> try:
        ...     client.invoices.create(data)
        ... except DGMaxError as e:
        ...     print(f"Error: {e.message}")
        ...     if e.response:
        ...         print(f"Response: {e.response}")
    """

    def __init__(self, message: str, info: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.info = info

    def __str__(self) -> str:
        return self.message

    @property
    def response(self) -> dict[str, Any] | None:
        """Parse info as JSON for structured access.

        Returns:
            Parsed JSON dict, or None if info is empty or invalid JSON.
        """
        if not self.info:
            return None
        try:
            return json.loads(self.info)
        except (json.JSONDecodeError, ValueError):
            return None


class DGMaxAuthenticationError(DGMaxError):
    """Raised when authentication with DGMax fails.

    This exception indicates that the API key is invalid, expired,
    or missing required permissions.

    Attributes:
        message: Human-readable error message
        info: Raw response data
        status_code: HTTP status code (typically 401 or 403)

    Examples:
        >>> try:
        ...     client = DGMaxClient(api_key="invalid_key")
        ...     client.companies.list()
        ... except DGMaxAuthenticationError as e:
        ...     print(f"Auth failed: {e.message}")
        ...     print(f"Status: {e.status_code}")
    """

    def __init__(
        self,
        message: str,
        info: str = "",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, info)
        self.status_code = status_code

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        return " | ".join(parts)


class DGMaxValidationError(DGMaxError):
    """Raised when request validation fails.

    This exception is raised when the request payload doesn't meet
    the API's validation requirements (HTTP 422).

    Attributes:
        message: Human-readable error message
        info: Detailed validation error information
        status_code: HTTP status code (typically 422)

    Examples:
        >>> try:
        ...     client.invoices.create({"invalid": "data"})
        ... except DGMaxValidationError as e:
        ...     print(f"Validation error: {e.message}")
        ...     if e.response:
        ...         print(f"Details: {e.response}")
    """

    def __init__(
        self,
        message: str,
        info: str = "",
        status_code: int = 422,
    ) -> None:
        super().__init__(message, info)
        self.status_code = status_code


class DGMaxRequestError(DGMaxError):
    """Raised when a request to DGMax fails.

    This exception covers general API request failures,
    typically 4xx errors other than authentication and validation.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code
        info: Raw response data
    """

    def __init__(self, message: str, status_code: int, info: str = "") -> None:
        super().__init__(message, info)
        self.status_code = status_code

    def __str__(self) -> str:
        return f"{self.message} | Status: {self.status_code}"


class DGMaxServerError(DGMaxError):
    """Raised when the DGMax server returns a 5xx error.

    This exception indicates a server-side problem that may be
    temporary. The retry mechanism may automatically retry requests
    that fail with this exception.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (5xx)
        info: Raw response data
    """

    def __init__(self, message: str, status_code: int, info: str = "") -> None:
        super().__init__(message, info)
        self.status_code = status_code

    def __str__(self) -> str:
        return f"{self.message} | Status: {self.status_code}"


class DGMaxTimeoutError(DGMaxError):
    """Raised when a request to DGMax times out.

    This exception indicates that the request took longer than
    the configured timeout period.

    Examples:
        >>> try:
        ...     client.invoices.create(data)
        ... except DGMaxTimeoutError as e:
        ...     print("Request timed out, please try again")
    """

    pass


class DGMaxConnectionError(DGMaxError):
    """Raised when there's a connection error with DGMax services.

    This exception indicates network-level issues such as DNS
    resolution failures, connection refused, or network unreachable.

    Examples:
        >>> try:
        ...     client.invoices.create(data)
        ... except DGMaxConnectionError as e:
        ...     print("Connection failed, check your network")
    """

    pass


class DGMaxRateLimitError(DGMaxError):
    """Raised when rate limits are exceeded.

    This exception is raised when the API returns HTTP 429,
    indicating too many requests in a given time period.

    Attributes:
        message: Human-readable error message
        retry_after: Seconds to wait before retrying (if provided)
        info: Raw response data
    """

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        info: str = "",
    ) -> None:
        super().__init__(message, info)
        self.retry_after = retry_after
        self.status_code = 429

    def __str__(self) -> str:
        parts = [self.message]
        if self.retry_after:
            parts.append(f"Retry after: {self.retry_after}s")
        return " | ".join(parts)
