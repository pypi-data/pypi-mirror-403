from unittest.mock import AsyncMock, MagicMock, patch

from message_sender.google_chat import AsyncGoogleChatClient, GoogleChatClient


def test_send_message() -> None:
    mock_client = MagicMock()

    with patch("message_sender.google_chat.Client", return_value=mock_client):
        client = GoogleChatClient("https://example.com/webhook")
        client.send_message("Hello, World!")
        client.close()

    mock_client.post.assert_called_once_with(
        "https://example.com/webhook", json={"text": "Hello, World!"}
    )

    mock_client.close.assert_called_once()


def test_context_manager() -> None:
    mock_client = MagicMock()

    with patch("message_sender.google_chat.Client", return_value=mock_client):
        with GoogleChatClient("https://example.com/webhook") as client:
            client.send_message("test message")

    mock_client.close.assert_called_once()


async def test_async_send_message() -> None:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()

    with patch("message_sender.google_chat.AsyncClient", return_value=mock_client):
        client = AsyncGoogleChatClient("https://example.com/webhook")
        await client.send_message("Hello, World!")
        await client.close()

    mock_client.post.assert_called_once_with(
        "https://example.com/webhook", json={"text": "Hello, World!"}
    )

    mock_client.aclose.assert_called_once()


async def test_async_context_manager() -> None:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()

    with patch("message_sender.google_chat.AsyncClient", return_value=mock_client):
        async with AsyncGoogleChatClient("https://example.com/webhook") as client:
            await client.send_message("test message")

    mock_client.aclose.assert_called_once()
