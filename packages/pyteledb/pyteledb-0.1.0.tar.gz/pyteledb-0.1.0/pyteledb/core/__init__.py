"""Core Telegram-native database logic.

This is the heart of pyteledb - the Telegram-native persistence abstraction.
"""

from pyteledb.core.database import TelegramDatabase
from pyteledb.core.locks import Lock, LockManager
from pyteledb.core.pointers import Pointer, PointerChain
from pyteledb.core.record import Record, RecordMetadata
from pyteledb.core.repair import RepairReport, RepairTool
from pyteledb.core.root import RootIndex

__all__ = [
    "TelegramDatabase",
    "Record",
    "RecordMetadata",
    "RootIndex",
    "Pointer",
    "PointerChain",
    "Lock",
    "LockManager",
    "RepairTool",
    "RepairReport",
]
