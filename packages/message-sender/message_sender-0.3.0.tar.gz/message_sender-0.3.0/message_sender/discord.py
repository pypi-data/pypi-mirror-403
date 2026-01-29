from __future__ import annotations

from typing import TYPE_CHECKING, Self

from httpx import AsyncClient, Client

if TYPE_CHECKING:
    from types import TracebackType


class _DiscordClientBase:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url


class AsyncDiscordClient(_DiscordClientBase):
    """Async client to send messages to Discord.

    Args:
        webhook_url: URL for the webhook created in Discord.
    """

    def __init__(self, webhook_url: str) -> None:
        self._client = AsyncClient()

        super().__init__(webhook_url=webhook_url)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        et: type[BaseException] | None,
        ev: type[BaseException] | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Closes the client.

        This is only needed if you don't use a context manager.

        Examples:
            >>> from message_sender.discord import AsyncDiscordClient
            >>>
            >>> client = AsyncDiscordClient("https://your-webhook-url.com")
            >>> await client.close()
        """

        await self._client.aclose()

    async def send_message(self, message: str) -> None:
        """Send a message to the Discord webhook.

        Args:
            message: The message to send

        Examples:
            >>> from message_sender.discord import AsyncDiscordClient
            >>>
            >>> async with AsyncDiscordClient("https://your-webhook-url.com") as client:
            >>>     await client.send_message("Some test message")
        """

        response = await self._client.post(self.webhook_url, json={"content": message})
        response.raise_for_status()


class DiscordClient(_DiscordClientBase):
    """Client to send messages to Discord.

    Args:
        webhook_url: URL for the webhook created in Discord.
    """

    def __init__(self, webhook_url: str) -> None:
        self._client = Client()

        super().__init__(webhook_url=webhook_url)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        et: type[BaseException] | None,
        ev: type[BaseException] | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Closes the client.

        This is only needed if you don't use a context manager.

        Examples:
            >>> from message_sender.discord import DiscordClient
            >>>
            >>> client = DiscordClient("https://your-webhook-url.com")
            >>> client.close()
        """

        self._client.close()

    def send_message(self, message: str) -> None:
        """Send a message to the Discord webhook.

        Args:
            message: The message to send

        Examples:
            >>> from message_sender.discord import DiscordClient
            >>>
            >>> with DiscordClient("https://your-webhook-url.com") as client:
            >>>     client.send_message("Some test message")
        """

        response = self._client.post(self.webhook_url, json={"content": message})
        response.raise_for_status()
