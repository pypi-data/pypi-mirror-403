"""
Centralized exception hierarchy for pyteledb.

All exceptions inherit from PyTeleDBError for easy catching.
Exception design follows the principle of explicit, inspectable failures.
"""

from __future__ import annotations

from typing import Any


class PyTeleDBError(Exception):
    """Base exception for all pyteledb errors."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | details={self.details}"
        return self.message


# =============================================================================
# Connection & Network Errors
# =============================================================================


class ConnectionError(PyTeleDBError):
    """Failed to connect to Telegram API."""

    pass


class RateLimitError(PyTeleDBError):
    """Telegram API rate limit exceeded."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.retry_after = retry_after


class APIError(PyTeleDBError):
    """Generic Telegram API error."""

    def __init__(
        self,
        message: str,
        *,
        error_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.error_code = error_code


# =============================================================================
# Record & Data Errors
# =============================================================================


class RecordNotFoundError(PyTeleDBError):
    """Requested record does not exist."""

    def __init__(
        self,
        message: str,
        *,
        record_id: str | None = None,
        message_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.record_id = record_id
        self.message_id = message_id


class VersionConflictError(PyTeleDBError):
    """Write conflict due to version mismatch (optimistic locking failure)."""

    def __init__(
        self,
        message: str,
        *,
        expected_version: int | None = None,
        actual_version: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.expected_version = expected_version
        self.actual_version = actual_version


class ValidationError(PyTeleDBError):
    """Data validation failed (schema, type, or constraint violation)."""

    pass


class SerializationError(PyTeleDBError):
    """Failed to serialize or deserialize data."""

    pass


class PayloadTooLargeError(PyTeleDBError):
    """Payload exceeds Telegram message size limits."""

    def __init__(
        self,
        message: str,
        *,
        size: int | None = None,
        max_size: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.size = size
        self.max_size = max_size


# =============================================================================
# Consistency & Integrity Errors
# =============================================================================


class CorruptionError(PyTeleDBError):
    """Data corruption detected (checksum mismatch, invalid structure)."""

    pass


class RepairNeededError(PyTeleDBError):
    """Database state requires repair before operations can continue."""

    def __init__(
        self,
        message: str,
        *,
        repair_actions: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.repair_actions = repair_actions or []


class LockError(PyTeleDBError):
    """Lock acquisition or release failed."""

    pass


class LockTimeoutError(LockError):
    """Timed out waiting for lock acquisition."""

    pass


class StaleLockError(LockError):
    """Detected a stale lock that may need cleanup."""

    def __init__(
        self,
        message: str,
        *,
        lock_holder: str | None = None,
        lock_age_seconds: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.lock_holder = lock_holder
        self.lock_age_seconds = lock_age_seconds


# =============================================================================
# Database State Errors
# =============================================================================


class DatabaseNotInitializedError(PyTeleDBError):
    """Database has not been initialized (no root index found)."""

    pass


class DatabaseAlreadyExistsError(PyTeleDBError):
    """Attempted to initialize a database that already exists."""

    pass


class InvalidChatError(PyTeleDBError):
    """The specified chat is not valid for use as a database."""

    pass
