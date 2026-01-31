"""
Neural LAB - AI Solutions Platform
Email Resource - Send emails via Resend.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from dataclasses import dataclass
from typing import Any

from ..base import DataclassMixin


@dataclass
class EmailResult(DataclassMixin):
    """Email sending result."""

    id: str
    status: str
    to: list[str]
    subject: str
    latency_ms: int
    cost_brl: float


class EmailResource:
    """
    Email resource for sending emails via Resend.

    Usage:
        result = client.email.send(
            to=["user@example.com"],
            subject="Bem-vindo!",
            html="<h1>Olá!</h1>",
        )
        print(result.id)
    """

    def __init__(self, client):
        self._client = client

    def send(
        self,
        to: list[str],
        subject: str,
        html: str | None = None,
        text: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        reply_to: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        tags: dict[str, str] | None = None,
    ) -> EmailResult:
        """
        Send an email.

        Args:
            to: List of recipient emails
            subject: Email subject
            html: HTML body (optional if text provided)
            text: Plain text body (optional if html provided)
            from_email: Sender email
            from_name: Sender name
            reply_to: Reply-to email
            cc: CC recipients
            bcc: BCC recipients
            tags: Email tags for tracking

        Returns:
            EmailResult with send status
        """
        if not html and not text:
            raise ValueError("Either html or text must be provided")

        payload = {
            "to": to,
            "subject": subject,
        }

        if html:
            payload["html"] = html
        if text:
            payload["text"] = text
        if from_email:
            payload["from_email"] = from_email
        if from_name:
            payload["from_name"] = from_name
        if reply_to:
            payload["reply_to"] = reply_to
        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc
        if tags:
            payload["tags"] = tags

        response = self._client.post("/v1/email/send", json=payload)

        return EmailResult(
            id=response.get("id", ""),
            status=response.get("status", "sent"),
            to=to,
            subject=subject,
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def get_providers(self) -> list[dict[str, Any]]:
        """
        Get available email providers.

        Returns:
            List of provider information
        """
        response = self._client.get("/v1/email/providers")
        return response.get("providers", [])

    def health(self) -> dict[str, Any]:
        """
        Check email service health.

        Returns:
            Health status
        """
        return self._client.get("/v1/email/health")
