"""Telegram Bot API boundary layer.

This module provides STRICT Bot API access only.
No MTProto, no user accounts, no sessions.
"""

from pyteledb.telegram.client import TelegramClient
from pyteledb.telegram.errors import (
    TelegramAPIError,
    TelegramNetworkError,
    TelegramRateLimitError,
)
from pyteledb.telegram.files import FileManager
from pyteledb.telegram.messages import MessageManager
from pyteledb.telegram.pins import PinManager

__all__ = [
    "TelegramClient",
    "MessageManager",
    "FileManager",
    "PinManager",
    "TelegramAPIError",
    "TelegramNetworkError",
    "TelegramRateLimitError",
]
