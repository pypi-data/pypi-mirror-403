"""Vendor model integration bridge for MCA SDK.

This module provides a base class for integrating vendor models (like Epic AI)
that don't provide direct code access but expose metrics via APIs.
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..core.client import MCAClient

logger = logging.getLogger(__name__)


class VendorBridge(ABC):
    """Base class for vendor model metric bridges.

    Provides a framework for polling vendor APIs and transforming their
    metrics into OTLP format for the MCA SDK.

    Subclasses must implement:
        - fetch_metrics(): Poll vendor API for metrics
        - transform_metrics(): Transform vendor format to OTLP

    Features:
        - Background polling loop with configurable interval
        - Automatic error handling and backoff
        - Health check support
        - Graceful shutdown

    Examples:
        >>> class EpicSepsisBridge(VendorBridge):
        ...     def fetch_metrics(self):
        ...         response = requests.get(f"{self.endpoint}/metrics")
        ...         return response.json()
        ...
        ...     def transform_metrics(self, data):
        ...         return {
        ...             "vendor.predictions_total": data['prediction_count'],
        ...             "vendor.accuracy_ratio": data['accuracy']
        ...         }
        >>>
        >>> bridge = EpicSepsisBridge(
        ...     service_name="epic-sepsis",
        ...     vendor_name="epic",
        ...     endpoint="https://epic.hospital.com/api/models/sepsis"
        ... )
        >>> bridge.start()  # Runs in background
    """

    def __init__(
        self,
        service_name: str,
        vendor_name: str,
        endpoint: str,
        poll_interval: float = 60.0,
        model_type: str = "vendor",
        team_name: Optional[str] = None,
        **client_kwargs,
    ):
        """Initialize vendor bridge.

        Args:
            service_name: Name of the service
            vendor_name: Name of the vendor (e.g., "epic", "cerner")
            endpoint: Vendor API endpoint URL
            poll_interval: Polling interval in seconds (default: 60)
            model_type: Model type (default: "vendor")
            team_name: Team responsible for integration
            **client_kwargs: Additional arguments for MCAClient

        Example:
            >>> bridge = VendorBridge(
            ...     service_name="epic-sepsis-model",
            ...     vendor_name="epic",
            ...     endpoint="https://epic.hospital.com/api",
            ...     poll_interval=30.0,
            ...     team_name="integrations"
            ... )
        """
        self.service_name = service_name
        self.vendor_name = vendor_name
        self.endpoint = endpoint
        self.poll_interval = poll_interval

        # Create MCA client for telemetry
        self.client = MCAClient(
            service_name=service_name,
            model_type=model_type,
            vendor_name=vendor_name,
            team_name=team_name,
            **client_kwargs,
        )

        # Background worker state
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Statistics
        self._poll_count = 0
        self._success_count = 0
        self._error_count = 0

    @abstractmethod
    def fetch_metrics(self) -> Dict[str, Any]:
        """Fetch metrics from vendor API.

        Subclasses must implement this method to poll the vendor's API
        and return raw metrics data.

        Returns:
            Dictionary containing raw metrics from vendor API

        Raises:
            Exception: If API request fails

        Example:
            >>> def fetch_metrics(self):
            ...     response = requests.get(
            ...         f"{self.endpoint}/metrics",
            ...         headers={"Authorization": f"Bearer {self.api_key}"}
            ...     )
            ...     response.raise_for_status()
            ...     return response.json()
        """

    @abstractmethod
    def transform_metrics(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Transform vendor metrics to OTLP format.

        Subclasses must implement this method to transform vendor-specific
        metric names and formats into standard OTLP metrics.

        Args:
            data: Raw metrics data from vendor API

        Returns:
            Dictionary mapping metric names to values

        Example:
            >>> def transform_metrics(self, data):
            ...     return {
            ...         "vendor.predictions_total": data['metrics']['total_predictions'],
            ...         "vendor.accuracy_ratio": data['metrics']['accuracy_score'],
            ...         "vendor.latency_seconds": data['metrics']['avg_latency_ms'] / 1000
            ...     }
        """

    def start(self):
        """Start background polling loop.

        Starts a daemon thread that polls the vendor API at regular intervals
        and records metrics via the MCA client.

        Safe to call multiple times (no-op if already running).

        Example:
            >>> bridge.start()
            >>> # Bridge now polls every poll_interval seconds
        """
        with self._lock:
            if self._running:
                logger.warning(f"{self.service_name}: Bridge already running")
                return

            self._running = True
            self._worker_thread = threading.Thread(
                target=self._poll_loop, name=f"VendorBridge-{self.service_name}", daemon=True
            )
            self._worker_thread.start()
            logger.info(
                f"{self.service_name}: Started vendor bridge (poll interval: {self.poll_interval}s)"
            )

    def stop(self):
        """Stop background polling loop.

        Gracefully stops the polling thread and shuts down the MCA client.

        Safe to call multiple times (no-op if not running).

        Example:
            >>> bridge.stop()
        """
        with self._lock:
            if not self._running:
                return

            self._running = False

        # Wait for worker thread to finish
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5.0)
            logger.info(f"{self.service_name}: Stopped vendor bridge")

        # Shutdown MCA client
        self.client.shutdown()

    def _poll_loop(self):
        """Background polling loop (internal method).

        Periodically fetches metrics from vendor API, transforms them,
        and records via MCA client.
        """
        logger.debug(f"{self.service_name}: Poll loop started")

        while self._running:
            try:
                self._poll_count += 1

                # Fetch metrics from vendor API
                logger.debug(f"{self.service_name}: Fetching metrics (poll #{self._poll_count})")
                raw_data = self.fetch_metrics()

                # Transform to OTLP format
                metrics = self.transform_metrics(raw_data)

                # Record each metric
                for metric_name, value in metrics.items():
                    try:
                        self.client.record_metric(metric_name, value, vendor=self.vendor_name)
                    except Exception as e:
                        logger.error(
                            f"{self.service_name}: Error recording metric {metric_name}: {e}",
                            extra={"metric": metric_name, "error": str(e)},
                        )

                self._success_count += 1
                logger.debug(f"{self.service_name}: Successfully recorded {len(metrics)} metrics")

            except Exception as e:
                self._error_count += 1
                logger.error(
                    f"{self.service_name}: Error polling vendor API: {e}",
                    extra={
                        "poll_count": self._poll_count,
                        "error_count": self._error_count,
                        "error": str(e),
                    },
                )

            # Sleep until next poll
            time.sleep(self.poll_interval)

        logger.debug(f"{self.service_name}: Poll loop stopped")

    def get_stats(self) -> Dict[str, int]:
        """Get bridge statistics.

        Returns:
            Dictionary with polling statistics

        Example:
            >>> stats = bridge.get_stats()
            >>> print(f"Success rate: {stats['success_count'] / stats['poll_count']:.2%}")
        """
        return {
            "poll_count": self._poll_count,
            "success_count": self._success_count,
            "error_count": self._error_count,
        }

    def is_running(self) -> bool:
        """Check if bridge is currently running.

        Returns:
            True if polling loop is active, False otherwise
        """
        with self._lock:
            return self._running

    def health_check(self) -> bool:
        """Perform health check on vendor API.

        Attempts a single fetch_metrics() call to verify API connectivity.

        Returns:
            True if API is reachable, False otherwise

        Example:
            >>> if bridge.health_check():
            ...     print("Vendor API is healthy")
            ... else:
            ...     print("Vendor API is unreachable")
        """
        try:
            raw_data = self.fetch_metrics()
            metrics = self.transform_metrics(raw_data)
            return len(metrics) > 0
        except Exception as e:
            logger.error(f"{self.service_name}: Health check failed: {e}")
            return False
