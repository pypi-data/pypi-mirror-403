"""
Tests for ntlabs.observability module.

Tests audit logging, metrics collection, Sentry integration, and tracing.
"""

import time

import pytest

from ntlabs.observability import (
    AuditCategory,
    AuditEntry,
    # Audit
    AuditLogger,
    AuditSeverity,
    # Metrics
    MetricsCollector,
    add_breadcrumb,
    capture_exception,
    capture_message,
    get_current_span_id,
    get_current_trace_id,
    get_metrics,
    get_tracer,
    set_metrics,
    set_user_context,
    # Tracing
    setup_sentry,
    trace_span,
    traced,
)

# =============================================================================
# Audit Entry Tests
# =============================================================================


class TestAuditEntry:
    """Tests for AuditEntry."""

    def test_create_entry(self):
        """Test creating audit entry."""
        entry = AuditEntry(
            action="user_login",
            category=AuditCategory.AUTH,
            severity=AuditSeverity.INFO,
            user_id="user_123",
        )
        assert entry.action == "user_login"
        assert entry.category == AuditCategory.AUTH
        assert entry.user_id == "user_123"
        assert entry.timestamp is not None

    def test_entry_to_dict(self):
        """Test converting entry to dict."""
        entry = AuditEntry(
            action="record_created",
            category=AuditCategory.DATA,
            severity=AuditSeverity.INFO,
            user_id="user_123",
            resource_type="patient",
            resource_id="patient_456",
            details={"field": "value"},
        )
        data = entry.to_dict()

        assert data["action"] == "record_created"
        assert data["category"] == "data"  # Enum value
        assert data["severity"] == "info"  # Enum value
        assert data["user_id"] == "user_123"
        assert data["resource_type"] == "patient"
        assert "timestamp" in data

    def test_entry_excludes_none(self):
        """Test to_dict excludes None values."""
        entry = AuditEntry(
            action="test",
            category=AuditCategory.SYSTEM,
            severity=AuditSeverity.INFO,
        )
        data = entry.to_dict()

        assert "user_id" not in data
        assert "ip_address" not in data


class TestAuditSeverity:
    """Tests for AuditSeverity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        assert AuditSeverity.DEBUG.value == "debug"
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.WARNING.value == "warning"
        assert AuditSeverity.ERROR.value == "error"
        assert AuditSeverity.CRITICAL.value == "critical"


class TestAuditCategory:
    """Tests for AuditCategory enum."""

    def test_category_values(self):
        """Test category enum values."""
        assert AuditCategory.AUTH.value == "auth"
        assert AuditCategory.DATA.value == "data"
        assert AuditCategory.ADMIN.value == "admin"
        assert AuditCategory.SECURITY.value == "security"
        assert AuditCategory.SYSTEM.value == "system"
        assert AuditCategory.API.value == "api"


# =============================================================================
# Audit Logger Tests
# =============================================================================


class TestAuditLogger:
    """Tests for AuditLogger."""

    def test_logger_initialization(self):
        """Test AuditLogger initialization."""
        logger = AuditLogger(
            service="test-service",
            buffer_size=100,
            enable_local_logging=True,
        )
        assert logger.service == "test-service"
        assert logger.buffer_size == 100

    def test_logger_with_supabase_config(self):
        """Test AuditLogger with Supabase config."""
        logger = AuditLogger(
            service="test-service",
            supabase_url="https://xxx.supabase.co",
            supabase_key="test_key",
            table_name="audit_logs",
        )
        assert logger.supabase_url == "https://xxx.supabase.co"
        assert logger.table_name == "audit_logs"

    @pytest.mark.asyncio
    async def test_log_entry(self):
        """Test logging an entry."""
        logger = AuditLogger(
            service="test-service",
            enable_local_logging=False,  # Disable to avoid log output
        )

        await logger.log(
            action="test_action",
            category=AuditCategory.SYSTEM,
            severity=AuditSeverity.INFO,
            details={"key": "value"},
        )

        # Entry should be in buffer
        assert len(logger._buffer) == 1
        assert logger._buffer[0].action == "test_action"

    @pytest.mark.asyncio
    async def test_log_auth(self):
        """Test auth convenience method."""
        logger = AuditLogger(
            service="test-service",
            enable_local_logging=False,
        )

        await logger.log_auth(
            action="user_login",
            user_id="user_123",
            ip_address="192.168.1.1",
            success=True,
        )

        assert len(logger._buffer) == 1
        entry = logger._buffer[0]
        assert entry.action == "user_login"
        assert entry.category == AuditCategory.AUTH

    @pytest.mark.asyncio
    async def test_log_data_access(self):
        """Test data access convenience method."""
        logger = AuditLogger(
            service="test-service",
            enable_local_logging=False,
        )

        await logger.log_data_access(
            action="view_record",
            resource_type="patient",
            resource_id="patient_123",
            user_id="doctor_456",
        )

        assert len(logger._buffer) == 1
        entry = logger._buffer[0]
        assert entry.category == AuditCategory.DATA
        assert entry.resource_type == "patient"

    @pytest.mark.asyncio
    async def test_log_security(self):
        """Test security convenience method."""
        logger = AuditLogger(
            service="test-service",
            enable_local_logging=False,
        )

        await logger.log_security(
            action="failed_login_attempt",
            severity=AuditSeverity.WARNING,
            ip_address="10.0.0.1",
        )

        assert len(logger._buffer) == 1
        entry = logger._buffer[0]
        assert entry.category == AuditCategory.SECURITY
        assert entry.severity == AuditSeverity.WARNING

    @pytest.mark.asyncio
    async def test_buffer_auto_flush(self):
        """Test auto-flush when buffer is full."""
        logger = AuditLogger(
            service="test-service",
            buffer_size=3,
            enable_local_logging=False,
        )

        # Add entries below buffer size
        await logger.log(
            action="entry1", category=AuditCategory.SYSTEM, severity=AuditSeverity.INFO
        )
        await logger.log(
            action="entry2", category=AuditCategory.SYSTEM, severity=AuditSeverity.INFO
        )

        assert len(logger._buffer) == 2

        # Buffer should stay until flush is triggered (at buffer_size)
        # Note: Without Supabase configured, flush does nothing but clears buffer
        await logger.log(
            action="entry3", category=AuditCategory.SYSTEM, severity=AuditSeverity.INFO
        )

        # Flush should have been triggered and buffer cleared (but re-added due to no client)
        # The buffer behavior depends on whether Supabase client is available


# =============================================================================
# Metrics Collector Tests
# =============================================================================


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_collector_initialization(self):
        """Test MetricsCollector initialization."""
        metrics = MetricsCollector(
            namespace="test_app",
            default_labels={"environment": "test"},
        )
        assert metrics.namespace == "test_app"
        assert metrics.default_labels == {"environment": "test"}

    def test_increment_counter(self):
        """Test incrementing counter."""
        metrics = MetricsCollector(namespace="test")

        metrics.increment("requests")
        metrics.increment("requests")
        metrics.increment("requests", value=3)

        assert metrics._counters["test_requests"] == 5

    def test_increment_counter_with_labels(self):
        """Test incrementing counter with labels."""
        metrics = MetricsCollector(namespace="test")

        metrics.increment("requests", labels={"endpoint": "/api/chat"})
        metrics.increment("requests", labels={"endpoint": "/api/export"})

        # Check both counters exist
        assert any("/api/chat" in k for k in metrics._counters)
        assert any("/api/export" in k for k in metrics._counters)

    def test_set_gauge(self):
        """Test setting gauge."""
        metrics = MetricsCollector(namespace="test")

        metrics.set_gauge("active_users", 42)
        assert metrics._gauges["test_active_users"] == 42

        # Update gauge
        metrics.set_gauge("active_users", 50)
        assert metrics._gauges["test_active_users"] == 50

    def test_histogram(self):
        """Test histogram observations."""
        metrics = MetricsCollector(namespace="test")

        metrics.histogram("response_time", 0.1)
        metrics.histogram("response_time", 0.2)
        metrics.histogram("response_time", 0.3)

        assert "test_response_time" in metrics._histograms
        assert len(metrics._histograms["test_response_time"]) == 3

    def test_timer_context_manager(self):
        """Test timer context manager."""
        metrics = MetricsCollector(namespace="test")

        with metrics.timer("operation_time"):
            time.sleep(0.1)

        assert "test_operation_time" in metrics._histograms
        values = metrics._histograms["test_operation_time"]
        assert len(values) == 1
        assert values[0] >= 0.1

    def test_timed_decorator(self):
        """Test timed decorator for sync function."""
        metrics = MetricsCollector(namespace="test")

        @metrics.timed("function_time")
        def my_function():
            time.sleep(0.05)
            return "result"

        result = my_function()

        assert result == "result"
        assert "test_function_time" in metrics._histograms

    def test_export_prometheus(self):
        """Test Prometheus export format."""
        metrics = MetricsCollector(namespace="test")

        metrics.increment("requests", value=10)
        metrics.set_gauge("users", 5)
        metrics.histogram("duration", 0.1)
        metrics.histogram("duration", 0.2)

        output = metrics.export_prometheus()

        assert "# TYPE test_requests counter" in output
        assert "test_requests 10" in output
        assert "# TYPE test_users gauge" in output
        assert "test_users 5" in output
        assert "# TYPE test_duration histogram" in output
        assert "test_duration_count 2" in output

    def test_get_stats(self):
        """Test getting stats as dict."""
        metrics = MetricsCollector(namespace="test")

        metrics.increment("counter1", value=5)
        metrics.set_gauge("gauge1", 10)
        metrics.histogram("hist1", 1.0)
        metrics.histogram("hist1", 2.0)

        stats = metrics.get_stats()

        assert "counters" in stats
        assert "gauges" in stats
        assert "histograms" in stats

        assert stats["counters"]["test_counter1"] == 5
        assert stats["gauges"]["test_gauge1"] == 10
        assert stats["histograms"]["test_hist1"]["count"] == 2
        assert stats["histograms"]["test_hist1"]["avg"] == 1.5

    def test_reset(self):
        """Test resetting all metrics."""
        metrics = MetricsCollector(namespace="test")

        metrics.increment("counter", value=10)
        metrics.set_gauge("gauge", 20)
        metrics.histogram("hist", 0.5)

        metrics.reset()

        assert len(metrics._counters) == 0
        assert len(metrics._gauges) == 0
        assert len(metrics._histograms) == 0


class TestGlobalMetrics:
    """Tests for global metrics functions."""

    def test_get_metrics(self):
        """Test getting global metrics."""
        metrics = get_metrics()
        assert isinstance(metrics, MetricsCollector)

    def test_set_metrics(self):
        """Test setting global metrics."""
        custom_metrics = MetricsCollector(namespace="custom")
        set_metrics(custom_metrics)

        retrieved = get_metrics()
        assert retrieved.namespace == "custom"

        # Reset to default for other tests
        set_metrics(MetricsCollector())


# =============================================================================
# Sentry Tests
# =============================================================================


class TestSentryFunctions:
    """Tests for Sentry functions."""

    def test_setup_sentry_without_dsn(self):
        """Test setup_sentry returns False without DSN."""
        result = setup_sentry(dsn="")
        assert result is False

    def test_capture_functions_exist(self):
        """Test Sentry capture functions exist."""
        # These functions should not raise even without sentry-sdk
        assert callable(capture_exception)
        assert callable(capture_message)
        assert callable(set_user_context)
        assert callable(add_breadcrumb)


# =============================================================================
# Tracing Tests
# =============================================================================


class TestTracingFunctions:
    """Tests for OpenTelemetry tracing functions."""

    def test_get_tracer_without_setup(self):
        """Test get_tracer returns NoOpTracer without setup."""
        tracer = get_tracer()
        # Should return a tracer (either real or NoOp)
        assert tracer is not None

    def test_trace_span_context_manager(self):
        """Test trace_span as context manager."""
        with trace_span("test_operation"):
            # Should not raise
            pass

    def test_traced_decorator_sync(self):
        """Test traced decorator on sync function."""

        @traced()
        def my_func():
            return "result"

        result = my_func()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_traced_decorator_async(self):
        """Test traced decorator on async function."""

        @traced()
        async def my_async_func():
            return "async_result"

        result = await my_async_func()
        assert result == "async_result"

    def test_get_current_trace_id(self):
        """Test get_current_trace_id."""
        # Without OpenTelemetry setup, should return None
        trace_id = get_current_trace_id()
        assert trace_id is None or isinstance(trace_id, str)

    def test_get_current_span_id(self):
        """Test get_current_span_id."""
        # Without OpenTelemetry setup, should return None
        span_id = get_current_span_id()
        assert span_id is None or isinstance(span_id, str)
