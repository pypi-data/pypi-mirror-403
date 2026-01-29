from __future__ import annotations

import smtplib
from email.message import EmailMessage

from aiosmtplib import SMTP


class _SMTPBase:
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        email_from: str,
        user_name: str,
        password: str,
    ) -> None:
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_from = email_from
        self.user_name = user_name
        self.password = password

    def _use_implicit_tls(self) -> bool:
        """Determine if implicit TLS should be used based on port.

        Port 465 uses implicit TLS, others use STARTTLS.
        """
        return self.smtp_port == 465


class AsyncSMTPClient(_SMTPBase):
    """Async client for sending SMTP emails.

    Args:
        smtp_server: The SMTP server for the email provider
        smtp_port: The SMTP port for the email provider. Port 465 uses implicit TLS,
            other ports use STARTTLS.
        email_from: The email address for sending emails
        user_name: The user name to use for sending SMTP emails
        password: The password to use for sending SMTP emails
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        email_from: str,
        user_name: str,
        password: str,
    ) -> None:
        super().__init__(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            email_from=email_from,
            user_name=user_name,
            password=password,
        )

    async def send_email(
        self,
        *,
        message: str,
        email_to: str,
        subject: str,
        html_content: str | None = None,
    ) -> None:
        """Send the email through the SMTP server.

        Args:
            message: The message body. If not html_content is provided or the receiving client does
                not support HTML this is used.
            email_to: The email address where the email should be sent
            subject: The subject of the email
            html_content: The message body with HTML markup. Defaults to None

        Examples:
            >>> from message_sender.email.smtp import AsyncSMTPClient
            >>>
            >>> client = AsyncSMTPClient(
            >>>     smtp_server="smtp.server.com",
            >>>     smtp_port=587,
            >>>     email_from="send_from@email.com",
            >>>     user_name="smtp_user",
            >>>     password="smtp_password",
            >>> )
            >>> await client.send_email(
            >>>     message="Your message body",
            >>>     email_to="someone@email.com",
            >>>     subject="Example",
            >>>     html_content="<p>Your HTML message body</p>",
            >>> )
        """

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.email_from
        msg["To"] = email_to
        msg.set_content(message)

        if html_content:
            msg.add_alternative(html_content, subtype="html")

        async with SMTP(
            hostname=self.smtp_server,
            port=self.smtp_port,
            username=self.user_name,
            password=self.password,
            use_tls=self._use_implicit_tls(),
            start_tls=not self._use_implicit_tls(),
        ) as smtp:
            await smtp.send_message(msg)


class SMTPClient(_SMTPBase):
    """Client for sending SMTP emails.

    Args:
        smtp_server: The SMTP server for the email provider
        smtp_port: The SMTP port for the email provider. Port 465 uses implicit TLS,
            other ports use STARTTLS.
        email_from: The email address for sending emails
        user_name: The user name to use for sending SMTP emails
        password: The password to use for sending SMTP emails
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        email_from: str,
        user_name: str,
        password: str,
    ) -> None:
        super().__init__(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            email_from=email_from,
            user_name=user_name,
            password=password,
        )

    def send_email(
        self,
        *,
        message: str,
        email_to: str,
        subject: str,
        html_content: str | None = None,
    ) -> None:
        """Send the email through the SMTP server.

        Args:
            message: The message body. If not html_content is provided or the receiving client does
                not support HTML this is used.
            email_to: The email address where the email should be sent
            subject: The subject of the email
            html_content: The message body with HTML markup. Defaults to None

        Examples:
            >>> from message_sender.email.smtp import SMTPClient
            >>>
            >>> client = SMTPClient(
            >>>     smtp_server="smtp.server.com",
            >>>     smtp_port=587,
            >>>     email_from="send_from@email.com",
            >>>     user_name="smtp_user",
            >>>     password="smtp_password",
            >>> )
            >>> client.send_email(
            >>>     message="Your message body",
            >>>     email_to="someone@email.com",
            >>>     subject="Example",
            >>>     html_content="<p>Your HTML message body</p>",
            >>> )
        """

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.email_from
        msg["To"] = email_to
        msg.set_content(message)

        if html_content:
            msg.add_alternative(html_content, subtype="html")

        if self._use_implicit_tls():
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                smtp.login(self.user_name, self.password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(self.user_name, self.password)
                smtp.send_message(msg)
