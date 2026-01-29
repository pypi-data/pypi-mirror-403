"""Registry telemetry for self-monitoring.

This module provides instrumentation for monitoring registry operations,
including refresh success/failure rates and latencies.
"""

from typing import Optional
from opentelemetry import metrics


class RegistryTelemetry:
    """Telemetry instrumentation for registry operations.

    Provides metrics to monitor registry health and performance:
    - Refresh success/failure counters
    - Refresh latency histogram
    - Error counters by type

    Example:
        >>> from opentelemetry import metrics
        >>> meter = metrics.get_meter("my-app.registry")
        >>> telemetry = RegistryTelemetry(meter)
        >>> telemetry.record_success(latency=0.125)
        >>> telemetry.record_error("RegistryConnectionError")
    """

    def __init__(self, meter: Optional[metrics.Meter] = None):
        """Initialize registry telemetry.

        Args:
            meter: OpenTelemetry Meter instance (if None, uses default meter)
        """
        if meter is None:
            meter = metrics.get_meter("mca.registry")

        self._meter = meter

        # Create metrics
        self.refresh_success_counter = self._meter.create_counter(
            name="mca.registry.refresh_success_total",
            description="Total number of successful registry refreshes",
            unit="1",
        )

        self.refresh_latency_histogram = self._meter.create_histogram(
            name="mca.registry.refresh_latency_seconds",
            description="Latency of registry refresh operations",
            unit="s",
        )

        self.errors_counter = self._meter.create_counter(
            name="mca.registry.errors_total",
            description="Total number of registry errors by type",
            unit="1",
        )

    def record_success(self, latency: float) -> None:
        """Record a successful registry refresh.

        Args:
            latency: Refresh latency in seconds
        """
        self.refresh_success_counter.add(1)
        self.refresh_latency_histogram.record(latency)

    def record_error(self, error_type: str) -> None:
        """Record a registry error.

        Args:
            error_type: Type of error (e.g., "RegistryConnectionError")
        """
        self.errors_counter.add(1, {"error_type": error_type})
