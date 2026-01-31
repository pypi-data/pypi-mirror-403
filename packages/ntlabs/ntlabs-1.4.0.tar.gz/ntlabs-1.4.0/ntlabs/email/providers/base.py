"""
Base email provider interface.

All email providers must implement this abstract class.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..models import EmailMessage, EmailResult


class BaseEmailProvider(ABC):
    """
    Abstract base class for email providers.

    Implementations:
    - ResendProvider: Resend.com API
    - SMTPProvider: Standard SMTP
    """

    def __init__(
        self, from_email: str | None = None, from_name: str | None = None, **kwargs
    ):
        """
        Initialize provider.

        Args:
            from_email: Default sender email
            from_name: Default sender name
        """
        self.from_email = from_email
        self.from_name = from_name

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass

    @abstractmethod
    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send a single email.

        Args:
            message: Email message to send

        Returns:
            EmailResult with success/failure info
        """
        pass

    async def send_batch(
        self, messages: list[EmailMessage], max_concurrent: int = 5
    ) -> list[EmailResult]:
        """
        Send multiple emails.

        Default implementation sends sequentially with concurrency limit.
        Providers may override for better batch support.

        Args:
            messages: List of email messages
            max_concurrent: Maximum concurrent sends

        Returns:
            List of EmailResult for each message
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_with_limit(msg):
            async with semaphore:
                return await self.send(msg)

        tasks = [send_with_limit(msg) for msg in messages]
        return await asyncio.gather(*tasks)

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Check provider health/connectivity.

        Returns:
            Dict with healthy status and provider info
        """
        pass

    def _prepare_message(self, message: EmailMessage) -> EmailMessage:
        """
        Prepare message with defaults.

        Args:
            message: Original message

        Returns:
            Message with defaults applied
        """
        # Apply default from_email if not set
        if not message.from_email:
            message.from_email = self.from_email
        if not message.from_name:
            message.from_name = self.from_name

        return message
