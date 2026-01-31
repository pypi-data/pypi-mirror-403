"""
NTLabs SDK - Async Email Resource Tests
Tests for the AsyncEmailResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
from unittest.mock import AsyncMock

from ntlabs.resources.async_email import AsyncEmailResource
from ntlabs.resources.email import EmailResult


@pytest.mark.asyncio
class TestAsyncEmailResource:
    """Tests for AsyncEmailResource."""

    async def test_initialization(self):
        """AsyncEmailResource initializes with client."""
        mock_client = AsyncMock()
        email = AsyncEmailResource(mock_client)
        assert email._client == mock_client


@pytest.mark.asyncio
class TestAsyncEmailSend:
    """Tests for async email sending."""

    async def test_send_basic(self, email_response):
        """Send basic email."""
        mock_client = AsyncMock()
        mock_client.post.return_value = email_response

        email = AsyncEmailResource(mock_client)
        result = await email.send(
            to=["user@example.com"],
            subject="Test Subject",
            html="<h1>Hello</h1>",
        )

        assert isinstance(result, EmailResult)
        assert result.id == "email-456"
        assert result.status == "sent"
        assert result.to == ["user@example.com"]
        assert result.subject == "Test Subject"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/email/send"
        assert call_args[1]["json"]["to"] == ["user@example.com"]
        assert call_args[1]["json"]["subject"] == "Test Subject"
        assert call_args[1]["json"]["html"] == "<h1>Hello</h1>"

    async def test_send_text_only(self, email_response):
        """Send text-only email."""
        mock_client = AsyncMock()
        mock_client.post.return_value = email_response

        email = AsyncEmailResource(mock_client)
        result = await email.send(
            to=["user@example.com"],
            subject="Test Subject",
            text="Hello, plain text!",
        )

        assert isinstance(result, EmailResult)
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["text"] == "Hello, plain text!"

    async def test_send_html_and_text(self, email_response):
        """Send email with both HTML and text."""
        mock_client = AsyncMock()
        mock_client.post.return_value = email_response

        email = AsyncEmailResource(mock_client)
        result = await email.send(
            to=["user@example.com"],
            subject="Test",
            html="<h1>Hello</h1>",
            text="Hello",
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["html"] == "<h1>Hello</h1>"
        assert call_args[1]["json"]["text"] == "Hello"

    async def test_send_without_content_raises(self):
        """Send email without content raises error."""
        mock_client = AsyncMock()
        email = AsyncEmailResource(mock_client)

        with pytest.raises(ValueError, match="Either html or text must be provided"):
            await email.send(
                to=["user@example.com"],
                subject="Test",
            )

    async def test_send_with_options(self, email_response):
        """Send email with all options."""
        mock_client = AsyncMock()
        mock_client.post.return_value = email_response

        email = AsyncEmailResource(mock_client)
        result = await email.send(
            to=["user@example.com", "other@example.com"],
            subject="Test",
            html="<h1>Hello</h1>",
            from_email="sender@example.com",
            from_name="Test Sender",
            reply_to="reply@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            tags={"campaign": "welcome", "user_id": "123"},
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["from_email"] == "sender@example.com"
        assert call_args[1]["json"]["from_name"] == "Test Sender"
        assert call_args[1]["json"]["reply_to"] == "reply@example.com"
        assert call_args[1]["json"]["cc"] == ["cc@example.com"]
        assert call_args[1]["json"]["bcc"] == ["bcc@example.com"]
        assert call_args[1]["json"]["tags"] == {"campaign": "welcome", "user_id": "123"}

    async def test_get_providers(self):
        """Get available providers."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "providers": [
                {"id": "resend", "name": "Resend", "available": True},
                {"id": "ses", "name": "AWS SES", "available": True},
            ]
        }

        email = AsyncEmailResource(mock_client)
        result = await email.get_providers()

        assert len(result) == 2
        assert result[0]["id"] == "resend"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/email/providers"

    async def test_health(self):
        """Check email health."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"status": "healthy", "provider": "resend"}

        email = AsyncEmailResource(mock_client)
        result = await email.health()

        assert result["status"] == "healthy"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/email/health"


@pytest.mark.asyncio
class TestAsyncEmailConvenience:
    """Tests for async convenience methods."""

    async def test_send_appointment_reminder(self, email_response):
        """Send appointment reminder."""
        mock_client = AsyncMock()
        mock_client.post.return_value = email_response

        email = AsyncEmailResource(mock_client)
        result = await email.send_appointment_reminder(
            to="patient@example.com",
            name="João Silva",
            date="28/01/2026",
            time="14:00",
            location="UBS Centro",
            professional="Dr. Carlos",
            from_name="Sistema de Saúde",
        )

        assert isinstance(result, EmailResult)
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["to"] == ["patient@example.com"]
        assert "Lembrete" in call_args[1]["json"]["subject"]
        assert "João Silva" in call_args[1]["json"]["html"]
        assert "UBS Centro" in call_args[1]["json"]["html"]

    async def test_send_vaccination_alert(self, email_response):
        """Send vaccination alert."""
        mock_client = AsyncMock()
        mock_client.post.return_value = email_response

        email = AsyncEmailResource(mock_client)
        result = await email.send_vaccination_alert(
            to="patient@example.com",
            name="Maria Souza",
            vaccine_name="Hepatite B",
            due_date="15/02/2026",
            locations=["UBS Centro", "UBS Norte"],
            from_name="Sistema de Saúde",
        )

        assert isinstance(result, EmailResult)
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["to"] == ["patient@example.com"]
        assert "Vacina" in call_args[1]["json"]["subject"]
        assert "Hepatite B" in call_args[1]["json"]["subject"]
        assert "UBS Centro" in call_args[1]["json"]["html"]
        assert "UBS Norte" in call_args[1]["json"]["html"]
