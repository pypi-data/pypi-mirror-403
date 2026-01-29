"""
Example using pyteledb with local cache.

This example demonstrates:
- Configuring cache settings
- Cache behavior (hits/misses)
- Cache statistics
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
        return

    # Configure with custom cache settings
    config = DatabaseConfig(
        bot_token=bot_token,
        chat_id=int(chat_id),
        db_name="cache_example",
        # Cache configuration
        cache_enabled=True,
        cache_ttl=60.0,  # 1 minute TTL
        cache_max_size=100,  # Max 100 entries
    )

    async with TelegramDatabase(config) as db:
        await db.initialize()

        # Insert some records
        print("Inserting records...")
        records = []
        for i in range(5):
            record = await db.insert(
                {
                    "index": i,
                    "value": f"item_{i}",
                }
            )
            records.append(record)
            print(f"  Created: {record.id[:8]}...")

        print()

        # Access records (should be cached)
        print("Accessing records (should hit cache)...")
        for record in records:
            fetched = await db.get(record.id)
            print(f"  Got: {fetched.payload['value']}")

        print()

        # Check cache statistics
        info = await db.info()
        cache_stats = info.get("cache", {})
        print("Cache statistics:")
        print(f"  Size: {cache_stats.get('size', 'N/A')}")
        print(f"  Hits: {cache_stats.get('hits', 'N/A')}")
        print(f"  Misses: {cache_stats.get('misses', 'N/A')}")
        print(f"  Hit rate: {cache_stats.get('hit_rate', 0):.1%}")

        print()

        # Clean up
        print("Cleaning up...")
        for record in records:
            await db.delete(record.id)
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
