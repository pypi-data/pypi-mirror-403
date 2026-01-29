"""Pin management for Telegram Bot API.

Handles pinned messages used for root index storage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyteledb.telegram.client import TelegramClient


class PinManager:
    """
    Manages pinned messages for root index storage.

    The root index is stored as a pinned message in the chat.
    This class handles pin/unpin operations and retrieval.
    """

    def __init__(self, client: TelegramClient, chat_id: int | str) -> None:
        """
        Initialize the pin manager.

        Args:
            client: Telegram client instance.
            chat_id: Chat ID for all operations.
        """
        self.client = client
        self.chat_id = chat_id

    async def pin(
        self,
        message_id: int,
        disable_notification: bool = True,
    ) -> bool:
        """
        Pin a message.

        Args:
            message_id: ID of the message to pin.
            disable_notification: Disable notification sound.

        Returns:
            True if successful.
        """
        result = await self.client.request(
            "pinChatMessage",
            {
                "chat_id": self.chat_id,
                "message_id": message_id,
                "disable_notification": disable_notification,
            },
        )
        return result is True

    async def unpin(self, message_id: int | None = None) -> bool:
        """
        Unpin a message.

        Args:
            message_id: Specific message to unpin (None = unpin all).

        Returns:
            True if successful.
        """
        if message_id is not None:
            result = await self.client.request(
                "unpinChatMessage",
                {"chat_id": self.chat_id, "message_id": message_id},
            )
        else:
            result = await self.client.request(
                "unpinAllChatMessages",
                {"chat_id": self.chat_id},
            )
        return result is True

    async def get_pinned_message_id(self) -> int | None:
        """
        Get the ID of the currently pinned message.

        Returns:
            Message ID if a message is pinned, None otherwise.
        """
        chat_info = await self.client.get_chat(self.chat_id)
        pinned = chat_info.get("pinned_message")
        if pinned:
            return pinned.get("message_id")
        return None

    async def get_pinned_message(self) -> dict[str, Any] | None:
        """
        Get the full pinned message data.

        Returns:
            Message data if pinned, None otherwise.
        """
        chat_info = await self.client.get_chat(self.chat_id)
        return chat_info.get("pinned_message")

    async def get_pinned_text(self) -> str | None:
        """
        Get the text of the pinned message.

        Returns:
            Message text if pinned, None otherwise.
        """
        message = await self.get_pinned_message()
        if message:
            return message.get("text")
        return None

    async def update_pinned(
        self,
        text: str,
        message_id: int | None = None,
    ) -> int:
        """
        Update the pinned message content.

        If message_id is provided, edits that message.
        Otherwise, gets the current pinned message and edits it.

        Args:
            text: New message text.
            message_id: Message ID to edit (optional).

        Returns:
            The message ID that was updated.

        Raises:
            ValueError: If no pinned message exists.
        """
        if message_id is None:
            message_id = await self.get_pinned_message_id()
            if message_id is None:
                raise ValueError("No pinned message to update")

        await self.client.edit_message_text(
            self.chat_id,
            message_id,
            text,
        )
        return message_id

    async def create_and_pin(
        self,
        text: str,
        disable_notification: bool = True,
    ) -> int:
        """
        Create a new message and pin it.

        Args:
            text: Message text.
            disable_notification: Disable notification sound.

        Returns:
            The new message ID.
        """
        result = await self.client.send_message(
            self.chat_id,
            text,
            disable_notification=disable_notification,
        )
        message_id = result["message_id"]
        await self.pin(message_id, disable_notification=disable_notification)
        return message_id
