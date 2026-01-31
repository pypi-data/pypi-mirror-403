"""
SMTP email provider.

Standard SMTP provider for sending emails via any SMTP server.
"""

import logging
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from ..models import EmailMessage, EmailResult
from .base import BaseEmailProvider

logger = logging.getLogger(__name__)


class SMTPProvider(BaseEmailProvider):
    """
    SMTP email provider.

    Supports standard SMTP with TLS/SSL.

    Example:
        provider = SMTPProvider(
            host="smtp.gmail.com",
            port=587,
            username="user@gmail.com",
            password="app_password",
            use_tls=True,
            from_email="user@gmail.com",
            from_name="My App"
        )

        result = await provider.send(EmailMessage(
            to=["recipient@example.com"],
            subject="Hello!",
            html="<h1>Hello World</h1>"
        ))
    """

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
        use_ssl: bool = False,
        from_email: str | None = None,
        from_name: str | None = None,
        timeout: float = 30.0,
        ssl_context: ssl.SSLContext | None = None,
    ):
        """
        Initialize SMTP provider.

        Args:
            host: SMTP server hostname
            port: SMTP port (25, 465, 587)
            username: SMTP username
            password: SMTP password
            use_tls: Use STARTTLS (port 587)
            use_ssl: Use SSL/TLS (port 465)
            from_email: Default sender email
            from_name: Default sender name
            timeout: Connection timeout
            ssl_context: Custom SSL context
        """
        super().__init__(from_email=from_email, from_name=from_name)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.ssl_context = ssl_context or ssl.create_default_context()

    @property
    def provider_name(self) -> str:
        return "smtp"

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send email via SMTP.

        Args:
            message: Email message to send

        Returns:
            EmailResult
        """
        message = self._prepare_message(message)

        try:
            # Build MIME message
            mime_message = self._build_mime_message(message)

            # Send via SMTP
            await self._send_smtp(mime_message, message.all_recipients)

            # Generate a pseudo message ID
            import uuid

            message_id = f"{uuid.uuid4()}@{self.host}"

            return EmailResult.success_result(
                message_id=message_id,
                provider=self.provider_name,
            )

        except Exception as e:
            logger.exception(f"SMTP send error: {e}")
            return EmailResult.failure_result(
                error=str(e),
                provider=self.provider_name,
            )

    async def _send_smtp(
        self, mime_message: MIMEMultipart, recipients: list[str]
    ) -> None:
        """Send message via SMTP."""
        import aiosmtplib

        smtp_kwargs = {
            "hostname": self.host,
            "port": self.port,
            "timeout": self.timeout,
        }

        if self.use_ssl:
            smtp_kwargs["use_tls"] = True
            smtp_kwargs["tls_context"] = self.ssl_context
        elif self.use_tls:
            smtp_kwargs["start_tls"] = True
            smtp_kwargs["tls_context"] = self.ssl_context

        async with aiosmtplib.SMTP(**smtp_kwargs) as smtp:
            if self.username and self.password:
                await smtp.login(self.username, self.password)

            await smtp.send_message(mime_message, recipients=recipients)

    def _build_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """Build MIME message from EmailMessage."""
        mime = MIMEMultipart("alternative")

        # Headers
        mime["Subject"] = message.subject
        mime["From"] = self._format_from(message)
        mime["To"] = ", ".join(message.to)

        if message.cc:
            mime["Cc"] = ", ".join(message.cc)
        if message.reply_to:
            mime["Reply-To"] = message.reply_to

        # Custom headers
        for key, value in message.headers.items():
            mime[key] = value

        # Content
        if message.text:
            text_part = MIMEText(message.text, "plain", "utf-8")
            mime.attach(text_part)

        if message.html:
            html_part = MIMEText(message.html, "html", "utf-8")
            mime.attach(html_part)

        # Attachments
        for attachment in message.attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.content)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f'attachment; filename="{attachment.filename}"'
            )
            if attachment.content_id:
                part.add_header("Content-ID", f"<{attachment.content_id}>")
            mime.attach(part)

        return mime

    async def health_check(self) -> dict[str, Any]:
        """Check SMTP server connectivity."""
        try:
            import aiosmtplib

            smtp_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "timeout": self.timeout,
            }

            if self.use_ssl:
                smtp_kwargs["use_tls"] = True
                smtp_kwargs["tls_context"] = self.ssl_context

            async with aiosmtplib.SMTP(**smtp_kwargs) as smtp:
                # Just connecting is enough to verify
                if self.use_tls and not self.use_ssl:
                    await smtp.starttls(tls_context=self.ssl_context)

                return {
                    "healthy": True,
                    "provider": self.provider_name,
                    "host": self.host,
                    "port": self.port,
                }

        except Exception as e:
            return {
                "healthy": False,
                "provider": self.provider_name,
                "host": self.host,
                "port": self.port,
                "error": str(e),
            }

    def _format_from(self, message: EmailMessage) -> str:
        """Format from address."""
        if message.from_name:
            return f"{message.from_name} <{message.from_email}>"
        return message.from_email
