"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for Sentry observability module
Version: 1.0.0
"""

from unittest.mock import MagicMock, patch

import pytest

from ntlabs.observability.sentry import (
    setup_sentry,
    capture_exception,
    capture_message,
    set_user_context,
    add_breadcrumb,
)


class TestSetupSentry:
    """Test Sentry setup function."""

    def test_setup_sentry_no_dsn(self):
        """Test setup without DSN."""
        result = setup_sentry(dsn="")
        assert result is False

    def test_setup_sentry_import_error(self):
        """Test handling of missing sentry-sdk."""
        with patch.dict("sys.modules", {"sentry_sdk": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'sentry_sdk'")):
                result = setup_sentry(dsn="https://test@sentry.io/123")
                assert result is False

    def test_setup_sentry_basic(self):
        """Test basic Sentry setup."""
        with patch("sentry_sdk.init") as mock_init:
            result = setup_sentry(
                dsn="https://test@sentry.io/123",
                environment="production",
            )

            assert result is True
            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["dsn"] == "https://test@sentry.io/123"
            assert call_kwargs["environment"] == "production"

    def test_setup_sentry_with_release(self):
        """Test Sentry setup with release."""
        with patch("sentry_sdk.init") as mock_init:
            setup_sentry(
                dsn="https://test@sentry.io/123",
                release="1.0.0",
            )

            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["release"] == "1.0.0"

    def test_setup_sentry_with_sample_rates(self):
        """Test Sentry setup with sample rates."""
        with patch("sentry_sdk.init") as mock_init:
            setup_sentry(
                dsn="https://test@sentry.io/123",
                traces_sample_rate=0.5,
                profiles_sample_rate=0.25,
            )

            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["traces_sample_rate"] == 0.5
            assert call_kwargs["profiles_sample_rate"] == 0.25

    def test_setup_sentry_with_pii(self):
        """Test Sentry setup with PII enabled."""
        with patch("sentry_sdk.init") as mock_init:
            setup_sentry(
                dsn="https://test@sentry.io/123",
                send_default_pii=True,
            )

            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["send_default_pii"] is True

    def test_setup_sentry_with_debug(self):
        """Test Sentry setup with debug mode."""
        with patch("sentry_sdk.init") as mock_init:
            setup_sentry(
                dsn="https://test@sentry.io/123",
                debug=True,
            )

            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["debug"] is True

    def test_setup_sentry_with_additional_options(self):
        """Test Sentry setup with additional kwargs."""
        with patch("sentry_sdk.init") as mock_init:
            setup_sentry(
                dsn="https://test@sentry.io/123",
                max_breadcrumbs=100,
                attach_stacktrace=True,
            )

            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["max_breadcrumbs"] == 100
            assert call_kwargs["attach_stacktrace"] is True

    def test_setup_sentry_with_integrations(self):
        """Test Sentry setup with custom integrations."""
        mock_integration = MagicMock()

        with patch("sentry_sdk.init") as mock_init:
            with patch("sentry_sdk.integrations.logging.LoggingIntegration") as mock_logging:
                setup_sentry(
                    dsn="https://test@sentry.io/123",
                    integrations=[mock_integration],
                )

                call_kwargs = mock_init.call_args[1]
                assert mock_integration in call_kwargs["integrations"]

    def test_setup_sentry_ignore_errors(self):
        """Test Sentry setup with ignored errors."""
        with patch("sentry_sdk.init") as mock_init:
            setup_sentry(
                dsn="https://test@sentry.io/123",
                ignore_errors=[ValueError, TypeError],
            )

            call_kwargs = mock_init.call_args[1]
            assert "before_send" in call_kwargs

    def test_setup_sentry_before_send_callback(self):
        """Test Sentry setup with before_send callback."""
        def custom_before_send(event, hint):
            return event

        with patch("sentry_sdk.init") as mock_init:
            setup_sentry(
                dsn="https://test@sentry.io/123",
                before_send=custom_before_send,
            )

            call_kwargs = mock_init.call_args[1]
            assert "before_send" in call_kwargs

    def test_setup_sentry_ignored_error_filtered(self):
        """Test that ignored errors are filtered."""
        def custom_before_send(event, hint):
            return event

        with patch("sentry_sdk.init") as mock_init:
            setup_sentry(
                dsn="https://test@sentry.io/123",
                ignore_errors=[ValueError],
            )

            # Get the before_send function
            call_kwargs = mock_init.call_args[1]
            before_send = call_kwargs["before_send"]

            # Test with ignored error
            event = {"message": "test"}
            hint = {"exc_info": (ValueError, ValueError("test"), None)}
            result = before_send(event, hint)
            assert result is None

            # Test with non-ignored error
            hint = {"exc_info": (TypeError, TypeError("test"), None)}
            result = before_send(event, hint)
            assert result == event

    def test_setup_sentry_fastapi_integration(self):
        """Test that FastAPI integration is added when available."""
        with patch("sentry_sdk.init") as mock_init:
            with patch("sentry_sdk.integrations.fastapi.FastApiIntegration") as mock_fastapi:
                with patch("sentry_sdk.integrations.starlette.StarletteIntegration") as mock_starlette:
                    mock_fastapi.return_value = MagicMock()
                    mock_starlette.return_value = MagicMock()

                    setup_sentry(dsn="https://test@sentry.io/123")

                    call_kwargs = mock_init.call_args[1]
                    integrations = call_kwargs["integrations"]
                    assert len(integrations) >= 3  # Logging + FastAPI + Starlette

    def test_setup_sentry_httpx_integration(self):
        """Test that HTTPX integration is added when available."""
        with patch("sentry_sdk.init") as mock_init:
            with patch("sentry_sdk.integrations.httpx.HttpxIntegration") as mock_httpx:
                mock_httpx.return_value = MagicMock()

                setup_sentry(dsn="https://test@sentry.io/123")

                call_kwargs = mock_init.call_args[1]
                integrations = call_kwargs["integrations"]
                assert len(integrations) >= 2  # Logging + HTTPX

    def test_setup_sentry_redis_integration(self):
        """Test that Redis integration is added when available."""
        with patch("sentry_sdk.init") as mock_init:
            with patch("sentry_sdk.integrations.redis.RedisIntegration") as mock_redis:
                mock_redis.return_value = MagicMock()

                setup_sentry(dsn="https://test@sentry.io/123")

                call_kwargs = mock_init.call_args[1]
                integrations = call_kwargs["integrations"]
                assert len(integrations) >= 2  # Logging + Redis


class TestCaptureException:
    """Test capture_exception function."""

    def test_capture_exception_import_error(self):
        """Test handling of missing sentry-sdk."""
        with patch.dict("sys.modules", {"sentry_sdk": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'sentry_sdk'")):
                result = capture_exception(ValueError("test"))
                assert result is None

    def test_capture_exception_basic(self):
        """Test basic exception capture."""
        with patch("sentry_sdk.capture_exception") as mock_capture:
            mock_capture.return_value = "event_id_123"

            error = ValueError("test error")
            result = capture_exception(error)

            assert result == "event_id_123"
            mock_capture.assert_called_once_with(error)

    def test_capture_exception_with_context(self):
        """Test exception capture with context."""
        with patch("sentry_sdk.capture_exception") as mock_capture:
            with patch("sentry_sdk.set_extra") as mock_set_extra:
                with patch("sentry_sdk.set_tag") as mock_set_tag:
                    with patch("sentry_sdk.set_user") as mock_set_user:
                        with patch("sentry_sdk.set_level") as mock_set_level:
                            mock_capture.return_value = "event_id_123"

                            error = ValueError("test")
                            result = capture_exception(
                                error,
                                extra={"key": "value"},
                                tags={"component": "test"},
                                user={"id": "123"},
                                level="warning",
                            )

                            assert result == "event_id_123"
                            mock_set_user.assert_called_once_with({"id": "123"})
                            mock_set_level.assert_called_once_with("warning")

    def test_capture_exception_with_multiple_tags(self):
        """Test exception capture with multiple tags."""
        with patch("sentry_sdk.capture_exception") as mock_capture:
            with patch("sentry_sdk.set_tag") as mock_set_tag:
                mock_capture.return_value = "event_id"

                capture_exception(
                    ValueError("test"),
                    tags={"tag1": "value1", "tag2": "value2"},
                )

                assert mock_set_tag.call_count == 2

    def test_capture_exception_with_multiple_extras(self):
        """Test exception capture with multiple extras."""
        with patch("sentry_sdk.capture_exception") as mock_capture:
            with patch("sentry_sdk.set_extra") as mock_set_extra:
                mock_capture.return_value = "event_id"

                capture_exception(
                    ValueError("test"),
                    extra={"key1": "value1", "key2": "value2"},
                )

                assert mock_set_extra.call_count == 2


class TestCaptureMessage:
    """Test capture_message function."""

    def test_capture_message_import_error(self):
        """Test handling of missing sentry-sdk."""
        with patch.dict("sys.modules", {"sentry_sdk": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'sentry_sdk'")):
                result = capture_message("test message")
                assert result is None

    def test_capture_message_basic(self):
        """Test basic message capture."""
        with patch("sentry_sdk.capture_message") as mock_capture:
            mock_capture.return_value = "event_id_123"

            result = capture_message("test message")

            assert result == "event_id_123"
            mock_capture.assert_called_once_with("test message", level="info")

    def test_capture_message_with_level(self):
        """Test message capture with level."""
        with patch("sentry_sdk.capture_message") as mock_capture:
            mock_capture.return_value = "event_id"

            capture_message("error message", level="error")

            mock_capture.assert_called_once_with("error message", level="error")

    def test_capture_message_with_tags(self):
        """Test message capture with tags."""
        with patch("sentry_sdk.capture_message") as mock_capture:
            with patch("sentry_sdk.set_tag") as mock_set_tag:
                mock_capture.return_value = "event_id"

                capture_message(
                    "test",
                    tags={"component": "test"},
                )

                mock_set_tag.assert_called_once_with("component", "test")

    def test_capture_message_with_extras(self):
        """Test message capture with extras."""
        with patch("sentry_sdk.capture_message") as mock_capture:
            with patch("sentry_sdk.set_extra") as mock_set_extra:
                mock_capture.return_value = "event_id"

                capture_message(
                    "test",
                    extra={"context": "value"},
                )

                mock_set_extra.assert_called_once_with("context", "value")


class TestSetUserContext:
    """Test set_user_context function."""

    def test_set_user_context_import_error(self):
        """Test handling of missing sentry-sdk."""
        with patch.dict("sys.modules", {"sentry_sdk": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'sentry_sdk'")):
                # Should not raise
                set_user_context(user_id="123")

    def test_set_user_context_basic(self):
        """Test basic user context setting."""
        with patch("sentry_sdk.set_user") as mock_set_user:
            set_user_context(
                user_id="123",
                email="user@example.com",
                username="testuser",
                ip_address="1.2.3.4",
            )

            expected = {
                "id": "123",
                "email": "user@example.com",
                "username": "testuser",
                "ip_address": "1.2.3.4",
            }
            mock_set_user.assert_called_once_with(expected)

    def test_set_user_context_partial(self):
        """Test user context with partial data."""
        with patch("sentry_sdk.set_user") as mock_set_user:
            set_user_context(user_id="123")

            mock_set_user.assert_called_once_with({"id": "123"})

    def test_set_user_context_empty(self):
        """Test user context with no data."""
        with patch("sentry_sdk.set_user") as mock_set_user:
            set_user_context()

            mock_set_user.assert_not_called()

    def test_set_user_context_with_extra(self):
        """Test user context with extra data."""
        with patch("sentry_sdk.set_user") as mock_set_user:
            set_user_context(
                user_id="123",
                role="admin",
                plan="premium",
            )

            expected = {
                "id": "123",
                "role": "admin",
                "plan": "premium",
            }
            mock_set_user.assert_called_once_with(expected)


class TestAddBreadcrumb:
    """Test add_breadcrumb function."""

    def test_add_breadcrumb_import_error(self):
        """Test handling of missing sentry-sdk."""
        with patch.dict("sys.modules", {"sentry_sdk": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'sentry_sdk'")):
                # Should not raise
                add_breadcrumb("test message")

    def test_add_breadcrumb_basic(self):
        """Test basic breadcrumb addition."""
        with patch("sentry_sdk.add_breadcrumb") as mock_add:
            add_breadcrumb("test message")

            mock_add.assert_called_once_with(
                message="test message",
                category="custom",
                level="info",
                data=None,
            )

    def test_add_breadcrumb_with_category(self):
        """Test breadcrumb with custom category."""
        with patch("sentry_sdk.add_breadcrumb") as mock_add:
            add_breadcrumb("query executed", category="db")

            call_args = mock_add.call_args[1]
            assert call_args["category"] == "db"

    def test_add_breadcrumb_with_level(self):
        """Test breadcrumb with custom level."""
        with patch("sentry_sdk.add_breadcrumb") as mock_add:
            add_breadcrumb("error occurred", level="error")

            call_args = mock_add.call_args[1]
            assert call_args["level"] == "error"

    def test_add_breadcrumb_with_data(self):
        """Test breadcrumb with data."""
        with patch("sentry_sdk.add_breadcrumb") as mock_add:
            data = {"query": "SELECT * FROM users", "duration_ms": 50}
            add_breadcrumb("query executed", category="db", data=data)

            call_args = mock_add.call_args[1]
            assert call_args["data"] == data
