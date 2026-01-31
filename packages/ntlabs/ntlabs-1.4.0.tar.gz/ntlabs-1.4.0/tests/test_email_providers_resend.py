"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for Resend email provider
Version: 1.0.0
"""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ntlabs.email.models import Attachment, EmailMessage
from ntlabs.email.providers.resend import ResendProvider


class TestResendProviderInit:
    """Test ResendProvider initialization."""

    def test_default_init(self):
        """Test initialization with default values."""
        provider = ResendProvider(api_key="test_key")
        assert provider.api_key == "test_key"
        assert provider.base_url == "https://api.resend.com"
        assert provider.timeout == 30.0
        assert provider._client is None

    def test_custom_init(self):
        """Test initialization with custom values."""
        provider = ResendProvider(
            api_key="test_key",
            from_email="sender@example.com",
            from_name="Test Sender",
            base_url="https://custom.resend.com",
            timeout=60.0,
        )
        assert provider.api_key == "test_key"
        assert provider.from_email == "sender@example.com"
        assert provider.from_name == "Test Sender"
        assert provider.base_url == "https://custom.resend.com"
        assert provider.timeout == 60.0

    def test_provider_name(self):
        """Test provider name property."""
        provider = ResendProvider(api_key="test_key")
        assert provider.provider_name == "resend"


class TestResendProviderClient:
    """Test HTTP client management."""

    @pytest.mark.asyncio
    async def test_get_client(self):
        """Test getting/creating HTTP client."""
        provider = ResendProvider(api_key="test_key")

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance

            client = await provider._get_client()
            assert client is mock_instance
            mock_client.assert_called_once()

            # Second call should return same instance
            client2 = await provider._get_client()
            assert client2 is client
            mock_client.assert_called_once()  # Not called again

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing HTTP client."""
        provider = ResendProvider(api_key="test_key")

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance

            await provider._get_client()
            await provider.close()

            mock_instance.aclose.assert_called_once()
            assert provider._client is None


class TestResendProviderSend:
    """Test sending emails."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance."""
        return ResendProvider(
            api_key="test_key",
            from_email="sender@example.com",
            from_name="Test Sender",
        )

    @pytest.fixture
    def basic_message(self):
        """Create a basic email message."""
        return EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            text="Test body",
        )

    @pytest.mark.asyncio
    async def test_send_success(self, provider, basic_message):
        """Test successful email send."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "message_123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.send(basic_message)

            assert result.success is True
            assert result.message_id == "message_123"
            assert result.provider == "resend"

    @pytest.mark.asyncio
    async def test_send_with_html(self, provider):
        """Test sending email with HTML content."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            html="<h1>Hello</h1>",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.send(message)
            assert result.success is True

            # Check that HTML was included in payload
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["html"] == "<h1>Hello</h1>"

    @pytest.mark.asyncio
    async def test_send_with_cc_bcc(self, provider):
        """Test sending email with CC and BCC."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.send(message)

            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["cc"] == ["cc@example.com"]
            assert payload["bcc"] == ["bcc@example.com"]

    @pytest.mark.asyncio
    async def test_send_with_reply_to(self, provider):
        """Test sending email with reply-to."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Body",
            reply_to="reply@example.com",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.send(message)

            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["reply_to"] == "reply@example.com"

    @pytest.mark.asyncio
    async def test_send_with_headers(self, provider):
        """Test sending email with custom headers."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Body",
            headers={"X-Custom-Header": "value"},
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.send(message)

            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["headers"] == {"X-Custom-Header": "value"}

    @pytest.mark.asyncio
    async def test_send_with_tags(self, provider):
        """Test sending email with tags."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Body",
            tags=["welcome", "new-user"],
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.send(message)

            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["tags"] == [{"name": "welcome"}, {"name": "new-user"}]

    @pytest.mark.asyncio
    async def test_send_with_attachments(self, provider):
        """Test sending email with attachments."""
        attachment = Attachment(
            filename="test.pdf",
            content=b"PDF content",
            content_type="application/pdf",
        )
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Body",
            attachments=[attachment],
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.send(message)

            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert "attachments" in payload
            assert len(payload["attachments"]) == 1
            assert payload["attachments"][0]["filename"] == "test.pdf"
            assert payload["attachments"][0]["type"] == "application/pdf"
            # Content should be base64 encoded
            decoded = base64.b64decode(payload["attachments"][0]["content"])
            assert decoded == b"PDF content"

    @pytest.mark.asyncio
    async def test_send_api_error(self, provider, basic_message):
        """Test handling API error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"message": "Invalid email"}'
        mock_response.json.return_value = {"message": "Invalid email"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.send(basic_message)

            assert result.success is False
            assert "Invalid email" in result.error

    @pytest.mark.asyncio
    async def test_send_network_error(self, provider, basic_message):
        """Test handling network error."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Connection error")

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.send(basic_message)

            assert result.success is False
            assert "Connection error" in result.error

    @pytest.mark.asyncio
    async def test_send_with_custom_from(self, provider):
        """Test sending with custom from address."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Body",
            from_email="custom@example.com",
            from_name="Custom Name",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.send(message)

            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["from"] == "Custom Name <custom@example.com>"


class TestResendProviderBatch:
    """Test batch email sending."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance."""
        return ResendProvider(api_key="test_key", from_email="sender@example.com")

    @pytest.mark.asyncio
    async def test_send_batch_native(self, provider):
        """Test batch sending using native API."""
        messages = [
            EmailMessage(to=[f"user{i}@example.com"], subject="Test", text="Body")
            for i in range(5)
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": f"msg_{i}"} for i in range(5)]
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            results = await provider.send_batch(messages)

            assert len(results) == 5
            assert all(r.success for r in results)
            assert all(r.message_id for r in results)

    @pytest.mark.asyncio
    async def test_send_batch_falls_back_to_concurrent(self, provider):
        """Test batch fallback when more than 100 messages."""
        messages = [
            EmailMessage(to=[f"user{i}@example.com"], subject="Test", text="Body")
            for i in range(101)
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            results = await provider.send_batch(messages)

            assert len(results) == 101

    @pytest.mark.asyncio
    async def test_send_batch_native_error(self, provider):
        """Test batch sending with API error."""
        messages = [
            EmailMessage(to=["user@example.com"], subject="Test", text="Body")
        ]

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            results = await provider.send_batch(messages)

            assert len(results) == 1
            assert results[0].success is False

    @pytest.mark.asyncio
    async def test_send_batch_native_exception(self, provider):
        """Test batch sending with exception."""
        messages = [
            EmailMessage(to=["user@example.com"], subject="Test", text="Body")
        ]

        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Network error")

        with patch.object(provider, "_get_client", return_value=mock_client):
            results = await provider.send_batch(messages)

            assert len(results) == 1
            assert results[0].success is False


class TestResendProviderHealthCheck:
    """Test health check functionality."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance."""
        return ResendProvider(api_key="test_key")

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, provider):
        """Test healthy status."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.health_check()

            assert result["healthy"] is True
            assert result["provider"] == "resend"
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, provider):
        """Test unhealthy status."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.health_check()

            assert result["healthy"] is False
            assert result["status_code"] == 401

    @pytest.mark.asyncio
    async def test_health_check_error(self, provider):
        """Test health check with exception."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection failed")

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.health_check()

            assert result["healthy"] is False
            assert "Connection failed" in result["error"]
