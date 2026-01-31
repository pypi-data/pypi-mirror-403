"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for SMTP email provider
Version: 1.0.0
"""

import ssl
from email.mime.multipart import MIMEMultipart
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ntlabs.email.models import Attachment, EmailMessage
from ntlabs.email.providers.smtp import SMTPProvider


class TestSMTPProviderInit:
    """Test SMTPProvider initialization."""

    def test_default_init(self):
        """Test initialization with default values."""
        provider = SMTPProvider(host="smtp.example.com")
        assert provider.host == "smtp.example.com"
        assert provider.port == 587
        assert provider.use_tls is True
        assert provider.use_ssl is False
        assert provider.timeout == 30.0

    def test_custom_init(self):
        """Test initialization with custom values."""
        custom_ssl = ssl.create_default_context()
        provider = SMTPProvider(
            host="smtp.gmail.com",
            port=465,
            username="user@gmail.com",
            password="password123",
            use_tls=False,
            use_ssl=True,
            from_email="sender@gmail.com",
            from_name="Test Sender",
            timeout=60.0,
            ssl_context=custom_ssl,
        )
        assert provider.host == "smtp.gmail.com"
        assert provider.port == 465
        assert provider.username == "user@gmail.com"
        assert provider.password == "password123"
        assert provider.use_tls is False
        assert provider.use_ssl is True
        assert provider.from_email == "sender@gmail.com"
        assert provider.from_name == "Test Sender"
        assert provider.timeout == 60.0
        assert provider.ssl_context is custom_ssl

    def test_provider_name(self):
        """Test provider name property."""
        provider = SMTPProvider(host="smtp.example.com")
        assert provider.provider_name == "smtp"

    def test_ssl_context_default(self):
        """Test that default SSL context is created."""
        provider = SMTPProvider(host="smtp.example.com")
        assert isinstance(provider.ssl_context, ssl.SSLContext)


class TestSMTPProviderSend:
    """Test sending emails."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance."""
        return SMTPProvider(
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="sender@example.com",
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
        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.send(basic_message)

            assert result.success is True
            assert result.provider == "smtp"
            assert result.message_id is not None
            mock_smtp.login.assert_called_once_with("user", "pass")
            mock_smtp.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_with_html(self, provider):
        """Test sending email with HTML content."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            html="<h1>Hello</h1>",
        )

        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.send(message)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_send_with_cc(self, provider):
        """Test sending email with CC."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Body",
            cc=["cc@example.com"],
        )

        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.send(message)
            assert result.success is True

            # Check recipients include CC
            call_args = mock_smtp.send_message.call_args
            recipients = call_args[1]["recipients"]
            assert "cc@example.com" in recipients

    @pytest.mark.asyncio
    async def test_send_with_reply_to(self, provider):
        """Test sending email with reply-to."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Body",
            reply_to="reply@example.com",
        )

        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.send(message)
            assert result.success is True

            # Check Reply-To header
            call_args = mock_smtp.send_message.call_args
            mime_message = call_args[0][0]
            assert mime_message["Reply-To"] == "reply@example.com"

    @pytest.mark.asyncio
    async def test_send_with_custom_headers(self, provider):
        """Test sending email with custom headers."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Body",
            headers={"X-Custom-Header": "custom-value"},
        )

        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.send(message)
            assert result.success is True

            # Check custom header
            call_args = mock_smtp.send_message.call_args
            mime_message = call_args[0][0]
            assert mime_message["X-Custom-Header"] == "custom-value"

    @pytest.mark.asyncio
    async def test_send_with_attachment(self, provider):
        """Test sending email with attachment."""
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

        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.send(message)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_send_with_content_id(self, provider):
        """Test sending email with content ID for inline attachments."""
        attachment = Attachment(
            filename="image.png",
            content=b"PNG data",
            content_type="image/png",
            content_id="image001",
        )
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Body",
            attachments=[attachment],
        )

        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.send(message)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_send_smtp_error(self, provider, basic_message):
        """Test handling SMTP error."""
        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock(side_effect=Exception("SMTP error"))

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.send(basic_message)

            assert result.success is False
            assert "SMTP error" in result.error

    @pytest.mark.asyncio
    async def test_send_with_ssl(self, basic_message):
        """Test sending with SSL connection."""
        provider = SMTPProvider(
            host="smtp.gmail.com",
            port=465,
            use_ssl=True,
            from_email="sender@example.com",
        )

        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.send_message = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp) as mock_smtp_class:
            result = await provider.send(basic_message)
            assert result.success is True

            # Check SSL was used
            call_kwargs = mock_smtp_class.call_args[1]
            assert call_kwargs["use_tls"] is True

    @pytest.mark.asyncio
    async def test_send_with_tls(self, basic_message):
        """Test sending with TLS connection."""
        provider = SMTPProvider(
            host="smtp.example.com",
            port=587,
            use_tls=True,
            from_email="sender@example.com",
        )

        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.send_message = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp) as mock_smtp_class:
            result = await provider.send(basic_message)
            assert result.success is True

            # Check TLS options
            call_kwargs = mock_smtp_class.call_args[1]
            assert call_kwargs["start_tls"] is True

    @pytest.mark.asyncio
    async def test_send_without_auth(self, basic_message):
        """Test sending without authentication."""
        provider = SMTPProvider(
            host="smtp.example.com",
            from_email="sender@example.com",
        )

        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.send(basic_message)
            assert result.success is True
            mock_smtp.login.assert_not_called()


class TestSMTPProviderBuildMime:
    """Test MIME message building."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance."""
        return SMTPProvider(
            host="smtp.example.com",
            from_email="sender@example.com",
            from_name="Test Sender",
        )

    def test_build_basic_message(self, provider):
        """Test building basic MIME message."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            text="Test body",
        )

        # Prepare message with defaults
        message = provider._prepare_message(message)
        mime = provider._build_mime_message(message)

        assert isinstance(mime, MIMEMultipart)
        assert mime["Subject"] == "Test Subject"
        assert mime["From"] == "Test Sender <sender@example.com>"
        assert mime["To"] == "recipient@example.com"

    def test_build_with_multiple_recipients(self, provider):
        """Test building message with multiple recipients."""
        message = EmailMessage(
            to=["user1@example.com", "user2@example.com"],
            subject="Test",
            text="Body",
        )

        message = provider._prepare_message(message)
        mime = provider._build_mime_message(message)
        assert mime["To"] == "user1@example.com, user2@example.com"

    def test_build_with_cc(self, provider):
        """Test building message with CC."""
        message = EmailMessage(
            to=["to@example.com"],
            cc=["cc@example.com"],
            subject="Test",
            text="Body",
        )

        message = provider._prepare_message(message)
        mime = provider._build_mime_message(message)
        assert mime["Cc"] == "cc@example.com"

    def test_build_with_html_and_text(self, provider):
        """Test building message with both HTML and text."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            text="Plain text",
            html="<p>HTML</p>",
        )

        message = provider._prepare_message(message)
        mime = provider._build_mime_message(message)
        parts = list(mime.walk())

        content_types = [p.get_content_type() for p in parts]
        assert "text/plain" in content_types
        assert "text/html" in content_types


class TestSMTPProviderHealthCheck:
    """Test health check functionality."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance."""
        return SMTPProvider(
            host="smtp.example.com",
            port=587,
            from_email="sender@example.com",
        )

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, provider):
        """Test healthy status."""
        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.health_check()

            assert result["healthy"] is True
            assert result["provider"] == "smtp"
            assert result["host"] == "smtp.example.com"
            assert result["port"] == 587

    @pytest.mark.asyncio
    async def test_health_check_with_starttls(self, provider):
        """Test health check with STARTTLS."""
        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)
        mock_smtp.starttls = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.health_check()
            assert result["healthy"] is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, provider):
        """Test unhealthy status."""
        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.health_check()

            assert result["healthy"] is False
            assert "Connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_with_ssl(self):
        """Test health check with SSL connection."""
        provider = SMTPProvider(
            host="smtp.gmail.com",
            port=465,
            use_ssl=True,
            from_email="sender@example.com",
        )

        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
        mock_smtp.__aexit__ = AsyncMock(return_value=None)

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await provider.health_check()
            assert result["healthy"] is True
