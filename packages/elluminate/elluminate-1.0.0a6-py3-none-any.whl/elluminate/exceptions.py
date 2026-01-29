"""Custom exceptions for the elluminate SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


@dataclass
class ResponseInfo:
    """Sanitized HTTP response information for error reporting.

    This class contains only non-sensitive information extracted from
    an HTTP response. It is safe to log, serialize, or send to error
    tracking services.

    Attributes:
        status_code: HTTP status code from the response.
        method: HTTP method used (GET, POST, etc.).
        url: Request URL with sensitive query parameters redacted.
        body: Response body (truncated if too large).
        content_type: Content-Type header from the response.

    """

    status_code: int
    method: str
    url: str
    body: str | dict | None
    content_type: str | None = None

    @classmethod
    def from_response(cls, response: httpx.Response) -> ResponseInfo:
        """Extract safe information from an httpx.Response.

        Sensitive data like request headers (API keys, tokens) and
        query parameters that may contain keys are excluded.

        Args:
            response: The httpx Response object to extract information from.

        Returns:
            ResponseInfo with sanitized data safe for logging.

        """
        # Sanitize URL - remove sensitive query params
        url = str(response.url)
        sensitive_params = ["api_key", "token", "key", "secret", "password"]
        if any(param in url.lower() for param in sensitive_params):
            url = url.split("?")[0] + "?<redacted>"

        # Extract response body (response bodies typically don't contain secrets)
        body: str | dict | None
        try:
            body = response.json()
        except Exception:
            # If not JSON, include truncated text
            text = response.text
            body = text[:1000] + "..." if len(text) > 1000 else text

        return cls(
            status_code=response.status_code,
            method=response.request.method,
            url=url,
            body=body,
            content_type=response.headers.get("content-type"),
        )


class ElluminateError(Exception):
    """Base exception for all elluminate SDK errors."""

    pass


class APIError(ElluminateError):
    """Error from the elluminate API.

    Attributes:
        status_code: HTTP status code from the response.
        message: Error message.
        response_info: Sanitized response information (safe to log/serialize).

    Security Note:
        This exception does NOT store the original httpx.Response object
        to prevent accidental exposure of API keys in logs, error tracking
        services, or serialization. Use response_info for debugging context.

    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.response_info = ResponseInfo.from_response(response) if response is not None else None
        super().__init__(message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(APIError):
    """Authentication failed (401).

    Raised when the API key or token is invalid or missing.
    """

    pass


class PermissionDeniedError(APIError):
    """Permission denied (403).

    Raised when the user doesn't have permission for the requested operation.
    """

    pass


class NotFoundError(APIError):
    """Resource not found (404).

    Raised when a requested resource doesn't exist.
    """

    pass


class ConflictError(APIError):
    """Resource already exists (409).

    Raised when attempting to create a resource that already exists.

    Attributes:
        resource_type: Type of resource (e.g., "prompt_template", "collection").
        resource_name: Name of the conflicting resource.
        resource_id: ID of the existing resource (if available).

    """

    def __init__(
        self,
        message: str,
        status_code: int = 409,
        response: "httpx.Response | None" = None,
        resource_type: str | None = None,
        resource_name: str | None = None,
        resource_id: int | None = None,
    ) -> None:
        super().__init__(message, status_code, response)
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.resource_id = resource_id


class RateLimitError(APIError):
    """Rate limit exceeded (429).

    Raised when too many requests are made in a short period.

    Attributes:
        retry_after: Seconds to wait before retrying (if provided by server).

    """

    def __init__(
        self,
        message: str,
        status_code: int = 429,
        response: httpx.Response | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code, response)
        self.retry_after = retry_after


class ServerError(APIError):
    """Server error (5xx).

    Raised when the server encounters an internal error.
    """

    pass


class ModelNotBoundError(ElluminateError):
    """Model not bound to a client.

    Raised when a rich model method is called on a model that wasn't
    fetched or created via a client. Rich models need a client reference
    to make API calls.

    Attributes:
        model_type: Type of model (e.g., "Experiment", "CriterionSet").
        hint: Suggestion for how to bind the model to a client.

    Example:
        # This will raise ModelNotBoundError:
        experiment = Experiment(name="test", ...)  # Created directly
        experiment.run()  # Error: not bound to client

        # This works:
        experiment = client.create_experiment(name="test", ...)  # Via client
        experiment.run()  # OK: client is bound

    """

    def __init__(
        self,
        model_type: str,
        hint: str | None = None,
    ) -> None:
        self.model_type = model_type
        self.hint = hint
        message = f"{model_type} is not bound to a client."
        if hint:
            message += f" {hint}"
        super().__init__(message)


class ValidationError(ElluminateError):
    """Input validation error.

    Raised when user-provided input fails validation.
    """

    pass


class ConfigurationError(ElluminateError):
    """Configuration error.

    Raised when the SDK is misconfigured (e.g., missing API key).
    """

    pass


class RetryExhaustedError(ElluminateError):
    """All retry attempts exhausted.

    Raised when an operation fails after all retry attempts.

    Attributes:
        last_exception: The last exception that caused the retry to fail.
        attempts: Number of attempts made.

    """

    def __init__(
        self,
        message: str,
        last_exception: Exception | None = None,
        attempts: int = 0,
    ) -> None:
        self.last_exception = last_exception
        self.attempts = attempts
        super().__init__(message)


def raise_api_error(response: httpx.Response, message: str | None = None) -> None:
    """Raise the appropriate APIError subclass based on status code.

    Args:
        response: The httpx Response object.
        message: Optional custom error message.

    Raises:
        AuthenticationError: For 401 responses.
        PermissionDeniedError: For 403 responses.
        NotFoundError: For 404 responses.
        ConflictError: For 409 responses.
        RateLimitError: For 429 responses.
        ServerError: For 5xx responses.
        APIError: For other non-2xx responses.

    """
    status_code = response.status_code

    # Try to extract error detail from response
    if message is None:
        try:
            detail = response.json().get("detail")
            message = detail if detail else response.text
        except Exception:
            message = response.text or f"HTTP {status_code}"

    # Ensure message is never None (for type safety)
    error_message = message if message else f"HTTP {status_code}"

    # Map status code to exception class
    if status_code == 401:
        raise AuthenticationError(error_message, status_code, response)
    elif status_code == 403:
        raise PermissionDeniedError(error_message, status_code, response)
    elif status_code == 404:
        raise NotFoundError(error_message, status_code, response)
    elif status_code == 409:
        raise ConflictError(error_message, status_code, response)
    elif status_code == 429:
        retry_after = response.headers.get("Retry-After")
        retry_after_seconds = float(retry_after) if retry_after else None
        raise RateLimitError(error_message, status_code, response, retry_after_seconds)
    elif 500 <= status_code < 600:
        raise ServerError(error_message, status_code, response)
    else:
        raise APIError(error_message, status_code, response)
