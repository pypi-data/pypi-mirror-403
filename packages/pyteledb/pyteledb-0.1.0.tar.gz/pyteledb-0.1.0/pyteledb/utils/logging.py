"""Logging utilities for pyteledb.

Provides structured logging with context propagation.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any


# Context variable for request/operation tracking
# Using factory function to avoid mutable default
def _default_context() -> dict[str, Any]:
    return {}


_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default=None)  # type: ignore


class ContextualFormatter(logging.Formatter):
    """Formatter that includes context variables in log output."""

    def format(self, record: logging.LogRecord) -> str:
        # Add context to the record
        context = _log_context.get() or {}
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            record.msg = f"[{context_str}] {record.msg}"
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name, typically __name__ of the module.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            ContextualFormatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def set_log_context(**kwargs: Any) -> None:
    """
    Set context variables for logging.

    These will be included in all log messages in the current context.

    Args:
        **kwargs: Key-value pairs to add to the log context.
    """
    current = (_log_context.get() or {}).copy()
    current.update(kwargs)
    _log_context.set(current)


def clear_log_context() -> None:
    """Clear all context variables."""
    _log_context.set({})


def get_log_context() -> dict[str, Any]:
    """
    Get the current log context.

    Returns:
        Copy of the current context dictionary.
    """
    return (_log_context.get() or {}).copy()


class LogContext:
    """Context manager for temporary log context."""

    def __init__(self, **kwargs: Any) -> None:
        self._new_context = kwargs
        self._old_context: dict[str, Any] = {}

    def __enter__(self) -> LogContext:
        self._old_context = (_log_context.get() or {}).copy()
        new = self._old_context.copy()
        new.update(self._new_context)
        _log_context.set(new)
        return self

    def __exit__(self, *_: Any) -> None:
        _log_context.set(self._old_context)
