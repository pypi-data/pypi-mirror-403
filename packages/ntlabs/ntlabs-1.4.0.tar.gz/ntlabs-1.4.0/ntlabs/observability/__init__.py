"""
NTLabs Observability - Monitoring and tracking utilities.

This module provides observability tools:
- Audit logging with Supabase
- Metrics collection for Prometheus
- Sentry error tracking
- OpenTelemetry distributed tracing

Quick Start:
    # Audit logging
    from ntlabs.observability import AuditLogger, AuditCategory

    audit = AuditLogger(
        service="hipocrates-api",
        supabase_url="https://xxx.supabase.co",
        supabase_key="xxx",
    )

    await audit.log(
        action="user_login",
        category=AuditCategory.AUTH,
        user_id="user_123",
    )

    # Metrics
    from ntlabs.observability import MetricsCollector

    metrics = MetricsCollector(namespace="myapp")
    metrics.increment("api_requests", labels={"endpoint": "/api"})
    metrics.histogram("response_time", 0.123)

    with metrics.timer("process_time"):
        do_work()

    # Sentry
    from ntlabs.observability import setup_sentry, capture_exception

    setup_sentry(
        dsn="https://xxx@sentry.io/123",
        environment="production",
    )

    try:
        risky_operation()
    except Exception as e:
        capture_exception(e)

    # OpenTelemetry
    from ntlabs.observability import setup_opentelemetry, traced, trace_span

    setup_opentelemetry(
        service_name="myapp",
        otlp_endpoint="http://collector:4317",
    )

    @traced()
    async def my_function():
        with trace_span("sub_operation"):
            pass
"""

from .audit import (
    AuditCategory,
    AuditEntry,
    AuditLogger,
    AuditSeverity,
)
from .metrics import (
    MetricsCollector,
    MetricValue,
    get_metrics,
    set_metrics,
)
from .sentry import (
    add_breadcrumb,
    capture_exception,
    capture_message,
    set_user_context,
    setup_sentry,
)
from .tracing import (
    get_current_span_id,
    get_current_trace_id,
    get_tracer,
    setup_opentelemetry,
    trace_span,
    traced,
)

__all__ = [
    # Audit
    "AuditLogger",
    "AuditEntry",
    "AuditSeverity",
    "AuditCategory",
    # Metrics
    "MetricsCollector",
    "MetricValue",
    "get_metrics",
    "set_metrics",
    # Sentry
    "setup_sentry",
    "capture_exception",
    "capture_message",
    "set_user_context",
    "add_breadcrumb",
    # Tracing
    "setup_opentelemetry",
    "get_tracer",
    "trace_span",
    "traced",
    "get_current_trace_id",
    "get_current_span_id",
]
