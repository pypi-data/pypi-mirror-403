"""
Basic usage example for pyteledb.

This example demonstrates:
- Initializing a database
- Inserting records
- Updating records
- Deleting records
- Getting database info
"""

import asyncio
import os

from pyteledb import DatabaseConfig, TelegramDatabase


async def main() -> None:
    # Get configuration from environment
    bot_token = os.environ.get("BOT_TOKEN")
    chat_id = os.environ.get("CHAT_ID")

    if not bot_token or not chat_id:
        print("Please set BOT_TOKEN and CHAT_ID environment variables")
        print("Example:")
        print("  export BOT_TOKEN='123456:ABC-DEF...'")
        print("  export CHAT_ID='-100123456789'")
        return

    # Create database configuration
    config = DatabaseConfig(
        bot_token=bot_token,
        chat_id=int(chat_id),
        db_name="example_db",
    )

    # Use the database
    async with TelegramDatabase(config) as db:
        # Initialize (creates root index if not exists)
        print("Initializing database...")
        root = await db.initialize()
        print(f"Database: {root.db_name}")
        print(f"Database ID: {root.db_id}")
        print()

        # Insert a record
        print("Inserting record...")
        record = await db.insert(
            {
                "user_id": 12345,
                "name": "Alice",
                "score": 100,
            }
        )
        print(f"Created record ID: {record.id}")
        print(f"Message ID: {record.message_id}")
        print(f"Version: {record.version}")
        print()

        # Update the record
        print("Updating record...")
        updated = await db.update(
            record.id,
            {
                "user_id": 12345,
                "name": "Alice",
                "score": 150,  # Updated score!
            },
        )
        print(f"New version: {updated.version}")
        print()

        # Get database info
        print("Database info:")
        info = await db.info()
        print(f"  Name: {info['name']}")
        print(f"  Record count: {info['record_count']}")
        print(f"  Cache enabled: {info['config']['cache_enabled']}")
        print()

        # Delete the record
        print("Deleting record...")
        await db.delete(record.id)
        print("Record deleted")
        print()

        # Final count
        count = await db.count()
        print(f"Final record count: {count}")


if __name__ == "__main__":
    asyncio.run(main())
