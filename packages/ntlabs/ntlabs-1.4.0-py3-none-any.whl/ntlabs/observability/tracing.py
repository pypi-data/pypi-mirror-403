"""
OpenTelemetry tracing integration.

Provides distributed tracing for microservices.
"""

import logging
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

# Global tracer
_tracer = None


def setup_opentelemetry(
    service_name: str,
    otlp_endpoint: str | None = None,
    environment: str = "production",
    sample_rate: float = 1.0,
    enable_console_export: bool = False,
    resource_attributes: dict[str, str] | None = None,
) -> bool:
    """
    Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP collector endpoint (e.g., "http://localhost:4317")
        environment: Environment name
        sample_rate: Sampling rate (0.0 - 1.0)
        enable_console_export: Export traces to console (for debugging)
        resource_attributes: Additional resource attributes

    Returns:
        True if initialization succeeded

    Example:
        from ntlabs.observability import setup_opentelemetry

        setup_opentelemetry(
            service_name="hipocrates-api",
            otlp_endpoint="http://collector:4317",
            environment="production",
        )
    """
    global _tracer

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    except ImportError:
        logger.warning(
            "opentelemetry packages not installed. "
            "Install with: pip install opentelemetry-sdk opentelemetry-exporter-otlp"
        )
        return False

    # Build resource
    resource_attrs = {
        SERVICE_NAME: service_name,
        "deployment.environment": environment,
    }
    if resource_attributes:
        resource_attrs.update(resource_attributes)

    resource = Resource.create(resource_attrs)

    # Create tracer provider
    sampler = TraceIdRatioBased(sample_rate)
    provider = TracerProvider(resource=resource, sampler=sampler)

    # Add exporters
    try:
        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(f"OTLP exporter configured: {otlp_endpoint}")

        if enable_console_export:
            from opentelemetry.sdk.trace.export import (
                ConsoleSpanExporter,
                SimpleSpanProcessor,
            )

            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    except ImportError as e:
        logger.warning(f"Could not configure exporter: {e}")

    # Set global tracer provider
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name)

    # Instrument common libraries
    _auto_instrument()

    logger.info(f"OpenTelemetry initialized: service={service_name}")
    return True


def _auto_instrument():
    """Auto-instrument common libraries."""
    # FastAPI
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor().instrument()
    except ImportError:
        pass

    # HTTPX
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except ImportError:
        pass

    # Redis
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
    except ImportError:
        pass

    # SQLAlchemy
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument()
    except ImportError:
        pass


def get_tracer(name: str | None = None):
    """
    Get a tracer instance.

    Args:
        name: Tracer name (uses default if not provided)

    Returns:
        Tracer instance
    """
    global _tracer

    if _tracer is None:
        try:
            from opentelemetry import trace

            return trace.get_tracer(name or "ntlabs")
        except ImportError:
            return NoOpTracer()

    return _tracer


class NoOpTracer:
    """No-op tracer for when OpenTelemetry is not available."""

    @contextmanager
    def start_as_current_span(self, name, **kwargs):
        yield NoOpSpan()

    def start_span(self, name, **kwargs):
        return NoOpSpan()


class NoOpSpan:
    """No-op span."""

    def set_attribute(self, key, value):
        pass

    def set_attributes(self, attributes):
        pass

    def add_event(self, name, attributes=None):
        pass

    def record_exception(self, exception):
        pass

    def set_status(self, status):
        pass

    def end(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
):
    """
    Create a trace span context manager.

    Args:
        name: Span name
        attributes: Span attributes

    Example:
        with trace_span("process_order", {"order_id": "123"}):
            process_order()
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def traced(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
):
    """
    Decorator to trace function execution.

    Args:
        name: Span name (uses function name if not provided)
        attributes: Static attributes to add to span

    Example:
        @traced()
        async def process_payment(payment_id: str):
            pass

        @traced(name="custom_name", attributes={"component": "payment"})
        def sync_function():
            pass
    """

    def decorator(func: Callable):
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    span.set_attributes(attributes)
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    span.set_attributes(attributes)
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_current_trace_id() -> str | None:
    """
    Get current trace ID.

    Returns:
        Trace ID as hex string or None
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span:
            context = span.get_span_context()
            if context.is_valid:
                return format(context.trace_id, "032x")
    except ImportError:
        pass

    return None


def get_current_span_id() -> str | None:
    """
    Get current span ID.

    Returns:
        Span ID as hex string or None
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span:
            context = span.get_span_context()
            if context.is_valid:
                return format(context.span_id, "016x")
    except ImportError:
        pass

    return None
