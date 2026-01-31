"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for OpenTelemetry tracing module
Version: 1.0.0
"""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from ntlabs.observability.tracing import (
    setup_opentelemetry,
    get_tracer,
    NoOpTracer,
    NoOpSpan,
    trace_span,
    traced,
    get_current_trace_id,
    get_current_span_id,
    _tracer,
)


class TestSetupOpentelemetry:
    """Test OpenTelemetry setup function."""

    def test_setup_import_error(self):
        """Test handling of missing opentelemetry packages."""
        with patch.dict("sys.modules", {"opentelemetry": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'opentelemetry'")):
                result = setup_opentelemetry(service_name="test")
                assert result is False

    def test_setup_basic(self):
        """Test basic OpenTelemetry setup."""
        with patch("opentelemetry.trace.set_tracer_provider") as mock_set:
            with patch("opentelemetry.trace.get_tracer") as mock_get_tracer:
                with patch("opentelemetry.sdk.trace.TracerProvider") as mock_provider:
                    with patch("opentelemetry.sdk.resources.Resource.create") as mock_resource:
                        mock_tracer = MagicMock()
                        mock_get_tracer.return_value = mock_tracer

                        result = setup_opentelemetry(
                            service_name="test-service",
                            environment="production",
                        )

                        assert result is True
                        mock_set.assert_called_once()
                        # get_tracer is called multiple times including by auto-instrumentation
                        mock_get_tracer.assert_called()

    def test_setup_with_otlp_endpoint(self):
        """Test setup with OTLP exporter."""
        with patch("opentelemetry.trace.set_tracer_provider"):
            with patch("opentelemetry.trace.get_tracer"):
                with patch("opentelemetry.sdk.trace.TracerProvider"):
                    with patch("opentelemetry.sdk.resources.Resource.create"):
                        with patch("opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter") as mock_exporter:
                            with patch("opentelemetry.sdk.trace.export.BatchSpanProcessor") as mock_processor:
                                result = setup_opentelemetry(
                                    service_name="test",
                                    otlp_endpoint="http://collector:4317",
                                )

                                assert result is True
                                mock_exporter.assert_called_once_with(endpoint="http://collector:4317")

    def test_setup_with_console_export(self):
        """Test setup with console exporter."""
        with patch("opentelemetry.trace.set_tracer_provider"):
            with patch("opentelemetry.trace.get_tracer"):
                with patch("opentelemetry.sdk.trace.TracerProvider"):
                    with patch("opentelemetry.sdk.resources.Resource.create"):
                        with patch("opentelemetry.sdk.trace.export.ConsoleSpanExporter") as mock_exporter:
                            with patch("opentelemetry.sdk.trace.export.SimpleSpanProcessor") as mock_processor:
                                result = setup_opentelemetry(
                                    service_name="test",
                                    enable_console_export=True,
                                )

                                assert result is True

    def test_setup_with_sample_rate(self):
        """Test setup with custom sample rate."""
        with patch("opentelemetry.trace.set_tracer_provider"):
            with patch("opentelemetry.trace.get_tracer"):
                with patch("opentelemetry.sdk.trace.TracerProvider") as mock_provider:
                    with patch("opentelemetry.sdk.trace.sampling.TraceIdRatioBased") as mock_sampler:
                        with patch("opentelemetry.sdk.resources.Resource.create"):
                            result = setup_opentelemetry(
                                service_name="test",
                                sample_rate=0.5,
                            )

                            assert result is True
                            mock_sampler.assert_called_once_with(0.5)

    def test_setup_with_resource_attributes(self):
        """Test setup with additional resource attributes."""
        with patch("opentelemetry.trace.set_tracer_provider"):
            with patch("opentelemetry.trace.get_tracer"):
                with patch("opentelemetry.sdk.trace.TracerProvider"):
                    with patch("opentelemetry.sdk.resources.Resource.create") as mock_resource:
                        result = setup_opentelemetry(
                            service_name="test",
                            resource_attributes={"custom.attr": "value"},
                        )

                        call_args = mock_resource.call_args[0][0]
                        assert call_args["custom.attr"] == "value"


class TestAutoInstrument:
    """Test auto-instrumentation."""

    def test_auto_instrument_fastapi(self):
        """Test FastAPI auto-instrumentation."""
        with patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor") as mock_fastapi:
            with patch("opentelemetry.trace.set_tracer_provider"):
                with patch("opentelemetry.trace.get_tracer"):
                    with patch("opentelemetry.sdk.trace.TracerProvider"):
                        with patch("opentelemetry.sdk.resources.Resource.create"):
                            setup_opentelemetry(service_name="test")
                            mock_fastapi.return_value.instrument.assert_called_once()

    def test_auto_instrument_httpx(self):
        """Test HTTPX auto-instrumentation."""
        with patch("opentelemetry.instrumentation.httpx.HTTPXClientInstrumentor") as mock_httpx:
            with patch("opentelemetry.trace.set_tracer_provider"):
                with patch("opentelemetry.trace.get_tracer"):
                    with patch("opentelemetry.sdk.trace.TracerProvider"):
                        with patch("opentelemetry.sdk.resources.Resource.create"):
                            setup_opentelemetry(service_name="test")
                            mock_httpx.return_value.instrument.assert_called_once()

    def test_auto_instrument_redis(self):
        """Test Redis auto-instrumentation."""
        with patch("opentelemetry.instrumentation.redis.RedisInstrumentor") as mock_redis:
            with patch("opentelemetry.trace.set_tracer_provider"):
                with patch("opentelemetry.trace.get_tracer"):
                    with patch("opentelemetry.sdk.trace.TracerProvider"):
                        with patch("opentelemetry.sdk.resources.Resource.create"):
                            setup_opentelemetry(service_name="test")
                            mock_redis.return_value.instrument.assert_called_once()

    def test_auto_instrument_sqlalchemy(self):
        """Test SQLAlchemy auto-instrumentation."""
        # SQLAlchemy instrumentation may not be installed, skip if not available
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        except ImportError:
            pytest.skip("SQLAlchemy instrumentation not installed")
        
        with patch("opentelemetry.instrumentation.sqlalchemy.SQLAlchemyInstrumentor") as mock_sqlalchemy:
            with patch("opentelemetry.trace.set_tracer_provider"):
                with patch("opentelemetry.trace.get_tracer"):
                    with patch("opentelemetry.sdk.trace.TracerProvider"):
                        with patch("opentelemetry.sdk.resources.Resource.create"):
                            setup_opentelemetry(service_name="test")
                            mock_sqlalchemy.return_value.instrument.assert_called_once()


class TestGetTracer:
    """Test get_tracer function."""

    def teardown_method(self):
        """Reset global tracer after each test."""
        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = None

    def test_get_tracer_global_set(self):
        """Test getting global tracer when set."""
        mock_tracer = MagicMock()
        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = mock_tracer

        result = get_tracer()
        assert result is mock_tracer

    def test_get_tracer_global_not_set(self):
        """Test getting tracer when global not set."""
        with patch("opentelemetry.trace.get_tracer") as mock_get_tracer:
            mock_tracer = MagicMock()
            mock_get_tracer.return_value = mock_tracer

            result = get_tracer("custom_name")
            mock_get_tracer.assert_called_once_with("custom_name")

    def test_get_tracer_import_error(self):
        """Test getting tracer when opentelemetry not available."""
        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = None

        with patch.dict("sys.modules", {"opentelemetry": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'opentelemetry'")):
                result = get_tracer()
                assert isinstance(result, NoOpTracer)


class TestNoOpTracer:
    """Test NoOpTracer implementation."""

    def test_start_as_current_span(self):
        """Test start_as_current_span context manager."""
        tracer = NoOpTracer()

        with tracer.start_as_current_span("test") as span:
            assert isinstance(span, NoOpSpan)

    def test_start_span(self):
        """Test start_span method."""
        tracer = NoOpTracer()
        span = tracer.start_span("test")
        assert isinstance(span, NoOpSpan)


class TestNoOpSpan:
    """Test NoOpSpan implementation."""

    def test_all_methods(self):
        """Test that all NoOpSpan methods work."""
        span = NoOpSpan()

        # All these should not raise
        span.set_attribute("key", "value")
        span.set_attributes({"key": "value"})
        span.add_event("event")
        span.add_event("event", {"attr": "value"})
        span.record_exception(ValueError("test"))
        span.set_status(MagicMock())
        span.end()

    def test_context_manager(self):
        """Test using NoOpSpan as context manager."""
        span = NoOpSpan()

        with span:
            pass  # Should work without issues


class TestTraceSpan:
    """Test trace_span context manager."""

    def test_trace_span_with_global_tracer(self):
        """Test trace_span with global tracer."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = mock_tracer

        with trace_span("test_operation", {"key": "value"}) as span:
            mock_span.set_attribute.assert_called_with("key", "value")

    def test_trace_span_no_attributes(self):
        """Test trace_span without attributes."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = mock_tracer

        with trace_span("test_operation") as span:
            # set_attribute should not be called without attributes
            mock_span.set_attribute.assert_not_called()


class TestTracedDecorator:
    """Test traced decorator."""

    def teardown_method(self):
        """Reset global tracer after each test."""
        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = None

    def test_traced_sync_function(self):
        """Test traced decorator on sync function."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = mock_tracer

        @traced()
        def test_func():
            return "result"

        result = test_func()
        assert result == "result"
        mock_tracer.start_as_current_span.assert_called_once()

    def test_traced_async_function(self):
        """Test traced decorator on async function."""
        import asyncio

        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = mock_tracer

        @traced()
        async def test_async_func():
            return "async_result"

        result = asyncio.run(test_async_func())
        assert result == "async_result"

    def test_traced_with_custom_name(self):
        """Test traced decorator with custom span name."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = mock_tracer

        @traced(name="custom_span_name")
        def test_func():
            pass

        test_func()
        mock_tracer.start_as_current_span.assert_called_once_with("custom_span_name")

    def test_traced_with_attributes(self):
        """Test traced decorator with static attributes."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = mock_tracer

        @traced(attributes={"component": "database"})
        def test_func():
            pass

        test_func()
        mock_span.set_attributes.assert_called_once_with({"component": "database"})

    def test_traced_exception_handling(self):
        """Test that exceptions are recorded and re-raised."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        import ntlabs.observability.tracing as tracing_module
        tracing_module._tracer = mock_tracer

        @traced()
        def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            failing_func()

        mock_span.record_exception.assert_called_once()


class TestGetCurrentTraceId:
    """Test get_current_trace_id function."""

    def test_get_trace_id_success(self):
        """Test getting current trace ID."""
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.is_valid = True
        mock_context.trace_id = 12345678901234567890123456789012
        mock_span.get_span_context.return_value = mock_context

        with patch("opentelemetry.trace.get_current_span") as mock_get_span:
            mock_get_span.return_value = mock_span

            trace_id = get_current_trace_id()
            assert trace_id is not None
            assert len(trace_id) == 32  # 32 hex characters

    def test_get_trace_id_no_span(self):
        """Test when no current span."""
        with patch("opentelemetry.trace.get_current_span") as mock_get_span:
            mock_get_span.return_value = None

            trace_id = get_current_trace_id()
            assert trace_id is None

    def test_get_trace_id_invalid_context(self):
        """Test when span context is invalid."""
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.is_valid = False
        mock_span.get_span_context.return_value = mock_context

        with patch("opentelemetry.trace.get_current_span") as mock_get_span:
            mock_get_span.return_value = mock_span

            trace_id = get_current_trace_id()
            assert trace_id is None

    def test_get_trace_id_import_error(self):
        """Test handling of missing opentelemetry."""
        with patch.dict("sys.modules", {"opentelemetry": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'opentelemetry'")):
                trace_id = get_current_trace_id()
                assert trace_id is None


class TestGetCurrentSpanId:
    """Test get_current_span_id function."""

    def test_get_span_id_success(self):
        """Test getting current span ID."""
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.is_valid = True
        mock_context.span_id = 1234567890123456
        mock_span.get_span_context.return_value = mock_context

        with patch("opentelemetry.trace.get_current_span") as mock_get_span:
            mock_get_span.return_value = mock_span

            span_id = get_current_span_id()
            assert span_id is not None
            assert len(span_id) == 16  # 16 hex characters

    def test_get_span_id_no_span(self):
        """Test when no current span."""
        with patch("opentelemetry.trace.get_current_span") as mock_get_span:
            mock_get_span.return_value = None

            span_id = get_current_span_id()
            assert span_id is None

    def test_get_span_id_invalid_context(self):
        """Test when span context is invalid."""
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.is_valid = False
        mock_span.get_span_context.return_value = mock_context

        with patch("opentelemetry.trace.get_current_span") as mock_get_span:
            mock_get_span.return_value = mock_span

            span_id = get_current_span_id()
            assert span_id is None

    def test_get_span_id_import_error(self):
        """Test handling of missing opentelemetry."""
        with patch.dict("sys.modules", {"opentelemetry": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'opentelemetry'")):
                span_id = get_current_span_id()
                assert span_id is None
