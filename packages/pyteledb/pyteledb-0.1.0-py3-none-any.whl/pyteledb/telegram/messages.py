"""Message operations for Telegram Bot API.

Handles sending, editing, and retrieving messages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyteledb.telegram.client import TelegramClient


@dataclass
class Message:
    """
    Represents a Telegram message.

    Simplified representation of the Telegram Message object.
    """

    message_id: int
    chat_id: int
    text: str | None = None
    date: int = 0
    edit_date: int | None = None
    from_user_id: int | None = None
    document: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Message:
        """Create from API response data."""
        chat = data.get("chat", {})
        from_user = data.get("from", {})

        return cls(
            message_id=data["message_id"],
            chat_id=chat.get("id", 0),
            text=data.get("text"),
            date=data.get("date", 0),
            edit_date=data.get("edit_date"),
            from_user_id=from_user.get("id"),
            document=data.get("document"),
            raw=data,
        )


class MessageManager:
    """
    High-level message operations.

    Wraps TelegramClient with message-specific logic.
    """

    def __init__(self, client: TelegramClient, chat_id: int | str) -> None:
        """
        Initialize the message manager.

        Args:
            client: Telegram client instance.
            chat_id: Chat ID for all operations.
        """
        self.client = client
        self.chat_id = chat_id

    async def send(
        self,
        text: str,
        parse_mode: str | None = None,
        disable_notification: bool = False,
        reply_to_message_id: int | None = None,
    ) -> Message:
        """
        Send a text message.

        Args:
            text: Message text.
            parse_mode: Parse mode ("HTML" or "Markdown").
            disable_notification: Disable notification sound.
            reply_to_message_id: Message to reply to.

        Returns:
            The sent message.
        """
        result = await self.client.send_message(
            self.chat_id,
            text,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
        )
        return Message.from_api(result)

    async def edit(
        self,
        message_id: int,
        text: str,
        parse_mode: str | None = None,
    ) -> Message:
        """
        Edit a message's text.

        Args:
            message_id: ID of the message to edit.
            text: New message text.
            parse_mode: Parse mode.

        Returns:
            The edited message.
        """
        result = await self.client.edit_message_text(
            self.chat_id,
            message_id,
            text,
            parse_mode=parse_mode,
        )
        return Message.from_api(result)

    async def delete(self, message_id: int) -> bool:
        """
        Delete a message.

        Args:
            message_id: ID of the message to delete.

        Returns:
            True if successful.
        """
        return await self.client.delete_message(self.chat_id, message_id)

    async def forward(
        self,
        from_chat_id: int | str,
        message_id: int,
    ) -> Message:
        """
        Forward a message to this chat.

        Args:
            from_chat_id: Source chat ID.
            message_id: Message ID to forward.

        Returns:
            The forwarded message.
        """
        result = await self.client.forward_message(
            self.chat_id,
            from_chat_id,
            message_id,
        )
        return Message.from_api(result)

    async def copy(
        self,
        from_chat_id: int | str,
        message_id: int,
        caption: str | None = None,
    ) -> int:
        """
        Copy a message to this chat.

        Args:
            from_chat_id: Source chat ID.
            message_id: Message ID to copy.
            caption: New caption (for media messages).

        Returns:
            The new message ID.
        """
        result = await self.client.copy_message(
            self.chat_id,
            from_chat_id,
            message_id,
            caption=caption,
        )
        return result["message_id"]

    async def get_by_forward(
        self,
        message_id: int,
        temp_chat_id: int | str | None = None,
    ) -> Message | None:
        """
        Retrieve a message by forwarding it (workaround for Bot API limitations).

        Note: This creates a temporary forwarded message that should be deleted.
        Only use this if you need to read message content that's not cached.

        Args:
            message_id: Message ID to retrieve.
            temp_chat_id: Chat to forward to (defaults to same chat).

        Returns:
            The message content, or None if not accessible.
        """
        target = temp_chat_id or self.chat_id

        try:
            result = await self.client.forward_message(
                target,
                self.chat_id,
                message_id,
            )
            forwarded = Message.from_api(result)

            # Clean up the temporary forward
            await self.client.delete_message(target, forwarded.message_id)

            return forwarded
        except Exception:
            return None
