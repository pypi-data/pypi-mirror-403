"""Unit tests for DGMax exceptions."""

from __future__ import annotations

import json

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


class TestDGMaxError:
    """Tests for the base DGMaxError exception."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = DGMaxError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.info == ""
        assert error.response is None

    def test_error_with_info(self) -> None:
        """Test error with info string."""
        error = DGMaxError("Error occurred", info="Additional info")

        assert error.info == "Additional info"
        assert error.response is None

    def test_error_with_json_info(self) -> None:
        """Test error with JSON info."""
        info = json.dumps({"detail": "Not found", "code": 404})
        error = DGMaxError("Error occurred", info=info)

        assert error.response == {"detail": "Not found", "code": 404}

    def test_error_with_invalid_json_info(self) -> None:
        """Test error with invalid JSON info."""
        error = DGMaxError("Error occurred", info="not valid json")

        assert error.response is None


class TestDGMaxAuthenticationError:
    """Tests for DGMaxAuthenticationError."""

    def test_basic_auth_error(self) -> None:
        """Test basic authentication error."""
        error = DGMaxAuthenticationError("Invalid API key")

        assert "Invalid API key" in str(error)
        assert error.status_code is None

    def test_auth_error_with_status(self) -> None:
        """Test authentication error with status code."""
        error = DGMaxAuthenticationError(
            "Unauthorized",
            status_code=401,
        )

        assert "Unauthorized" in str(error)
        assert "401" in str(error)
        assert error.status_code == 401

    def test_auth_error_str_format(self) -> None:
        """Test authentication error string formatting."""
        error = DGMaxAuthenticationError(
            "Access denied",
            status_code=403,
        )

        expected = "Access denied | Status: 403"
        assert str(error) == expected


class TestDGMaxValidationError:
    """Tests for DGMaxValidationError."""

    def test_validation_error(self) -> None:
        """Test validation error."""
        error = DGMaxValidationError("Validation failed")

        assert error.status_code == 422

    def test_validation_error_with_info(self) -> None:
        """Test validation error with details."""
        info = json.dumps({"detail": [{"loc": ["body", "rnc"], "msg": "Required"}]})
        error = DGMaxValidationError("Validation failed", info=info)

        assert error.response is not None
        assert "detail" in error.response


class TestDGMaxRequestError:
    """Tests for DGMaxRequestError."""

    def test_request_error(self) -> None:
        """Test request error."""
        error = DGMaxRequestError("Bad request", status_code=400)

        assert error.status_code == 400
        assert "Bad request" in str(error)
        assert "400" in str(error)


class TestDGMaxServerError:
    """Tests for DGMaxServerError."""

    def test_server_error(self) -> None:
        """Test server error."""
        error = DGMaxServerError("Internal server error", status_code=500)

        assert error.status_code == 500
        assert "Internal server error" in str(error)
        assert "500" in str(error)


class TestDGMaxTimeoutError:
    """Tests for DGMaxTimeoutError."""

    def test_timeout_error(self) -> None:
        """Test timeout error."""
        error = DGMaxTimeoutError("Request timed out")

        assert error.message == "Request timed out"


class TestDGMaxConnectionError:
    """Tests for DGMaxConnectionError."""

    def test_connection_error(self) -> None:
        """Test connection error."""
        error = DGMaxConnectionError("Connection refused")

        assert error.message == "Connection refused"


class TestDGMaxRateLimitError:
    """Tests for DGMaxRateLimitError."""

    def test_rate_limit_error(self) -> None:
        """Test rate limit error."""
        error = DGMaxRateLimitError("Too many requests")

        assert error.status_code == 429
        assert error.retry_after is None

    def test_rate_limit_error_with_retry(self) -> None:
        """Test rate limit error with retry-after."""
        error = DGMaxRateLimitError("Too many requests", retry_after=60)

        assert error.retry_after == 60
        assert "60s" in str(error)
