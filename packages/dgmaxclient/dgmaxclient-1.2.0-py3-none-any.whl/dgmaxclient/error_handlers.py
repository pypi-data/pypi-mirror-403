"""
Error handlers for the DGMax client.

This module provides error handling logic for HTTP responses
and network exceptions.
"""

from __future__ import annotations

import logging
import socket

from apiclient import exceptions
from apiclient.error_handlers import ErrorHandler
from apiclient.response import Response
from requests.exceptions import ConnectionError, RequestException, Timeout
from urllib3.exceptions import (
    ConnectTimeoutError,
    NameResolutionError,
    NewConnectionError,
    ProtocolError,
    ReadTimeoutError,
)
from urllib3.exceptions import TimeoutError as Urllib3TimeoutError

from dgmaxclient.exceptions import (
    DGMaxAuthenticationError,
    DGMaxConnectionError,
    DGMaxRateLimitError,
    DGMaxRequestError,
    DGMaxServerError,
    DGMaxTimeoutError,
    DGMaxValidationError,
)

logger = logging.getLogger(__name__)


class DGMaxErrorHandler(ErrorHandler):
    """Error handler for DGMax client following apiclient strategy pattern.

    This error handler maps HTTP status codes to appropriate DGMax
    exceptions and handles network-level errors.
    """

    TIMEOUT_EXCEPTIONS = (
        Timeout,
        socket.timeout,
        ConnectTimeoutError,
        ReadTimeoutError,
        Urllib3TimeoutError,
        TimeoutError,
    )

    CONNECTION_EXCEPTIONS = (
        NameResolutionError,
        NewConnectionError,
        ConnectionError,
        socket.gaierror,
        ProtocolError,
    )

    RETRYABLE_NETWORK_EXCEPTIONS = (
        *TIMEOUT_EXCEPTIONS,
        *CONNECTION_EXCEPTIONS,
        RequestException,
        OSError,
    )

    @staticmethod
    def is_timeout_exception(exc: Exception) -> bool:
        """Check if exception is a timeout-related error.

        Args:
            exc: The exception to check

        Returns:
            True if the exception is timeout-related
        """
        return isinstance(exc, DGMaxErrorHandler.TIMEOUT_EXCEPTIONS)

    @staticmethod
    def is_connection_exception(exc: Exception) -> bool:
        """Check if exception is a connection-related error.

        Note: This must be checked BEFORE is_timeout_exception because
        urllib3's NameResolutionError and NewConnectionError inherit from
        ConnectTimeoutError -> TimeoutError, but they are connection errors.

        Args:
            exc: The exception to check

        Returns:
            True if the exception is connection-related
        """
        return isinstance(exc, DGMaxErrorHandler.CONNECTION_EXCEPTIONS)

    @staticmethod
    def get_exception(response: Response) -> exceptions.APIRequestError:
        """Get the appropriate exception for an HTTP response.

        Maps HTTP status codes to DGMax exception types:
        - 401, 403: DGMaxAuthenticationError
        - 422: DGMaxValidationError
        - 429: DGMaxRateLimitError
        - 4xx: DGMaxRequestError
        - 5xx: DGMaxServerError

        Args:
            response: The HTTP response object

        Returns:
            An appropriate exception instance
        """
        status_code = response.get_status_code()
        url = response.get_requested_url()
        raw_data = response.get_raw_data()
        reason = response.get_status_reason()

        message = f"{status_code} Error: {reason} for url: {url}"

        if status_code == 401 or status_code == 403:
            return DGMaxAuthenticationError(
                message=message,
                info=raw_data,
                status_code=status_code,
            )

        if status_code == 422:
            return DGMaxValidationError(
                message=message,
                info=raw_data,
                status_code=status_code,
            )

        if status_code == 429:
            retry_after = None
            # Try to extract retry-after from response headers if available
            try:
                # The Response object wraps requests.Response which has headers
                if hasattr(response, "_response") and hasattr(
                    response._response, "headers"
                ):
                    retry_header = response._response.headers.get("Retry-After")
                    if retry_header:
                        retry_after = int(retry_header)
            except (ValueError, AttributeError):
                pass
            return DGMaxRateLimitError(
                message=message,
                retry_after=retry_after,
                info=raw_data,
            )

        if 400 <= status_code < 500:
            return DGMaxRequestError(
                message=message,
                status_code=status_code,
                info=raw_data,
            )

        if 500 <= status_code < 600:
            return DGMaxServerError(
                message=message,
                status_code=status_code,
                info=raw_data,
            )

        return exceptions.UnexpectedError(
            message=message,
            status_code=status_code,
            info=raw_data,
        )

    @staticmethod
    def is_retryable_network_exception(exc: Exception) -> bool:
        """Check if an exception is a retryable network error.

        Args:
            exc: Exception to check

        Returns:
            True if exception should trigger retry logic
        """
        return isinstance(exc, DGMaxErrorHandler.RETRYABLE_NETWORK_EXCEPTIONS)

    @staticmethod
    def wrap_transport_error(exc: Exception, endpoint: str) -> None:
        """Wrap transport exception in DGMax-specific exception and raise it.

        This method converts network-level exceptions to DGMax exceptions.
        Connection exceptions are checked BEFORE timeouts because
        urllib3's NameResolutionError and NewConnectionError inherit from
        ConnectTimeoutError -> TimeoutError, but they are connection errors.

        Args:
            exc: The transport exception that occurred
            endpoint: The endpoint URL that was being contacted

        Raises:
            DGMaxConnectionError: For connection-related network errors
            DGMaxTimeoutError: For timeout-related network errors
            UnexpectedError: For other unexpected errors
        """
        if DGMaxErrorHandler.is_connection_exception(exc):
            raise DGMaxConnectionError(
                message=f"Connection error for '{endpoint}': {exc}"
            ) from exc

        if DGMaxErrorHandler.is_timeout_exception(exc):
            raise DGMaxTimeoutError(
                message=f"Request timeout for '{endpoint}': {exc}"
            ) from exc

        raise exceptions.UnexpectedError(f"Error when contacting '{endpoint}'") from exc
