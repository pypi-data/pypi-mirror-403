"""
Email data models.

Provides data classes for email operations:
- EmailMessage: Represents an email to be sent
- Attachment: File attachment
- EmailResult: Result of email send operation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EmailStatus(Enum):
    """Email sending status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


@dataclass
class Attachment:
    """
    Email attachment.

    Example:
        attachment = Attachment(
            filename="report.pdf",
            content=pdf_bytes,
            content_type="application/pdf"
        )
    """

    filename: str
    content: bytes
    content_type: str = "application/octet-stream"
    content_id: str | None = None  # For inline attachments

    def __post_init__(self):
        if not self.filename:
            raise ValueError("Attachment filename is required")
        if not self.content:
            raise ValueError("Attachment content is required")


@dataclass
class EmailAddress:
    """
    Email address with optional display name.

    Example:
        addr = EmailAddress("user@example.com", "John Doe")
        str(addr)  # "John Doe <user@example.com>"
    """

    email: str
    name: str | None = None

    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email

    @classmethod
    def parse(cls, value: str) -> "EmailAddress":
        """Parse email string like 'Name <email@example.com>'."""
        import re

        match = re.match(r"(.+?)\s*<(.+?)>", value)
        if match:
            return cls(email=match.group(2).strip(), name=match.group(1).strip())
        return cls(email=value.strip())


@dataclass
class EmailMessage:
    """
    Email message to be sent.

    Example:
        message = EmailMessage(
            to=["user@example.com"],
            subject="Hello!",
            html="<h1>Hello World</h1>",
            text="Hello World",
        )
    """

    to: list[str]
    subject: str
    html: str | None = None
    text: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    reply_to: str | None = None
    attachments: list[Attachment] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Normalize to list
        if isinstance(self.to, str):
            self.to = [self.to]
        if isinstance(self.cc, str):
            self.cc = [self.cc]
        if isinstance(self.bcc, str):
            self.bcc = [self.bcc]

        # Validate
        if not self.to:
            raise ValueError("At least one recipient is required")
        if not self.subject:
            raise ValueError("Subject is required")
        if not self.html and not self.text:
            raise ValueError("Either html or text content is required")

    @property
    def all_recipients(self) -> list[str]:
        """Get all recipients (to + cc + bcc)."""
        return self.to + self.cc + self.bcc


@dataclass
class EmailResult:
    """
    Result of an email send operation.

    Example:
        result = await email.send(message)
        if result.success:
            print(f"Sent! ID: {result.message_id}")
        else:
            print(f"Failed: {result.error}")
    """

    success: bool
    message_id: str | None = None
    error: str | None = None
    status: EmailStatus = EmailStatus.PENDING
    sent_at: datetime | None = None
    provider: str | None = None
    raw_response: dict[str, Any] | None = None

    @classmethod
    def success_result(
        cls, message_id: str, provider: str, raw_response: dict | None = None
    ) -> "EmailResult":
        """Create a success result."""
        return cls(
            success=True,
            message_id=message_id,
            status=EmailStatus.SENT,
            sent_at=datetime.utcnow(),
            provider=provider,
            raw_response=raw_response,
        )

    @classmethod
    def failure_result(
        cls, error: str, provider: str | None = None, raw_response: dict | None = None
    ) -> "EmailResult":
        """Create a failure result."""
        return cls(
            success=False,
            error=error,
            status=EmailStatus.FAILED,
            provider=provider,
            raw_response=raw_response,
        )


@dataclass
class BatchEmailResult:
    """
    Result of a batch email send operation.

    Example:
        results = await email.send_batch(messages)
        print(f"Sent: {results.success_count}, Failed: {results.failure_count}")
    """

    total: int
    success_count: int
    failure_count: int
    results: list[EmailResult] = field(default_factory=list)

    @property
    def all_successful(self) -> bool:
        """Check if all emails were sent successfully."""
        return self.failure_count == 0

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.success_count / self.total) * 100
