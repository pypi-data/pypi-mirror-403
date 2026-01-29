from email.message import EmailMessage
from unittest.mock import AsyncMock, MagicMock, patch

from message_sender.email.smtp import AsyncSMTPClient, SMTPClient


def test_send_email_plain_text() -> None:
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)

    with patch("message_sender.email.smtp.smtplib.SMTP", return_value=mock_smtp):
        client = SMTPClient(
            smtp_server="smtp.server.com",
            smtp_port=587,
            email_from="sender@email.com",
            user_name="test-user",
            password="test-password",
        )
        client.send_email(
            message="Hello, World!",
            email_to="recipient@example.com",
            subject="Test Subject",
        )

    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("test-user", "test-password")
    mock_smtp.send_message.assert_called_once()

    sent_message: EmailMessage = mock_smtp.send_message.call_args[0][0]
    assert sent_message["Subject"] == "Test Subject"
    assert sent_message["From"] == "sender@email.com"
    assert sent_message["To"] == "recipient@example.com"
    assert sent_message.get_content().strip() == "Hello, World!"


def test_send_email_with_html() -> None:
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)

    with patch("message_sender.email.smtp.smtplib.SMTP", return_value=mock_smtp):
        client = SMTPClient(
            smtp_server="smtp.server.com",
            smtp_port=587,
            email_from="sender@email.com",
            user_name="test-user",
            password="test-password",
        )
        client.send_email(
            message="Hello, World!",
            email_to="recipient@example.com",
            subject="Test Subject",
            html_content="<p>Hello, World!</p>",
        )

    mock_smtp.send_message.assert_called_once()

    sent_message: EmailMessage = mock_smtp.send_message.call_args[0][0]
    assert sent_message.is_multipart()


def test_smtp_connection_parameters() -> None:
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)

    with patch("message_sender.email.smtp.smtplib.SMTP", return_value=mock_smtp) as mock_smtp_class:
        client = SMTPClient(
            smtp_server="smtp.server.com",
            smtp_port=587,
            email_from="sender@email.com",
            user_name="test-user",
            password="test-password",
        )
        client.send_email(
            message="Hello",
            email_to="recipient@example.com",
            subject="Test",
        )

    mock_smtp_class.assert_called_once_with("smtp.server.com", 587)


def test_smtp_port_465_uses_implicit_tls() -> None:
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)

    with patch(
        "message_sender.email.smtp.smtplib.SMTP_SSL", return_value=mock_smtp
    ) as mock_smtp_ssl_class:
        client = SMTPClient(
            smtp_server="smtp.server.com",
            smtp_port=465,
            email_from="sender@email.com",
            user_name="test-user",
            password="test-password",
        )
        client.send_email(
            message="Hello",
            email_to="recipient@example.com",
            subject="Test",
        )

    mock_smtp_ssl_class.assert_called_once_with("smtp.server.com", 465)
    mock_smtp.login.assert_called_once_with("test-user", "test-password")
    mock_smtp.send_message.assert_called_once()


async def test_async_send_email_plain_text() -> None:
    mock_smtp = MagicMock()
    mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
    mock_smtp.__aexit__ = AsyncMock(return_value=False)
    mock_smtp.send_message = AsyncMock()

    with patch("message_sender.email.smtp.SMTP", return_value=mock_smtp):
        client = AsyncSMTPClient(
            smtp_server="smtp.server.com",
            smtp_port=587,
            email_from="sender@email.com",
            user_name="test-user",
            password="test-password",
        )
        await client.send_email(
            message="Hello, World!",
            email_to="recipient@example.com",
            subject="Test Subject",
        )

    mock_smtp.send_message.assert_called_once()

    sent_message: EmailMessage = mock_smtp.send_message.call_args[0][0]
    assert sent_message["Subject"] == "Test Subject"
    assert sent_message["From"] == "sender@email.com"
    assert sent_message["To"] == "recipient@example.com"
    assert sent_message.get_content().strip() == "Hello, World!"


async def test_async_send_email_with_html() -> None:
    mock_smtp = MagicMock()
    mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
    mock_smtp.__aexit__ = AsyncMock(return_value=False)
    mock_smtp.send_message = AsyncMock()

    with patch("message_sender.email.smtp.SMTP", return_value=mock_smtp):
        client = AsyncSMTPClient(
            smtp_server="smtp.server.com",
            smtp_port=587,
            email_from="sender@email.com",
            user_name="test-user",
            password="test-password",
        )
        await client.send_email(
            message="Hello, World!",
            email_to="recipient@example.com",
            subject="Test Subject",
            html_content="<p>Hello, World!</p>",
        )

    mock_smtp.send_message.assert_called_once()

    sent_message: EmailMessage = mock_smtp.send_message.call_args[0][0]
    assert sent_message.is_multipart()


async def test_async_smtp_connection_parameters() -> None:
    mock_smtp = MagicMock()
    mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
    mock_smtp.__aexit__ = AsyncMock(return_value=False)
    mock_smtp.send_message = AsyncMock()

    with patch("message_sender.email.smtp.SMTP", return_value=mock_smtp) as mock_smtp_class:
        client = AsyncSMTPClient(
            smtp_server="smtp.server.com",
            smtp_port=587,
            email_from="sender@email.com",
            user_name="test-user",
            password="test-password",
        )
        await client.send_email(
            message="Hello",
            email_to="recipient@example.com",
            subject="Test",
        )

    mock_smtp_class.assert_called_once_with(
        hostname="smtp.server.com",
        port=587,
        username="test-user",
        password="test-password",
        use_tls=False,
        start_tls=True,
    )


async def test_async_smtp_port_465_uses_implicit_tls() -> None:
    mock_smtp = MagicMock()
    mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
    mock_smtp.__aexit__ = AsyncMock(return_value=False)
    mock_smtp.send_message = AsyncMock()

    with patch("message_sender.email.smtp.SMTP", return_value=mock_smtp) as mock_smtp_class:
        client = AsyncSMTPClient(
            smtp_server="smtp.server.com",
            smtp_port=465,
            email_from="sender@email.com",
            user_name="test-user",
            password="test-password",
        )
        await client.send_email(
            message="Hello",
            email_to="recipient@example.com",
            subject="Test",
        )

    mock_smtp_class.assert_called_once_with(
        hostname="smtp.server.com",
        port=465,
        username="test-user",
        password="test-password",
        use_tls=True,
        start_tls=False,
    )
