"""Async Telegram Bot API client.

Token-based authentication via httpx.
STRICT Bot API only - no MTProto, no user accounts.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx

from pyteledb.telegram.errors import (
    TelegramNetworkError,
    parse_api_error,
)
from pyteledb.utils.logging import get_logger

logger = get_logger(__name__)

# Telegram Bot API base URL
BOT_API_BASE = "https://api.telegram.org"


@dataclass
class ClientConfig:
    """Configuration for TelegramClient."""

    token: str
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    pool_size: int = 10


@dataclass
class APIResponse:
    """Parsed API response."""

    ok: bool
    result: Any = None
    error_code: int | None = None
    description: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


class TelegramClient:
    """
    Async Telegram Bot API client.

    Uses httpx for HTTP transport with connection pooling.
    Handles rate limiting, retries, and error parsing.
    """

    def __init__(self, config: ClientConfig) -> None:
        """
        Initialize the Telegram client.

        Args:
            config: Client configuration with bot token.
        """
        self.config = config
        self._base_url = f"{BOT_API_BASE}/bot{config.token}"
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                limits=httpx.Limits(
                    max_connections=self.config.pool_size,
                    max_keepalive_connections=self.config.pool_size,
                ),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> TelegramClient:
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make a Bot API request.

        Args:
            method: API method name (e.g., "sendMessage").
            params: Request parameters.
            files: Files to upload (for multipart requests).

        Returns:
            The "result" field from the API response.

        Raises:
            TelegramAPIError: On API errors.
            TelegramNetworkError: On network errors.
        """
        client = await self._ensure_client()
        url = f"{self._base_url}/{method}"

        # Filter None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        last_error: Exception | None = None

        for attempt in range(self.config.max_retries):
            try:
                if files:
                    # Multipart upload
                    response = await client.post(url, data=params, files=files)
                else:
                    # JSON request
                    response = await client.post(url, json=params or {})

                data = response.json()
                api_response = APIResponse(
                    ok=data.get("ok", False),
                    result=data.get("result"),
                    error_code=data.get("error_code"),
                    description=data.get("description"),
                    parameters=data.get("parameters", {}),
                )

                if api_response.ok:
                    return api_response.result

                # Parse and raise API error
                error = parse_api_error(response.status_code, data)

                # Check if we should retry
                from pyteledb.telegram.errors import (
                    TelegramRateLimitError,
                    is_retryable,
                )

                if is_retryable(error) and attempt < self.config.max_retries - 1:
                    if isinstance(error, TelegramRateLimitError):
                        wait_time = error.retry_after
                    else:
                        wait_time = self.config.retry_delay * (2**attempt)

                    logger.warning(f"Retrying {method} after {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    last_error = error
                    continue

                raise error

            except httpx.RequestError as e:
                last_error = TelegramNetworkError(
                    f"Network error: {e}",
                    description=str(e),
                )

                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2**attempt)
                    logger.warning(f"Network error, retrying {method} after {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

                raise last_error from e

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise TelegramNetworkError("Request failed after retries")

    # Convenience methods for common operations

    async def get_me(self) -> dict[str, Any]:
        """Get bot information."""
        return await self.request("getMe")

    async def get_chat(self, chat_id: int | str) -> dict[str, Any]:
        """Get chat information."""
        return await self.request("getChat", {"chat_id": chat_id})

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a text message."""
        return await self.request(
            "sendMessage",
            {"chat_id": chat_id, "text": text, **kwargs},
        )

    async def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Edit a message's text."""
        return await self.request(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                **kwargs,
            },
        )

    async def delete_message(
        self,
        chat_id: int | str,
        message_id: int,
    ) -> bool:
        """Delete a message."""
        return await self.request(
            "deleteMessage",
            {"chat_id": chat_id, "message_id": message_id},
        )

    async def forward_message(
        self,
        chat_id: int | str,
        from_chat_id: int | str,
        message_id: int,
    ) -> dict[str, Any]:
        """Forward a message."""
        return await self.request(
            "forwardMessage",
            {
                "chat_id": chat_id,
                "from_chat_id": from_chat_id,
                "message_id": message_id,
            },
        )

    async def copy_message(
        self,
        chat_id: int | str,
        from_chat_id: int | str,
        message_id: int,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Copy a message."""
        return await self.request(
            "copyMessage",
            {
                "chat_id": chat_id,
                "from_chat_id": from_chat_id,
                "message_id": message_id,
                **kwargs,
            },
        )
