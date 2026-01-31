"""
Resend email provider.

Resend (https://resend.com) is a modern email API
for developers.
"""

import logging
from typing import Any

from ..models import EmailMessage, EmailResult
from .base import BaseEmailProvider

logger = logging.getLogger(__name__)


class ResendProvider(BaseEmailProvider):
    """
    Resend.com email provider.

    Example:
        provider = ResendProvider(
            api_key="re_xxx",
            from_email="noreply@example.com",
            from_name="My App"
        )

        result = await provider.send(EmailMessage(
            to=["user@example.com"],
            subject="Hello!",
            html="<h1>Hello World</h1>"
        ))
    """

    def __init__(
        self,
        api_key: str,
        from_email: str | None = None,
        from_name: str | None = None,
        base_url: str = "https://api.resend.com",
        timeout: float = 30.0,
    ):
        """
        Initialize Resend provider.

        Args:
            api_key: Resend API key
            from_email: Default sender email
            from_name: Default sender name
            base_url: Resend API base URL
            timeout: Request timeout in seconds
        """
        super().__init__(from_email=from_email, from_name=from_name)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = None

    @property
    def provider_name(self) -> str:
        return "resend"

    async def _get_client(self):
        """Get or create httpx client."""
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send email via Resend API.

        Args:
            message: Email message to send

        Returns:
            EmailResult
        """
        message = self._prepare_message(message)

        try:
            client = await self._get_client()

            # Build request payload
            payload = {
                "from": self._format_from(message),
                "to": message.to,
                "subject": message.subject,
            }

            if message.html:
                payload["html"] = message.html
            if message.text:
                payload["text"] = message.text
            if message.cc:
                payload["cc"] = message.cc
            if message.bcc:
                payload["bcc"] = message.bcc
            if message.reply_to:
                payload["reply_to"] = message.reply_to
            if message.headers:
                payload["headers"] = message.headers
            if message.tags:
                payload["tags"] = [{"name": tag} for tag in message.tags]

            # Handle attachments
            if message.attachments:
                import base64

                payload["attachments"] = [
                    {
                        "filename": att.filename,
                        "content": base64.b64encode(att.content).decode("utf-8"),
                        "type": att.content_type,
                    }
                    for att in message.attachments
                ]

            # Send request
            response = await client.post("/emails", json=payload)

            if response.status_code == 200:
                data = response.json()
                return EmailResult.success_result(
                    message_id=data.get("id"),
                    provider=self.provider_name,
                    raw_response=data,
                )
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
                logger.error(f"Resend API error: {error_msg}")
                return EmailResult.failure_result(
                    error=error_msg,
                    provider=self.provider_name,
                    raw_response=error_data,
                )

        except Exception as e:
            logger.exception(f"Resend send error: {e}")
            return EmailResult.failure_result(
                error=str(e),
                provider=self.provider_name,
            )

    async def send_batch(
        self, messages: list[EmailMessage], max_concurrent: int = 10
    ) -> list[EmailResult]:
        """
        Send batch emails via Resend.

        Resend has native batch support for up to 100 emails.
        """
        if len(messages) <= 100:
            # Use native batch API
            return await self._send_batch_native(messages)
        else:
            # Fall back to concurrent individual sends
            return await super().send_batch(messages, max_concurrent)

    async def _send_batch_native(
        self, messages: list[EmailMessage]
    ) -> list[EmailResult]:
        """Send batch using Resend's native batch API."""
        try:
            client = await self._get_client()

            payload = []
            for message in messages:
                message = self._prepare_message(message)
                item = {
                    "from": self._format_from(message),
                    "to": message.to,
                    "subject": message.subject,
                }
                if message.html:
                    item["html"] = message.html
                if message.text:
                    item["text"] = message.text
                payload.append(item)

            response = await client.post("/emails/batch", json=payload)

            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("data", []):
                    results.append(
                        EmailResult.success_result(
                            message_id=item.get("id"),
                            provider=self.provider_name,
                            raw_response=item,
                        )
                    )
                return results
            else:
                error_msg = f"Batch send failed: HTTP {response.status_code}"
                return [
                    EmailResult.failure_result(
                        error=error_msg, provider=self.provider_name
                    )
                    for _ in messages
                ]

        except Exception as e:
            logger.exception(f"Resend batch error: {e}")
            return [
                EmailResult.failure_result(error=str(e), provider=self.provider_name)
                for _ in messages
            ]

    async def health_check(self) -> dict[str, Any]:
        """Check Resend API connectivity."""
        try:
            client = await self._get_client()
            response = await client.get("/domains")

            return {
                "healthy": response.status_code == 200,
                "provider": self.provider_name,
                "status_code": response.status_code,
            }
        except Exception as e:
            return {
                "healthy": False,
                "provider": self.provider_name,
                "error": str(e),
            }

    def _format_from(self, message: EmailMessage) -> str:
        """Format from address."""
        if message.from_name:
            return f"{message.from_name} <{message.from_email}>"
        return message.from_email
