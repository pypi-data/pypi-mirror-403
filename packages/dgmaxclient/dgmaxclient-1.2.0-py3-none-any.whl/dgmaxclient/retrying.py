"""
Retry logic for the DGMax client.

This module provides retry decorators for handling transient failures
when making requests to the DGMax API.
"""

from __future__ import annotations

import logging

import tenacity
from tenacity import RetryCallState

from dgmaxclient.exceptions import (
    DGMaxConnectionError,
    DGMaxRateLimitError,
    DGMaxServerError,
    DGMaxTimeoutError,
)

logger = logging.getLogger(__name__)

MAX_RETRY_ATTEMPTS = 3

# Default exponential backoff wait strategy
_default_wait = tenacity.wait_exponential(
    multiplier=2, min=2, max=60
) + tenacity.wait_random(0, 2)


def _should_retry(exc: BaseException) -> bool:
    """Determine if an exception should trigger a retry.

    Args:
        exc: The exception that occurred

    Returns:
        True if the request should be retried
    """
    # Retry on server errors (5xx)
    if isinstance(exc, DGMaxServerError):
        return True

    # Retry on network errors
    if isinstance(exc, (DGMaxTimeoutError, DGMaxConnectionError)):
        return True

    # Retry on rate limit errors (429) - will respect Retry-After header
    return isinstance(exc, DGMaxRateLimitError)


def _wait_for_retry(retry_state: RetryCallState) -> float:
    """Calculate wait time, respecting Retry-After header for rate limits.

    Args:
        retry_state: The current retry state

    Returns:
        Number of seconds to wait before retrying
    """
    if retry_state.outcome:
        exc = retry_state.outcome.exception()
        # If rate limited with Retry-After header, use that value
        if isinstance(exc, DGMaxRateLimitError) and exc.retry_after:
            wait_time = float(exc.retry_after)
            logger.info(
                "Rate limited, waiting %d seconds (Retry-After header)", exc.retry_after
            )
            return wait_time

    # Otherwise use default exponential backoff
    return _default_wait(retry_state)


def _log_retry_attempt(retry_state: RetryCallState) -> None:
    """Log retry attempts for observability.

    Args:
        retry_state: The current retry state
    """
    error_name = "Unknown"
    if retry_state.outcome and hasattr(retry_state.outcome, "exception"):
        exc = retry_state.outcome.exception()
        if exc:
            error_name = exc.__class__.__name__

    logger.warning(
        "DGMax retry attempt %d/%d due to %s",
        retry_state.attempt_number,
        MAX_RETRY_ATTEMPTS,
        error_name,
    )


# Retry decorator for DGMax API requests
retry_request = tenacity.retry(
    retry=tenacity.retry_if_exception(_should_retry),
    wait=_wait_for_retry,
    stop=tenacity.stop_after_attempt(MAX_RETRY_ATTEMPTS),
    before_sleep=_log_retry_attempt,
    reraise=True,
)
