"""
NTLabs Email - Email sending utilities.

This module provides email sending functionality with:
- Multiple providers (Resend, SMTP)
- Template rendering with Jinja2
- Attachments support
- Batch sending

Quick Start:
    from ntlabs.email import EmailService, Attachment

    # Using Resend
    email = EmailService(
        provider="resend",
        api_key="re_xxx",
        from_email="noreply@example.com",
        from_name="My App",
    )

    # Simple email
    result = await email.send(
        to=["user@example.com"],
        subject="Hello!",
        html="<h1>Hello World</h1>",
    )

    # With template
    result = await email.send_template(
        to=["user@example.com"],
        subject="Welcome!",
        template="welcome",
        context={"user_name": "John"},
    )

    # With attachment
    result = await email.send(
        to=["user@example.com"],
        subject="Report",
        html="<p>See attached report.</p>",
        attachments=[
            Attachment(
                filename="report.pdf",
                content=pdf_bytes,
                content_type="application/pdf"
            )
        ],
    )

Context Manager:
    async with EmailService(provider="resend", api_key="re_xxx") as email:
        await email.send(to="user@example.com", subject="Hi", text="Hello")
"""

from .models import (
    Attachment,
    BatchEmailResult,
    EmailAddress,
    EmailMessage,
    EmailResult,
    EmailStatus,
)
from .providers import (
    BaseEmailProvider,
    ResendProvider,
    SMTPProvider,
)
from .service import EmailService
from .templates import (
    TemplateRenderer,
    get_builtin_templates,
)

__all__ = [
    # Main service
    "EmailService",
    # Models
    "EmailMessage",
    "EmailResult",
    "BatchEmailResult",
    "Attachment",
    "EmailAddress",
    "EmailStatus",
    # Providers
    "BaseEmailProvider",
    "ResendProvider",
    "SMTPProvider",
    # Templates
    "TemplateRenderer",
    "get_builtin_templates",
]
