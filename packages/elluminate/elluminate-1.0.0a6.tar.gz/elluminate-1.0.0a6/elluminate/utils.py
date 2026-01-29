import asyncio
import warnings
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar, cast

import httpx
from httpx import Response
from loguru import logger
from tenacity import (
    RetryError,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from elluminate.exceptions import (
    RateLimitError,
    ServerError,
    raise_api_error,
)

# Configure warnings to only show once
warnings.filterwarnings("once", category=DeprecationWarning)


@dataclass
class RetryConfig:
    """Configuration for automatic retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts (default: 3).
        min_wait: Minimum wait time in seconds between retries (default: 1.0).
        max_wait: Maximum wait time in seconds between retries (default: 30.0).
        multiplier: Exponential backoff multiplier (default: 2.0).
        retry_on_429: Whether to retry on rate limit errors (default: True).
        retry_on_503: Whether to retry on service unavailable errors (default: True).
        retry_on_timeout: Whether to retry on timeout errors (default: True).

    Example:
        # Custom retry config with more attempts
        config = RetryConfig(max_attempts=5, max_wait=60.0)
        client = Client(retry_config=config)

        # Disable retries entirely
        client = Client(retry_config=RetryConfig(max_attempts=1))

    """

    max_attempts: int = 3
    min_wait: float = 1.0
    max_wait: float = 30.0
    multiplier: float = 2.0
    retry_on_429: bool = True
    retry_on_503: bool = True
    retry_on_timeout: bool = True
    _retryable_status_codes: set[int] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        """Build the set of retryable status codes."""
        self._retryable_status_codes = set()
        if self.retry_on_429:
            self._retryable_status_codes.add(429)
        if self.retry_on_503:
            self._retryable_status_codes.add(503)

    def should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry.

        Args:
            exception: The exception to check.

        Returns:
            True if the request should be retried.

        """
        # Check for HTTP status errors
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            if status_code in self._retryable_status_codes:
                logger.warning(f"Retrying due to {status_code} error: {exception}")
                return True
            return False

        # Check for our custom exceptions
        if isinstance(exception, (RateLimitError, ServerError)):
            if isinstance(exception, RateLimitError) and self.retry_on_429:
                logger.warning(f"Retrying due to rate limit: {exception}")
                return True
            if isinstance(exception, ServerError) and self.retry_on_503 and exception.status_code == 503:
                logger.warning(f"Retrying due to 503 service unavailable: {exception}")
                return True
            return False

        # Check for timeout errors
        if self.retry_on_timeout:
            if isinstance(exception, httpx.ReadTimeout):
                logger.warning(f"Retrying due to read timeout: {exception}")
                return True
            if isinstance(exception, httpx.ConnectTimeout):
                logger.warning(f"Retrying due to connect timeout: {exception}")
                return True

        return False


# Default retry configuration
DEFAULT_RETRY_CONFIG = RetryConfig()


def raise_for_status_with_detail(response: Response) -> None:
    """Raises appropriate exception with detailed error message from response.

    Uses the new exception hierarchy for better error handling.
    Falls back to HTTPStatusError for backwards compatibility if needed.
    """
    if response.is_success:
        return

    # Use new exception hierarchy
    raise_api_error(response)


T = TypeVar("T")
P = ParamSpec("P")
F = TypeVar("F", bound=Callable[..., Any])


_sync_loop: asyncio.AbstractEventLoop | None = None


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """Get the current event loop or create a persistent one for sync usage.

    This avoids the deprecation warning from asyncio.get_event_loop() in Python 3.10+
    while maintaining a persistent loop for the sync client to reuse.
    """
    global _sync_loop

    try:
        # If we're inside an async context, use that loop
        return asyncio.get_running_loop()
    except RuntimeError:
        pass

    # No running loop - use or create our persistent sync loop
    if _sync_loop is None or _sync_loop.is_closed():
        _sync_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_sync_loop)

    return _sync_loop


def run_async(async_func: Callable[P, Awaitable[T]]) -> Callable[P, T]:
    """Utility function to run an async function in a synchronous context."""

    @wraps(async_func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        loop = _get_or_create_event_loop()
        return cast(T, loop.run_until_complete(async_func(*args, **kwargs)))

    return sync_wrapper


def retry_predicate(exception: Exception) -> bool:
    """Retry if the exception is retryable based on default config."""
    return DEFAULT_RETRY_CONFIG.should_retry(exception)


retry_request = retry(
    stop=stop_after_attempt(DEFAULT_RETRY_CONFIG.max_attempts),
    wait=wait_exponential(
        multiplier=DEFAULT_RETRY_CONFIG.multiplier,
        min=DEFAULT_RETRY_CONFIG.min_wait,
        max=DEFAULT_RETRY_CONFIG.max_wait,
    ),
    retry=retry_if_exception(retry_predicate),
    retry_error_cls=RetryError,
)


def deprecated(
    since: str | None = None,
    removal_version: str | None = None,
    alternative: str | None = None,
    extra_message: str | None = None,
) -> Callable[[F], F]:
    """Decorator to mark functions as deprecated.

    Args:
        since (str | None): Version when the deprecation was introduced
        removal_version (str | None): Version when the function will be removed
        alternative (str | None): Alternative function or method to use
        extra_message (str | None): Additional message to include in the deprecation warning
    Returns:
        Callable: Decorated function that issues a deprecation warning

    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            message = f"{func.__name__} is deprecated"
            if since:
                message += f" since version {since}."
            else:
                message += "."
            if removal_version:
                message += f" It will be removed in version {removal_version}."
            else:
                message += " It will be removed in a future version."
            if alternative:
                message += f" Use {alternative} instead."
            if extra_message:
                message += f" {extra_message}"

            warnings.warn(
                message,
                category=DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator
