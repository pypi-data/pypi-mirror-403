"""
Email service - High-level email sending interface.

Provides a unified interface for sending emails through different providers.
"""

import logging
from typing import Any

from .models import Attachment, BatchEmailResult, EmailMessage, EmailResult
from .providers.base import BaseEmailProvider
from .providers.resend import ResendProvider
from .providers.smtp import SMTPProvider
from .templates.renderer import TemplateRenderer

logger = logging.getLogger(__name__)


class EmailService:
    """
    High-level email service.

    Supports multiple providers and template rendering.

    Example:
        # Using Resend
        email = EmailService(
            provider="resend",
            api_key="re_xxx",
            from_email="noreply@example.com",
            from_name="My App",
        )

        # Using SMTP
        email = EmailService(
            provider="smtp",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="user@gmail.com",
            smtp_password="app_password",
            from_email="user@gmail.com",
        )

        # Send simple email
        result = await email.send(
            to=["user@example.com"],
            subject="Hello!",
            html="<h1>Hello World</h1>",
        )

        # Send with template
        result = await email.send_template(
            to=["user@example.com"],
            subject="Welcome!",
            template="welcome",
            context={"user_name": "John", "company_name": "Acme Inc"},
        )
    """

    def __init__(
        self,
        provider: str = "resend",
        # Resend settings
        api_key: str | None = None,
        # SMTP settings
        smtp_host: str | None = None,
        smtp_port: int = 587,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        smtp_use_tls: bool = True,
        smtp_use_ssl: bool = False,
        # Common settings
        from_email: str | None = None,
        from_name: str | None = None,
        template_dir: str | None = None,
        # Advanced
        timeout: float = 30.0,
    ):
        """
        Initialize email service.

        Args:
            provider: Provider name ("resend" or "smtp")
            api_key: Resend API key
            smtp_host: SMTP server host
            smtp_port: SMTP port
            smtp_user: SMTP username
            smtp_password: SMTP password
            smtp_use_tls: Use STARTTLS
            smtp_use_ssl: Use SSL
            from_email: Default sender email
            from_name: Default sender name
            template_dir: Directory for email templates
            timeout: Request/connection timeout
        """
        self.from_email = from_email
        self.from_name = from_name

        # Initialize provider
        self._provider = self._create_provider(
            provider=provider,
            api_key=api_key,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            smtp_use_tls=smtp_use_tls,
            smtp_use_ssl=smtp_use_ssl,
            from_email=from_email,
            from_name=from_name,
            timeout=timeout,
        )

        # Initialize template renderer
        self._renderer = TemplateRenderer(template_dir=template_dir)

    def _create_provider(self, provider: str, **kwargs) -> BaseEmailProvider:
        """Create email provider instance."""
        provider = provider.lower()

        if provider == "resend":
            if not kwargs.get("api_key"):
                raise ValueError("api_key is required for Resend provider")

            return ResendProvider(
                api_key=kwargs["api_key"],
                from_email=kwargs.get("from_email"),
                from_name=kwargs.get("from_name"),
                timeout=kwargs.get("timeout", 30.0),
            )

        elif provider == "smtp":
            if not kwargs.get("smtp_host"):
                raise ValueError("smtp_host is required for SMTP provider")

            return SMTPProvider(
                host=kwargs["smtp_host"],
                port=kwargs.get("smtp_port", 587),
                username=kwargs.get("smtp_user"),
                password=kwargs.get("smtp_password"),
                use_tls=kwargs.get("smtp_use_tls", True),
                use_ssl=kwargs.get("smtp_use_ssl", False),
                from_email=kwargs.get("from_email"),
                from_name=kwargs.get("from_name"),
                timeout=kwargs.get("timeout", 30.0),
            )

        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def send(
        self,
        to: str | list[str],
        subject: str,
        html: str | None = None,
        text: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        reply_to: str | None = None,
        attachments: list[Attachment] | None = None,
        headers: dict[str, str] | None = None,
        tags: list[str] | None = None,
    ) -> EmailResult:
        """
        Send an email.

        Args:
            to: Recipient(s)
            subject: Email subject
            html: HTML content
            text: Plain text content
            from_email: Sender email (overrides default)
            from_name: Sender name (overrides default)
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            reply_to: Reply-to address
            attachments: File attachments
            headers: Custom headers
            tags: Tags for tracking

        Returns:
            EmailResult
        """
        # Normalize inputs
        if isinstance(to, str):
            to = [to]
        if isinstance(cc, str):
            cc = [cc]
        if isinstance(bcc, str):
            bcc = [bcc]

        message = EmailMessage(
            to=to,
            subject=subject,
            html=html,
            text=text,
            from_email=from_email or self.from_email,
            from_name=from_name or self.from_name,
            cc=cc or [],
            bcc=bcc or [],
            reply_to=reply_to,
            attachments=attachments or [],
            headers=headers or {},
            tags=tags or [],
        )

        return await self._provider.send(message)

    async def send_template(
        self,
        to: str | list[str],
        subject: str,
        template: str,
        context: dict[str, Any],
        from_email: str | None = None,
        from_name: str | None = None,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        reply_to: str | None = None,
        attachments: list[Attachment] | None = None,
        headers: dict[str, str] | None = None,
        tags: list[str] | None = None,
    ) -> EmailResult:
        """
        Send an email using a template.

        Args:
            to: Recipient(s)
            subject: Email subject
            template: Template name
            context: Template variables
            from_email: Sender email
            from_name: Sender name
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            reply_to: Reply-to address
            attachments: File attachments
            headers: Custom headers
            tags: Tags for tracking

        Returns:
            EmailResult
        """
        # Add common context
        from datetime import datetime

        full_context = {
            "year": datetime.now().year,
            "company_name": self.from_name or "Neural Thinkers",
            **context,
        }

        # Render template
        html = self._renderer.render(template, full_context)

        return await self.send(
            to=to,
            subject=subject,
            html=html,
            from_email=from_email,
            from_name=from_name,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            attachments=attachments,
            headers=headers,
            tags=tags,
        )

    async def send_batch(
        self, messages: list[EmailMessage], max_concurrent: int = 5
    ) -> BatchEmailResult:
        """
        Send multiple emails.

        Args:
            messages: List of EmailMessage objects
            max_concurrent: Maximum concurrent sends

        Returns:
            BatchEmailResult with overall statistics
        """
        results = await self._provider.send_batch(messages, max_concurrent)

        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        return BatchEmailResult(
            total=len(results),
            success_count=success_count,
            failure_count=failure_count,
            results=results,
        )

    async def health_check(self) -> dict[str, Any]:
        """Check email service health."""
        return await self._provider.health_check()

    async def close(self):
        """Close provider connections."""
        if hasattr(self._provider, "close"):
            await self._provider.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
