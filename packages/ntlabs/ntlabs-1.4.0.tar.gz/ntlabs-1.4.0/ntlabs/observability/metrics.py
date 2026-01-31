"""
Metrics collection for Prometheus.

Provides metrics collection utilities compatible with Prometheus.
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """Single metric value."""

    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """
    Prometheus-compatible metrics collector.

    Example:
        metrics = MetricsCollector(namespace="hipocrates")

        # Counter
        metrics.increment("api_requests", labels={"endpoint": "/api/chat"})

        # Gauge
        metrics.set_gauge("active_users", 42)

        # Histogram
        metrics.histogram("response_time", 0.123, labels={"endpoint": "/api/chat"})

        # Timer context manager
        with metrics.timer("process_time"):
            do_something()

        # Get Prometheus format
        output = metrics.export_prometheus()
    """

    def __init__(
        self,
        namespace: str = "",
        default_labels: dict[str, str] | None = None,
    ):
        """
        Initialize metrics collector.

        Args:
            namespace: Prefix for all metric names
            default_labels: Labels applied to all metrics
        """
        self.namespace = namespace
        self.default_labels = default_labels or {}

        # Storage
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}

        # Metric metadata
        self._metric_help: dict[str, str] = {}
        self._metric_type: dict[str, str] = {}

    def _make_name(self, name: str) -> str:
        """Create full metric name with namespace."""
        if self.namespace:
            return f"{self.namespace}_{name}"
        return name

    def _make_key(self, name: str, labels: dict[str, str]) -> str:
        """Create storage key from name and labels."""
        all_labels = {**self.default_labels, **labels}
        if not all_labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(all_labels.items()))
        return f"{name}{{{label_str}}}"

    def register(
        self,
        name: str,
        metric_type: str,
        help_text: str = "",
    ) -> None:
        """
        Register a metric with metadata.

        Args:
            name: Metric name
            metric_type: Type (counter, gauge, histogram)
            help_text: Description
        """
        full_name = self._make_name(name)
        self._metric_type[full_name] = metric_type
        self._metric_help[full_name] = help_text

    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        Increment a counter.

        Args:
            name: Metric name
            value: Increment value
            labels: Additional labels
        """
        full_name = self._make_name(name)
        key = self._make_key(full_name, labels or {})

        if key not in self._counters:
            self._counters[key] = 0

        self._counters[key] += value

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        Set a gauge value.

        Args:
            name: Metric name
            value: Gauge value
            labels: Additional labels
        """
        full_name = self._make_name(name)
        key = self._make_key(full_name, labels or {})
        self._gauges[key] = value

    def histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        Observe a histogram value.

        Args:
            name: Metric name
            value: Observed value
            labels: Additional labels
        """
        full_name = self._make_name(name)
        key = self._make_key(full_name, labels or {})

        if key not in self._histograms:
            self._histograms[key] = []

        self._histograms[key].append(value)

    @contextmanager
    def timer(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ):
        """
        Context manager to time operations.

        Example:
            with metrics.timer("request_duration", labels={"endpoint": "/api"}):
                process_request()
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.histogram(name, duration, labels)

    def timed(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ):
        """
        Decorator to time function execution.

        Example:
            @metrics.timed("function_duration")
            def my_function():
                pass
        """

        def decorator(func):
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.timer(name, labels):
                    return func(*args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.timer(name, labels):
                    return await func(*args, **kwargs)

            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus exposition format string
        """
        lines = []

        # Export counters
        for key, value in self._counters.items():
            name = key.split("{")[0] if "{" in key else key
            if name in self._metric_help:
                lines.append(f"# HELP {name} {self._metric_help[name]}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{key} {value}")

        # Export gauges
        for key, value in self._gauges.items():
            name = key.split("{")[0] if "{" in key else key
            if name in self._metric_help:
                lines.append(f"# HELP {name} {self._metric_help[name]}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{key} {value}")

        # Export histogram summaries
        for key, values in self._histograms.items():
            name = key.split("{")[0] if "{" in key else key
            if name in self._metric_help:
                lines.append(f"# HELP {name} {self._metric_help[name]}")
            lines.append(f"# TYPE {name} histogram")

            if values:
                count = len(values)
                total = sum(values)
                lines.append(f"{key}_count {count}")
                lines.append(f"{key}_sum {total}")

                # Calculate percentiles
                sorted_values = sorted(values)
                for quantile in [0.5, 0.9, 0.95, 0.99]:
                    idx = int(len(sorted_values) * quantile)
                    idx = min(idx, len(sorted_values) - 1)
                    q_key = key.replace("}", f',quantile="{quantile}"}}')
                    if "{" not in key:
                        q_key = f'{key}{{quantile="{quantile}"}}'
                    lines.append(f"{q_key} {sorted_values[idx]}")

        return "\n".join(lines)

    def get_stats(self) -> dict[str, Any]:
        """Get metrics as dictionary."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "avg": sum(v) / len(v) if v else 0,
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                }
                for k, v in self._histograms.items()
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()


# Global metrics instance
_global_metrics: MetricsCollector | None = None


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    return _global_metrics


def set_metrics(metrics: MetricsCollector) -> None:
    """Set global metrics collector."""
    global _global_metrics
    _global_metrics = metrics
