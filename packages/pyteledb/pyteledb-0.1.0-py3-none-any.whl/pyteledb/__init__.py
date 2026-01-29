"""
pyteledb - A Telegram-native embedded database for Telegram bots.

This library implements a persistence abstraction where Telegram itself
is the storage layer. Only the Telegram Bot API is used - no MTProto,
no user accounts, no external databases required.

Data Model:
- Telegram channel/group = database
- Pinned message = root index
- Each record = one Telegram message

Example:
    ```python
    from pyteledb import TelegramDatabase, DatabaseConfig

    config = DatabaseConfig(
        bot_token="YOUR_BOT_TOKEN",
        chat_id=-100123456789,
        db_name="my_database",
    )

    async with TelegramDatabase(config) as db:
        await db.initialize()

        # Insert a record
        record = await db.insert({"name": "Alice", "score": 100})

        # Retrieve by ID
        fetched = await db.get(record.id)

        # Update
        await db.update(record.id, {"name": "Alice", "score": 150})

        # Delete
        await db.delete(record.id)
    ```
"""

# Core exports
from pyteledb.core.database import DatabaseConfig, TelegramDatabase
from pyteledb.core.record import Record, RecordMetadata
from pyteledb.core.root import RootIndex

# Exception exports
from pyteledb.exceptions import (
    ConnectionError,
    CorruptionError,
    DatabaseNotInitializedError,
    PyTeleDBError,
    RateLimitError,
    RecordNotFoundError,
    RepairNeededError,
    VersionConflictError,
)
from pyteledb.version import __version__

__all__ = [
    # Version
    "__version__",
    # Core
    "TelegramDatabase",
    "DatabaseConfig",
    "Record",
    "RecordMetadata",
    "RootIndex",
    # Exceptions
    "PyTeleDBError",
    "ConnectionError",
    "RateLimitError",
    "RecordNotFoundError",
    "VersionConflictError",
    "CorruptionError",
    "RepairNeededError",
    "DatabaseNotInitializedError",
]
