"""
Tests for ntlabs.email module.

Tests email models, providers, and service.
"""

import pytest

from ntlabs.email import (
    Attachment,
    BatchEmailResult,
    EmailAddress,
    # Models
    EmailMessage,
    EmailResult,
    # Service
    EmailService,
    EmailStatus,
)

# =============================================================================
# Email Models Tests
# =============================================================================


class TestEmailModels:
    """Tests for email data models."""

    def test_attachment_creation(self):
        """Test Attachment creation."""
        attachment = Attachment(
            filename="report.pdf",
            content=b"PDF content",
            content_type="application/pdf",
        )
        assert attachment.filename == "report.pdf"
        assert attachment.content == b"PDF content"
        assert attachment.content_type == "application/pdf"

    def test_attachment_requires_filename(self):
        """Test Attachment requires filename."""
        with pytest.raises(ValueError) as exc_info:
            Attachment(filename="", content=b"data")
        assert "filename" in str(exc_info.value)

    def test_attachment_requires_content(self):
        """Test Attachment requires content."""
        with pytest.raises(ValueError) as exc_info:
            Attachment(filename="file.txt", content=b"")
        assert "content" in str(exc_info.value)

    def test_email_address_simple(self):
        """Test EmailAddress with just email."""
        addr = EmailAddress("user@example.com")
        assert str(addr) == "user@example.com"

    def test_email_address_with_name(self):
        """Test EmailAddress with name."""
        addr = EmailAddress("user@example.com", "John Doe")
        assert str(addr) == "John Doe <user@example.com>"

    def test_email_address_parse(self):
        """Test EmailAddress parsing."""
        addr = EmailAddress.parse("John Doe <user@example.com>")
        assert addr.email == "user@example.com"
        assert addr.name == "John Doe"

    def test_email_address_parse_simple(self):
        """Test EmailAddress parsing simple email."""
        addr = EmailAddress.parse("user@example.com")
        assert addr.email == "user@example.com"
        assert addr.name is None

    def test_email_message_creation(self):
        """Test EmailMessage creation."""
        msg = EmailMessage(
            to=["user@example.com"],
            subject="Hello!",
            html="<h1>Hello</h1>",
        )
        assert msg.to == ["user@example.com"]
        assert msg.subject == "Hello!"
        assert msg.html == "<h1>Hello</h1>"

    def test_email_message_string_to(self):
        """Test EmailMessage normalizes string to to list."""
        msg = EmailMessage(
            to="user@example.com",
            subject="Test",
            text="Content",
        )
        assert msg.to == ["user@example.com"]

    def test_email_message_requires_recipient(self):
        """Test EmailMessage requires at least one recipient."""
        with pytest.raises(ValueError) as exc_info:
            EmailMessage(to=[], subject="Test", html="Content")
        assert "recipient" in str(exc_info.value)

    def test_email_message_requires_subject(self):
        """Test EmailMessage requires subject."""
        with pytest.raises(ValueError) as exc_info:
            EmailMessage(to=["user@example.com"], subject="", html="Content")
        assert "Subject" in str(exc_info.value)

    def test_email_message_requires_content(self):
        """Test EmailMessage requires html or text."""
        with pytest.raises(ValueError) as exc_info:
            EmailMessage(to=["user@example.com"], subject="Test")
        assert "content" in str(exc_info.value).lower()

    def test_email_message_all_recipients(self):
        """Test EmailMessage all_recipients property."""
        msg = EmailMessage(
            to=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            subject="Test",
            html="Content",
        )
        all_recipients = msg.all_recipients
        assert "to@example.com" in all_recipients
        assert "cc@example.com" in all_recipients
        assert "bcc@example.com" in all_recipients


class TestEmailResult:
    """Tests for EmailResult."""

    def test_success_result(self):
        """Test creating success result."""
        result = EmailResult.success_result(
            message_id="msg_123",
            provider="resend",
        )
        assert result.success is True
        assert result.message_id == "msg_123"
        assert result.provider == "resend"
        assert result.status == EmailStatus.SENT
        assert result.sent_at is not None

    def test_failure_result(self):
        """Test creating failure result."""
        result = EmailResult.failure_result(
            error="Connection timeout",
            provider="smtp",
        )
        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.provider == "smtp"
        assert result.status == EmailStatus.FAILED


class TestBatchEmailResult:
    """Tests for BatchEmailResult."""

    def test_batch_result(self):
        """Test batch result creation."""
        results = [
            EmailResult(success=True, message_id="1"),
            EmailResult(success=True, message_id="2"),
            EmailResult(success=False, error="Failed"),
        ]
        batch = BatchEmailResult(
            total=3,
            success_count=2,
            failure_count=1,
            results=results,
        )
        assert batch.total == 3
        assert batch.success_count == 2
        assert batch.failure_count == 1

    def test_all_successful(self):
        """Test all_successful property."""
        batch_success = BatchEmailResult(total=2, success_count=2, failure_count=0)
        assert batch_success.all_successful is True

        batch_partial = BatchEmailResult(total=2, success_count=1, failure_count=1)
        assert batch_partial.all_successful is False

    def test_success_rate(self):
        """Test success_rate property."""
        batch = BatchEmailResult(total=4, success_count=3, failure_count=1)
        assert batch.success_rate == 75.0

    def test_success_rate_empty(self):
        """Test success_rate with no emails."""
        batch = BatchEmailResult(total=0, success_count=0, failure_count=0)
        assert batch.success_rate == 0.0


# =============================================================================
# Email Service Tests
# =============================================================================


class TestEmailService:
    """Tests for EmailService."""

    def test_create_resend_service(self):
        """Test creating Resend service."""
        service = EmailService(
            provider="resend",
            api_key="re_test_key",
            from_email="noreply@example.com",
        )
        assert service.from_email == "noreply@example.com"

    def test_create_smtp_service(self):
        """Test creating SMTP service."""
        service = EmailService(
            provider="smtp",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="user@gmail.com",
            smtp_password="password",
            from_email="user@gmail.com",
        )
        assert service.from_email == "user@gmail.com"

    def test_resend_requires_api_key(self):
        """Test Resend provider requires api_key."""
        with pytest.raises(ValueError) as exc_info:
            EmailService(provider="resend")
        assert "api_key" in str(exc_info.value)

    def test_smtp_requires_host(self):
        """Test SMTP provider requires host."""
        with pytest.raises(ValueError) as exc_info:
            EmailService(provider="smtp")
        assert "smtp_host" in str(exc_info.value)

    def test_unknown_provider(self):
        """Test unknown provider raises error."""
        with pytest.raises(ValueError) as exc_info:
            EmailService(provider="unknown")
        assert "Unknown provider" in str(exc_info.value)


# =============================================================================
# Email Status Tests
# =============================================================================


class TestEmailStatus:
    """Tests for EmailStatus enum."""

    def test_status_values(self):
        """Test EmailStatus values."""
        assert EmailStatus.PENDING.value == "pending"
        assert EmailStatus.SENT.value == "sent"
        assert EmailStatus.DELIVERED.value == "delivered"
        assert EmailStatus.FAILED.value == "failed"
        assert EmailStatus.BOUNCED.value == "bounced"
        assert EmailStatus.COMPLAINED.value == "complained"
