"""
NTLabs SDK - Email Resource Tests
Tests for the EmailResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest

from ntlabs.resources.email import EmailResource, EmailResult


class TestEmailResult:
    """Tests for EmailResult dataclass."""

    def test_create_result(self):
        """Create email result."""
        result = EmailResult(
            id="email-123",
            status="sent",
            to=["user@example.com"],
            subject="Test Subject",
            latency_ms=150,
            cost_brl=0.001,
        )
        assert result.id == "email-123"
        assert result.status == "sent"
        assert result.to == ["user@example.com"]
        assert result.subject == "Test Subject"
        assert result.latency_ms == 150
        assert result.cost_brl == 0.001


class TestEmailResource:
    """Tests for EmailResource."""

    def test_initialization(self, mock_client):
        """EmailResource initializes with client."""
        email = EmailResource(mock_client)
        assert email._client == mock_client

    def test_send_html(self, mock_client, mock_response, email_response):
        """Send email with HTML content."""
        mock_client._mock_http.request.return_value = mock_response(email_response)

        result = mock_client.email.send(
            to=["user@example.com"],
            subject="Welcome!",
            html="<h1>Hello</h1>",
        )

        assert isinstance(result, EmailResult)
        assert result.status == "sent"
        assert result.to == ["user@example.com"]

    def test_send_text(self, mock_client, mock_response, email_response):
        """Send email with plain text content."""
        mock_client._mock_http.request.return_value = mock_response(email_response)

        result = mock_client.email.send(
            to=["user@example.com"],
            subject="Welcome!",
            text="Hello World",
        )

        assert isinstance(result, EmailResult)

    def test_send_requires_content(self, mock_client):
        """Send email requires html or text."""
        with pytest.raises(ValueError) as exc_info:
            mock_client.email.send(
                to=["user@example.com"],
                subject="No content",
            )
        assert "Either html or text must be provided" in str(exc_info.value)

    def test_send_multiple_recipients(self, mock_client, mock_response, email_response):
        """Send email to multiple recipients."""
        mock_client._mock_http.request.return_value = mock_response(email_response)

        result = mock_client.email.send(
            to=["user1@example.com", "user2@example.com"],
            subject="Team Update",
            html="<p>Update content</p>",
        )

        assert isinstance(result, EmailResult)
        assert len(result.to) == 2

    def test_send_with_from_email(self, mock_client, mock_response, email_response):
        """Send email with custom from address."""
        mock_client._mock_http.request.return_value = mock_response(email_response)

        result = mock_client.email.send(
            to=["user@example.com"],
            subject="Custom Sender",
            html="<p>Content</p>",
            from_email="noreply@company.com",
            from_name="Company Name",
        )

        assert isinstance(result, EmailResult)

    def test_send_with_reply_to(self, mock_client, mock_response, email_response):
        """Send email with reply-to address."""
        mock_client._mock_http.request.return_value = mock_response(email_response)

        result = mock_client.email.send(
            to=["user@example.com"],
            subject="Reply Test",
            html="<p>Content</p>",
            reply_to="support@company.com",
        )

        assert isinstance(result, EmailResult)

    def test_send_with_cc_bcc(self, mock_client, mock_response, email_response):
        """Send email with CC and BCC."""
        mock_client._mock_http.request.return_value = mock_response(email_response)

        result = mock_client.email.send(
            to=["user@example.com"],
            subject="CC/BCC Test",
            html="<p>Content</p>",
            cc=["manager@company.com"],
            bcc=["archive@company.com"],
        )

        assert isinstance(result, EmailResult)

    def test_send_with_tags(self, mock_client, mock_response, email_response):
        """Send email with tracking tags."""
        mock_client._mock_http.request.return_value = mock_response(email_response)

        result = mock_client.email.send(
            to=["user@example.com"],
            subject="Tagged Email",
            html="<p>Content</p>",
            tags={"campaign": "welcome", "source": "signup"},
        )

        assert isinstance(result, EmailResult)

    def test_get_providers(self, mock_client, mock_response):
        """Get available email providers."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "providers": [
                    {"id": "resend", "name": "Resend", "status": "active"},
                    {"id": "sendgrid", "name": "SendGrid", "status": "inactive"},
                ]
            }
        )

        providers = mock_client.email.get_providers()

        assert len(providers) == 2
        assert providers[0]["id"] == "resend"

    def test_get_providers_empty(self, mock_client, mock_response):
        """Handle empty providers list."""
        mock_client._mock_http.request.return_value = mock_response({})

        providers = mock_client.email.get_providers()
        assert providers == []

    def test_health(self, mock_client, mock_response):
        """Check email service health."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "status": "healthy",
                "providers": {"resend": "up"},
            }
        )

        health = mock_client.email.health()

        assert health["status"] == "healthy"

    def test_send_empty_response(self, mock_client, mock_response):
        """Handle empty response gracefully."""
        mock_client._mock_http.request.return_value = mock_response({})

        result = mock_client.email.send(
            to=["user@example.com"],
            subject="Test",
            html="<p>Test</p>",
        )

        assert result.id == ""
        assert result.status == "sent"
        assert result.latency_ms == 0
        assert result.cost_brl == 0
