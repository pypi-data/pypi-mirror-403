from __future__ import annotations

from typing import TYPE_CHECKING, Self

from httpx import AsyncClient, Client

if TYPE_CHECKING:
    from types import TracebackType


class _GoogleChatClientBase:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url


class AsyncGoogleChatClient(_GoogleChatClientBase):
    """Async client to send messages to Google Chat.

    Args:
        webhook_url: URL for the webhook created in Google. To set this up creat a "space" in
            Google Chat then go to Apps & integrations and create a new webhook
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
            >>> from message_sender.google_chat import AsyncGoogleChatClient
            >>>
            >>> client = AsyncGoogleChatClient("https://your-webhook-url.com")
            >>> await client.close()
        """

        await self._client.aclose()

    async def send_message(self, message: str) -> None:
        """Send a message to the Google Chat webhook.

        Args:
            message: The message to send

        Examples:
            >>> from message_sender.google_chat import AsyncGoogleChatClient
            >>>
            >>> async with AsyncGoogleChatClient("https://your-webhook-url.com") as client:
            >>>     await client.send_message("Some test message")
        """

        result = await self._client.post(self.webhook_url, json={"text": message})
        result.raise_for_status()


class GoogleChatClient(_GoogleChatClientBase):
    """Client to send messages to Google Chat.

    Args:
        webhook_url: URL for the webhook created in Google. To set this up creat a "space" in
            Google Chat then go to Apps & integrations and create a new webhook
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
            >>> from message_sender.google_chat import GoogleChatClient
            >>>
            >>> client = GoogleChatClient("https://your-webhook-url.com")
            >>> client.close()
        """

        self._client.close()

    def send_message(self, message: str) -> None:
        """Send a message to the Google Chat webhook.

        Args:
            message: The message to send

        Examples:
            >>> from message_sender.google_chat import GoogleChatClient
            >>>
            >>> with GoogleChatClient("https://your-webhook-url.com") as client:
            >>>     client.send_message("Some test message")
        """

        result = self._client.post(self.webhook_url, json={"text": message})
        result.raise_for_status()
