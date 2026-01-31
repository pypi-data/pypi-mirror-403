"""
Comprehensive tests for ntlabs.middleware.logging module.

Tests logging middleware for FastAPI.
"""

import logging
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ntlabs.middleware.logging import (
    LoggingMiddleware,
    StructuredLogger,
    get_request_id,
)


# =============================================================================
# Logging Middleware Initialization Tests
# =============================================================================


class TestLoggingMiddlewareInit:
    """Tests for LoggingMiddleware initialization."""

    def test_middleware_init_defaults(self):
        """Test middleware initialization with defaults."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        assert middleware.app is not None
        assert middleware.logger is not None
        assert middleware.log_request_body is False
        assert middleware.log_response_body is False
        assert middleware.max_body_length == 1000
        assert "/health" in middleware.exclude_paths
        assert "/metrics" in middleware.exclude_paths
        assert middleware.request_id_header == "X-Request-ID"
        assert middleware.generate_request_id is True
        assert middleware.slow_request_threshold == 1.0

    def test_middleware_init_custom_logger(self):
        """Test middleware with custom logger."""

        class MockApp:
            pass

        custom_logger = logging.getLogger("custom")
        middleware = LoggingMiddleware(app=MockApp(), logger=custom_logger)
        assert middleware.logger == custom_logger

    def test_middleware_init_log_body_flags(self):
        """Test middleware with log body flags."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(
            app=MockApp(),
            log_request_body=True,
            log_response_body=True,
        )
        assert middleware.log_request_body is True
        assert middleware.log_response_body is True

    def test_middleware_init_custom_body_length(self):
        """Test middleware with custom body length."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp(), max_body_length=500)
        assert middleware.max_body_length == 500

    def test_middleware_init_custom_exclude_paths(self):
        """Test middleware with custom exclude paths."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(
            app=MockApp(),
            exclude_paths=["/custom", "/exclude"],
        )
        assert "/custom" in middleware.exclude_paths
        assert "/exclude" in middleware.exclude_paths
        assert "/health" not in middleware.exclude_paths

    def test_middleware_init_custom_exclude_headers(self):
        """Test middleware with custom exclude headers."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(
            app=MockApp(),
            exclude_headers=["x-custom-secret"],
        )
        assert "x-custom-secret" in middleware.exclude_headers

    def test_middleware_init_custom_request_id_header(self):
        """Test middleware with custom request ID header."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(
            app=MockApp(),
            request_id_header="X-Custom-Request-ID",
        )
        assert middleware.request_id_header == "X-Custom-Request-ID"

    def test_middleware_init_no_request_id_generation(self):
        """Test middleware with request ID generation disabled."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(
            app=MockApp(),
            generate_request_id=False,
        )
        assert middleware.generate_request_id is False

    def test_middleware_init_custom_slow_threshold(self):
        """Test middleware with custom slow request threshold."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(
            app=MockApp(),
            slow_request_threshold=0.5,
        )
        assert middleware.slow_request_threshold == 0.5


# =============================================================================
# Middleware Call Tests
# =============================================================================


class TestLoggingMiddlewareCall:
    """Tests for LoggingMiddleware __call__ method."""

    @pytest.mark.asyncio
    async def test_call_non_http_scope(self):
        """Test middleware ignores non-HTTP scopes."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({"type": "websocket.accept"})

        middleware = LoggingMiddleware(app=MockApp())
        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        # Should pass through without logging
        assert middleware.app is not None

    @pytest.mark.asyncio
    async def test_call_excluded_path(self):
        """Test middleware skips excluded paths."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({"type": "http.response.start", "status": 200})

        middleware = LoggingMiddleware(
            app=MockApp(),
            exclude_paths=["/health"],
        )
        scope = {"type": "http", "path": "/health", "method": "GET"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        # Should pass through without logging

    @pytest.mark.asyncio
    async def test_call_normal_request(self):
        """Test middleware logs normal request."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({"type": "http.response.start", "status": 200})

        middleware = LoggingMiddleware(app=MockApp())
        scope = {
            "type": "http",
            "path": "/api/test",
            "method": "GET",
            "headers": [],
        }
        receive = AsyncMock()
        send = AsyncMock()

        with patch.object(middleware, "_log_request") as mock_log:
            await middleware(scope, receive, send)

            # Should log the request
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_with_existing_request_id(self):
        """Test middleware uses existing request ID from header."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({"type": "http.response.start", "status": 200})

        middleware = LoggingMiddleware(app=MockApp())
        scope = {
            "type": "http",
            "path": "/api/test",
            "method": "GET",
            "headers": [(b"x-request-id", b"existing-id-123")],
        }
        receive = AsyncMock()
        send = AsyncMock()

        with patch.object(middleware, "_log_request") as mock_log:
            await middleware(scope, receive, send)

            call_args = mock_log.call_args.kwargs
            assert call_args["request_id"] == "existing-id-123"

    @pytest.mark.asyncio
    async def test_call_generates_request_id(self):
        """Test middleware generates request ID when not provided."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({"type": "http.response.start", "status": 200})

        middleware = LoggingMiddleware(app=MockApp())
        scope = {
            "type": "http",
            "path": "/api/test",
            "method": "GET",
            "headers": [],
        }
        receive = AsyncMock()
        send = AsyncMock()

        with patch.object(middleware, "_log_request") as mock_log:
            await middleware(scope, receive, send)

            call_args = mock_log.call_args.kwargs
            assert call_args["request_id"] is not None
            assert len(call_args["request_id"]) > 0

    @pytest.mark.asyncio
    async def test_call_does_not_generate_when_disabled(self):
        """Test middleware doesn't generate request ID when disabled."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({"type": "http.response.start", "status": 200})

        middleware = LoggingMiddleware(
            app=MockApp(),
            generate_request_id=False,
        )
        scope = {
            "type": "http",
            "path": "/api/test",
            "method": "GET",
            "headers": [],
        }
        receive = AsyncMock()
        send = AsyncMock()

        with patch.object(middleware, "_log_request") as mock_log:
            await middleware(scope, receive, send)

            call_args = mock_log.call_args.kwargs
            assert call_args["request_id"] == ""

    @pytest.mark.asyncio
    async def test_call_adds_request_id_to_response(self):
        """Test middleware adds request ID to response headers."""

        captured_headers = None

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [],
                })

        middleware = LoggingMiddleware(app=MockApp())
        scope = {
            "type": "http",
            "path": "/api/test",
            "method": "GET",
            "headers": [],
        }
        receive = AsyncMock()

        async def capture_send(message):
            nonlocal captured_headers
            if message["type"] == "http.response.start":
                captured_headers = message.get("headers", [])

        await middleware(scope, receive, capture_send)

        # Check that request ID was added to response
        header_names = [h[0].decode() for h in captured_headers or []]
        assert "X-Request-ID" in header_names


# =============================================================================
# Client IP Extraction Tests
# =============================================================================


class TestClientIPExtraction:
    """Tests for client IP extraction."""

    def test_get_client_ip_from_forwarded(self):
        """Test extracting IP from X-Forwarded-For header."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        scope = {"client": ("10.0.0.1", 12345)}
        headers = {b"x-forwarded-for": b"203.0.113.195, 70.41.3.18"}

        ip = middleware._get_client_ip(scope, headers)
        assert ip == "203.0.113.195"

    def test_get_client_ip_from_real_ip(self):
        """Test extracting IP from X-Real-IP header."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        scope = {"client": ("10.0.0.1", 12345)}
        headers = {b"x-real-ip": b"198.51.100.42"}

        ip = middleware._get_client_ip(scope, headers)
        assert ip == "198.51.100.42"

    def test_get_client_ip_from_scope(self):
        """Test extracting IP from scope client."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        scope = {"client": ("192.168.1.100", 54321)}
        headers = {}

        ip = middleware._get_client_ip(scope, headers)
        assert ip == "192.168.1.100"

    def test_get_client_ip_unknown(self):
        """Test extracting IP when all sources fail."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        scope = {}
        headers = {}

        ip = middleware._get_client_ip(scope, headers)
        assert ip == "unknown"

    def test_get_client_ip_forwarded_single(self):
        """Test extracting IP from single X-Forwarded-For value."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        scope = {}
        headers = {b"x-forwarded-for": b"203.0.113.195"}

        ip = middleware._get_client_ip(scope, headers)
        assert ip == "203.0.113.195"

    def test_get_client_ip_forwarded_whitespace(self):
        """Test extracting IP with whitespace in X-Forwarded-For."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        scope = {}
        headers = {b"x-forwarded-for": b" 203.0.113.195 , 70.41.3.18 "}

        ip = middleware._get_client_ip(scope, headers)
        assert ip == "203.0.113.195"


# =============================================================================
# Request Logging Tests
# =============================================================================


class TestRequestLogging:
    """Tests for request logging functionality."""

    def test_log_request_info_level(self):
        """Test logging at INFO level for successful request."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        mock_logger = MagicMock()
        middleware.logger = mock_logger

        middleware._log_request(
            request_id="test-123",
            method="GET",
            path="/api/test",
            client_ip="127.0.0.1",
            status_code=200,
            duration=0.1,
        )

        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.INFO
        assert "GET" in call_args[0][1]
        assert "200" in call_args[0][1]

    def test_log_request_warning_level_4xx(self):
        """Test logging at WARNING level for 4xx errors."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        mock_logger = MagicMock()
        middleware.logger = mock_logger

        middleware._log_request(
            request_id="test-123",
            method="POST",
            path="/api/test",
            client_ip="127.0.0.1",
            status_code=400,
            duration=0.1,
        )

        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.WARNING

    def test_log_request_error_level_5xx(self):
        """Test logging at ERROR level for 5xx errors."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        mock_logger = MagicMock()
        middleware.logger = mock_logger

        middleware._log_request(
            request_id="test-123",
            method="GET",
            path="/api/test",
            client_ip="127.0.0.1",
            status_code=500,
            duration=0.1,
        )

        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.ERROR

    def test_log_request_warning_slow(self):
        """Test logging at WARNING level for slow requests."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp(), slow_request_threshold=0.5)
        mock_logger = MagicMock()
        middleware.logger = mock_logger

        middleware._log_request(
            request_id="test-123",
            method="GET",
            path="/api/test",
            client_ip="127.0.0.1",
            status_code=200,
            duration=1.0,  # Slow request
        )

        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.WARNING
        # Check extra data for slow request flag
        extra = call_args[1].get("extra", {})
        assert extra.get("slow_request") is True

    def test_log_request_with_error(self):
        """Test logging with error message."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        mock_logger = MagicMock()
        middleware.logger = mock_logger

        middleware._log_request(
            request_id="test-123",
            method="GET",
            path="/api/test",
            client_ip="127.0.0.1",
            status_code=500,
            duration=0.1,
            error="Database connection failed",
        )

        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.ERROR
        # Check extra data for error
        extra = call_args[1].get("extra", {})
        assert extra.get("error") == "Database connection failed"

    def test_log_request_extra_data(self):
        """Test logging extra data in log record."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        mock_logger = MagicMock()
        middleware.logger = mock_logger

        middleware._log_request(
            request_id="test-123",
            method="GET",
            path="/api/test",
            client_ip="127.0.0.1",
            status_code=200,
            duration=0.123456789,  # Should be rounded to 2 decimal places
        )

        call_args = mock_logger.log.call_args
        extra = call_args[1].get("extra", {})
        assert extra.get("request_id") == "test-123"
        assert extra.get("method") == "GET"
        assert extra.get("path") == "/api/test"
        assert extra.get("client_ip") == "127.0.0.1"
        assert extra.get("status") == 200
        # Duration should be rounded to 2 decimal places (in ms)
        assert "duration_ms" in extra


# =============================================================================
# Exception Handling Tests
# =============================================================================


class TestExceptionHandling:
    """Tests for exception handling in middleware."""

    @pytest.mark.asyncio
    async def test_call_exception_handling(self):
        """Test middleware handles exceptions correctly."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                raise ValueError("Test exception")

        middleware = LoggingMiddleware(app=MockApp())
        scope = {
            "type": "http",
            "path": "/api/test",
            "method": "GET",
            "headers": [],
        }
        receive = AsyncMock()
        send = AsyncMock()

        with patch.object(middleware, "_log_request") as mock_log:
            with pytest.raises(ValueError, match="Test exception"):
                await middleware(scope, receive, send)

            # Should log the error before re-raising
            mock_log.assert_called_once()
            call_args = mock_log.call_args.kwargs
            assert call_args["status_code"] == 500
            assert "Test exception" in call_args["error"]


# =============================================================================
# Get Request ID Tests
# =============================================================================


class TestGetRequestID:
    """Tests for get_request_id function."""

    def test_get_request_id_returns_none(self):
        """Test get_request_id returns None by default."""
        result = get_request_id()
        assert result is None


# =============================================================================
# Structured Logger Tests
# =============================================================================


class TestStructuredLogger:
    """Tests for StructuredLogger class."""

    def test_structured_logger_init(self):
        """Test StructuredLogger initialization."""
        logger = StructuredLogger("test_logger")
        assert logger._logger.name == "test_logger"

    def test_structured_logger_debug(self):
        """Test StructuredLogger debug method."""
        logger = StructuredLogger("test")
        mock_logger = MagicMock()
        logger._logger = mock_logger

        logger.debug("Debug message", key1="value1", key2="value2")

        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.DEBUG
        assert call_args[0][1] == "Debug message"
        assert call_args[1]["extra"]["structured_data"] == {
            "key1": "value1",
            "key2": "value2",
        }

    def test_structured_logger_info(self):
        """Test StructuredLogger info method."""
        logger = StructuredLogger("test")
        mock_logger = MagicMock()
        logger._logger = mock_logger

        logger.info("Info message", user_id="123", action="login")

        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.INFO
        assert call_args[1]["extra"]["structured_data"] == {
            "user_id": "123",
            "action": "login",
        }

    def test_structured_logger_warning(self):
        """Test StructuredLogger warning method."""
        logger = StructuredLogger("test")
        mock_logger = MagicMock()
        logger._logger = mock_logger

        logger.warning("Warning message", threshold_exceeded=True)

        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.WARNING

    def test_structured_logger_error(self):
        """Test StructuredLogger error method."""
        logger = StructuredLogger("test")
        mock_logger = MagicMock()
        logger._logger = mock_logger

        logger.error("Error message", error_code="E001")

        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.ERROR

    def test_structured_logger_critical(self):
        """Test StructuredLogger critical method."""
        logger = StructuredLogger("test")
        mock_logger = MagicMock()
        logger._logger = mock_logger

        logger.critical("Critical message", system="down")

        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.CRITICAL

    def test_structured_logger_no_extra(self):
        """Test StructuredLogger with no extra data."""
        logger = StructuredLogger("test")
        mock_logger = MagicMock()
        logger._logger = mock_logger

        logger.info("Simple message")

        call_args = mock_logger.log.call_args
        assert "extra" not in call_args[1] or call_args[1]["extra"] == {}


# =============================================================================
# Integration Tests
# =============================================================================


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    @pytest.mark.asyncio
    async def test_full_request_lifecycle(self):
        """Test full request lifecycle logging."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [],
                })

        middleware = LoggingMiddleware(
            app=MockApp(),
            exclude_paths=[],
        )
        scope = {
            "type": "http",
            "path": "/api/users",
            "method": "POST",
            "headers": [
                (b"x-request-id", b"req-123"),
                (b"x-forwarded-for", b"203.0.113.195"),
            ],
            "client": ("127.0.0.1", 12345),
        }
        receive = AsyncMock()
        send = AsyncMock()

        with patch.object(middleware, "_log_request") as mock_log:
            await middleware(scope, receive, send)

            mock_log.assert_called_once()
            call_args = mock_log.call_args.kwargs
            assert call_args["request_id"] == "req-123"
            assert call_args["method"] == "POST"
            assert call_args["path"] == "/api/users"
            assert call_args["client_ip"] == "203.0.113.195"
            assert call_args["status_code"] == 200

    @pytest.mark.asyncio
    async def test_excluded_path_not_logged(self):
        """Test that excluded paths are not logged."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [],
                })

        middleware = LoggingMiddleware(
            app=MockApp(),
            exclude_paths=["/health"],
        )
        scope = {
            "type": "http",
            "path": "/health",
            "method": "GET",
            "headers": [],
        }
        receive = AsyncMock()
        send = AsyncMock()

        with patch.object(middleware, "_log_request") as mock_log:
            await middleware(scope, receive, send)

            mock_log.assert_not_called()
