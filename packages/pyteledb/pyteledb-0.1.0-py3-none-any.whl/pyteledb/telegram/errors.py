"""Telegram API error handling.

Provides structured error types for Telegram Bot API responses.
"""

from __future__ import annotations

from typing import Any


class TelegramAPIError(Exception):
    """
    Base exception for Telegram API errors.

    Attributes:
        message: Error message.
        error_code: Telegram API error code.
        description: API error description.
        parameters: Additional error parameters.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: int | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.description = description
        self.parameters = parameters or {}

    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f"code={self.error_code}")
        if self.description:
            parts.append(f"desc='{self.description}'")
        return " | ".join(parts)


class TelegramNetworkError(TelegramAPIError):
    """Network-level error (connection failed, timeout, etc.)."""

    pass


class TelegramRateLimitError(TelegramAPIError):
    """
    Rate limit exceeded (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: float,
        error_code: int | None = 429,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code=error_code,
            description=description,
            parameters=parameters,
        )
        self.retry_after = retry_after


class TelegramBadRequestError(TelegramAPIError):
    """Bad request error (HTTP 400)."""

    pass


class TelegramUnauthorizedError(TelegramAPIError):
    """Unauthorized error - invalid bot token (HTTP 401)."""

    pass


class TelegramForbiddenError(TelegramAPIError):
    """Forbidden - bot lacks permissions (HTTP 403)."""

    pass


class TelegramNotFoundError(TelegramAPIError):
    """Resource not found (HTTP 404)."""

    pass


class TelegramConflictError(TelegramAPIError):
    """Conflict error - e.g., webhook already set (HTTP 409)."""

    pass


def parse_api_error(
    status_code: int,
    response_data: dict[str, Any],
) -> TelegramAPIError:
    """
    Parse an API error response into the appropriate exception type.

    Args:
        status_code: HTTP status code.
        response_data: Parsed JSON response.

    Returns:
        Appropriate TelegramAPIError subclass.
    """
    error_code = response_data.get("error_code", status_code)
    description = response_data.get("description", "Unknown error")
    parameters = response_data.get("parameters", {})

    # Check for rate limiting
    retry_after = parameters.get("retry_after")
    if retry_after is not None or status_code == 429:
        return TelegramRateLimitError(
            f"Rate limited: {description}",
            retry_after=float(retry_after or 30),
            error_code=error_code,
            description=description,
            parameters=parameters,
        )

    # Map status codes to exceptions
    error_map: dict[int, type[TelegramAPIError]] = {
        400: TelegramBadRequestError,
        401: TelegramUnauthorizedError,
        403: TelegramForbiddenError,
        404: TelegramNotFoundError,
        409: TelegramConflictError,
    }

    error_class = error_map.get(status_code, TelegramAPIError)
    return error_class(
        description,
        error_code=error_code,
        description=description,
        parameters=parameters,
    )


def is_retryable(error: TelegramAPIError) -> bool:
    """
    Check if an error is retryable.

    Args:
        error: The error to check.

    Returns:
        True if the request should be retried.
    """
    # Rate limits should be retried after waiting
    if isinstance(error, TelegramRateLimitError):
        return True

    # Network errors are generally retryable
    if isinstance(error, TelegramNetworkError):
        return True

    # Server errors (5xx) are retryable
    return bool(error.error_code and error.error_code >= 500)
