"""
Request strategies for the DGMax client.

This module provides custom request handling logic for the DGMax API.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from apiclient.request_strategies import RequestStrategy
from apiclient.response import RequestsResponse, Response
from apiclient.utils.typing import OptionalDict

from dgmaxclient.exceptions import (
    DGMaxAuthenticationError,
    DGMaxConnectionError,
    DGMaxError,
    DGMaxRateLimitError,
    DGMaxRequestError,
    DGMaxServerError,
    DGMaxTimeoutError,
    DGMaxValidationError,
)


class DGMaxRequestStrategy(RequestStrategy):
    """Request strategy for DGMax client following ApiClient patterns.

    This strategy delegates exception creation to the error handler,
    mirroring how _handle_bad_response delegates to get_exception().
    """

    def _make_request(
        self,
        request_method: Callable[..., Any],
        endpoint: str,
        params: OptionalDict = None,
        headers: OptionalDict = None,
        data: OptionalDict = None,
        **kwargs: Any,
    ) -> Response:
        """Make the request with the given method.

        Delegates response parsing to the response handler.

        Args:
            request_method: The HTTP method to use
            endpoint: The endpoint URL
            params: Query parameters
            headers: Request headers
            data: Request body data
            **kwargs: Additional arguments (files, json, etc.)

        Returns:
            The decoded response data
        """
        try:
            response = RequestsResponse(
                request_method(
                    endpoint,
                    params=self._get_request_params(params),
                    headers=self._get_request_headers(headers),
                    auth=self._get_username_password_authentication(),
                    data=self._get_formatted_data(data),
                    timeout=self._get_request_timeout(),
                    **kwargs,
                )
            )
        except Exception as error:
            self._handle_request_error(error, endpoint)
        else:
            self._check_response(response)
        return self._decode_response_data(response)

    def _handle_request_error(self, error: Exception, endpoint: str) -> None:
        """Handle transport errors by delegating to the error handler.

        Follows the ApiClient pattern where _handle_bad_response delegates
        to self.get_client().get_error_handler().get_exception(response).
        Similarly, this method delegates transport errors to wrap_transport_error.

        DGMax exceptions are preserved unchanged to maintain error semantics.

        Args:
            error: The exception that occurred during request
            endpoint: The endpoint URL that was being contacted

        Raises:
            DGMaxConnectionError: For connection-related network errors
            DGMaxTimeoutError: For timeout-related network errors
            Original DGMax exception: If already a DGMax exception type
            UnexpectedError: For truly unexpected errors
        """
        # Preserve existing DGMax exceptions
        if isinstance(
            error,
            (
                DGMaxError,
                DGMaxAuthenticationError,
                DGMaxValidationError,
                DGMaxRequestError,
                DGMaxServerError,
                DGMaxTimeoutError,
                DGMaxConnectionError,
                DGMaxRateLimitError,
            ),
        ):
            raise error

        # Delegate to error handler for network errors
        self.get_client().get_error_handler().wrap_transport_error(error, endpoint)
