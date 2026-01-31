"""Retry utilities using tenacity."""

import logging
from typing import Tuple, Type

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ibm_watsonx_ai_120b.config import get_config

logger = logging.getLogger(__name__)


def create_retry_decorator(
    max_attempts: int | None = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    min_wait: float = 0.5,
    max_wait: float = 10.0,
):
    """Create a tenacity retry decorator with standard settings.

    Args:
        max_attempts: Maximum retry attempts (default from config)
        exceptions: Exception types to retry on
        min_wait: Minimum wait between retries in seconds
        max_wait: Maximum wait between retries in seconds

    Returns:
        Configured retry decorator
    """
    if max_attempts is None:
        max_attempts = get_config().max_retries

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=0.5, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def is_retryable_error(exception: Exception) -> bool:
    """Determine if an error is transient and should be retried.

    Args:
        exception: The exception to check

    Returns:
        True if the error is likely transient
    """
    from ibm_watsonx_ai_120b.exceptions import (
        ThinkingOnlyResponseError,
        ToolExtractionError,
        JSONExtractionError,
        SchemaValidationError,
    )

    # These are retryable - model may produce better output on retry
    retryable_types = (
        ThinkingOnlyResponseError,
        ToolExtractionError,
        JSONExtractionError,
        SchemaValidationError,
    )

    if isinstance(exception, retryable_types):
        return True

    # Check for transient HTTP errors
    error_str = str(exception).lower()
    transient_indicators = [
        "timeout",
        "connection",
        "temporarily unavailable",
        "rate limit",
        "429",
        "503",
        "504",
    ]

    return any(indicator in error_str for indicator in transient_indicators)