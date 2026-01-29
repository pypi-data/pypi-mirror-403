"""Buffered OTLP exporters with automatic retry and queueing.

This module provides wrapped OTLP exporters that queue telemetry when
the collector is unreachable and automatically retry with exponential backoff.
"""

import logging
import threading
import time
from typing import Optional

from opentelemetry.sdk.metrics.export import (
    MetricsData,
)
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

from .queue import TelemetryQueue
from .retry import RetryPolicy
from ..utils.exceptions import BufferingError

logger = logging.getLogger(__name__)


class BufferedOTLPMetricExporter:
    """Buffered wrapper for OTLP metric exporter.

    Wraps the standard OTLPMetricExporter to provide automatic queueing
    and retry logic when the collector is temporarily unreachable.

    Features:
        - Automatic queueing of failed exports
        - Background worker thread drains queue periodically
        - Retry logic with exponential backoff
        - Graceful shutdown with final flush
        - Prevents infinite queue growth on persistent failures

    Thread Safety:
        All operations are thread-safe. The background worker runs in
        a separate daemon thread.

    Examples:
        >>> queue = TelemetryQueue(max_size=1000)
        >>> retry_policy = RetryPolicy(max_attempts=3)
        >>> exporter = BufferedOTLPMetricExporter(
        ...     endpoint="http://localhost:4318/v1/metrics",
        ...     queue=queue,
        ...     retry_policy=retry_policy
        ... )
        >>> # Exporter will automatically queue and retry failed exports
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:4318/v1/metrics",
        headers: Optional[dict] = None,
        timeout: int = 10,
        queue: Optional[TelemetryQueue] = None,
        retry_policy: Optional[RetryPolicy] = None,
        drain_interval: float = 1.0,
        max_retry_queue_size: int = 100,
    ):
        """Initialize buffered metric exporter.

        Args:
            endpoint: OTLP collector endpoint URL
            headers: Optional HTTP headers for requests
            timeout: Request timeout in seconds
            queue: TelemetryQueue for buffering (creates default if None)
            retry_policy: RetryPolicy for retries (creates default if None)
            drain_interval: Seconds between queue drain attempts (default: 1.0)
            max_retry_queue_size: Max items to re-queue on failure (default: 100)

        Raises:
            BufferingError: If configuration is invalid
        """
        if drain_interval <= 0:
            raise BufferingError(f"drain_interval must be positive, got {drain_interval}")

        if max_retry_queue_size <= 0:
            raise BufferingError(
                f"max_retry_queue_size must be positive, got {max_retry_queue_size}"
            )

        # Create underlying OTLP exporter
        self._exporter = OTLPMetricExporter(endpoint=endpoint, headers=headers, timeout=timeout)

        # Queue and retry policy
        self._queue = queue or TelemetryQueue(max_size=1000)
        self._retry_policy = retry_policy or RetryPolicy(max_attempts=3)

        # Configuration
        self._drain_interval = drain_interval
        self._max_retry_queue_size = max_retry_queue_size

        # Background worker state
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Metrics for monitoring
        self._export_attempts = 0
        self._export_successes = 0
        self._export_failures = 0
        self._items_queued = 0
        self._items_requeued = 0

    def export(self, metrics_data: MetricsData) -> bool:
        """Export metrics data (with automatic queueing on failure).

        This method is called by the OpenTelemetry SDK to export metrics.
        If export fails, data is automatically queued for retry.

        Args:
            metrics_data: Metrics to export

        Returns:
            True if export succeeded or was queued, False otherwise

        Note:
            This method is called by the OTel SDK, not user code.
        """
        self._export_attempts += 1

        try:
            # Try to export directly first
            result = self._retry_policy.execute(self._exporter.export, metrics_data)

            if result.is_success:
                self._export_successes += 1
                logger.debug("Metric export succeeded")
                return True
            else:
                # Export failed, queue for retry
                logger.warning(
                    f"Metric export failed: {result.description}",
                    extra={"description": result.description},
                )
                self._queue_for_retry(metrics_data)
                return True  # Return True because we queued it

        except Exception as e:
            # Exception during export, queue for retry
            self._export_failures += 1
            logger.error(f"Exception during metric export: {e}", extra={"error": str(e)})
            self._queue_for_retry(metrics_data)
            return True  # Return True because we queued it

    def _queue_for_retry(self, metrics_data: MetricsData) -> None:
        """Queue failed metrics for retry (internal method).

        Args:
            metrics_data: Metrics to queue
        """
        # Check if queue is getting too full
        if self._queue.size() >= self._max_retry_queue_size:
            logger.warning(
                "Queue size limit reached, dropping metrics to prevent unbounded growth",
                extra={
                    "queue_size": self._queue.size(),
                    "max_retry_queue_size": self._max_retry_queue_size,
                },
            )
            return

        # Enqueue metrics
        queued = self._queue.enqueue(metrics_data)
        if queued:
            self._items_queued += 1
            logger.debug(
                f"Queued metrics for retry (queue size: {self._queue.size()})",
                extra={"queue_size": self._queue.size()},
            )
        else:
            logger.warning("Queue is full, metrics were dropped")

    def start_background_worker(self) -> None:
        """Start background worker thread to drain queue.

        The worker periodically attempts to export queued metrics.
        Safe to call multiple times (no-op if already running).

        Example:
            >>> exporter.start_background_worker()
            >>> # Worker now drains queue every drain_interval seconds
        """
        with self._lock:
            if self._running:
                logger.debug("Background worker already running")
                return

            self._running = True
            self._worker_thread = threading.Thread(
                target=self._worker_loop, name="BufferedExporter-Worker", daemon=True
            )
            self._worker_thread.start()
            logger.info("Started background worker thread")

    def stop_background_worker(self) -> None:
        """Stop background worker thread.

        Waits for worker to finish current operation before stopping.
        Safe to call multiple times (no-op if not running).

        Example:
            >>> exporter.stop_background_worker()
        """
        with self._lock:
            if not self._running:
                return

            self._running = False

        # Wait for worker thread to finish
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5.0)
            logger.info("Stopped background worker thread")

    def _worker_loop(self) -> None:
        """Background worker loop (internal method).

        Periodically drains queue and attempts to export metrics.
        Runs until stop_background_worker() is called.
        """
        logger.debug("Background worker loop started")

        while self._running:
            try:
                # Drain a batch from queue
                batch_size = min(10, self._queue.size())
                if batch_size > 0:
                    batch = self._queue.dequeue_batch(batch_size)

                    logger.debug(
                        f"Draining {len(batch)} items from queue", extra={"batch_size": len(batch)}
                    )

                    # Try to export each item
                    for metrics_data in batch:
                        try:
                            result = self._retry_policy.execute(self._exporter.export, metrics_data)

                            if result.is_success:
                                self._export_successes += 1
                                logger.debug("Queued metrics exported successfully")
                            else:
                                # Failed again, re-queue if not at limit
                                self._items_requeued += 1
                                if self._queue.size() < self._max_retry_queue_size:
                                    self._queue.enqueue(metrics_data)
                                    logger.warning(
                                        f"Re-queued failed metrics: {result.description}"
                                    )
                                else:
                                    logger.warning("Dropped metrics: queue limit reached")

                        except Exception as e:
                            # Re-queue on exception
                            self._items_requeued += 1
                            if self._queue.size() < self._max_retry_queue_size:
                                self._queue.enqueue(metrics_data)
                                logger.warning(f"Re-queued metrics after exception: {e}")

            except Exception as e:
                logger.error(f"Error in worker loop: {e}", extra={"error": str(e)})

            # Sleep until next drain
            time.sleep(self._drain_interval)

        logger.debug("Background worker loop stopped")

    def flush(self, timeout_millis: int = 30000) -> bool:
        """Flush all queued metrics.

        Attempts to export all queued metrics within the timeout period.
        Blocks until complete or timeout is reached.

        Args:
            timeout_millis: Maximum time to wait in milliseconds

        Returns:
            True if all metrics were flushed, False otherwise

        Example:
            >>> exporter.flush(timeout_millis=10000)  # Wait up to 10s
            True
        """
        timeout_seconds = timeout_millis / 1000.0
        start_time = time.time()

        logger.info(
            f"Flushing queue ({self._queue.size()} items)",
            extra={"queue_size": self._queue.size(), "timeout_seconds": timeout_seconds},
        )

        while self._queue.size() > 0:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout_seconds:
                logger.warning(
                    f"Flush timeout reached, {self._queue.size()} items remain",
                    extra={"queue_size": self._queue.size()},
                )
                return False

            # Drain one item
            metrics_data = self._queue.dequeue()
            if metrics_data is None:
                break  # Queue empty

            try:
                result = self._retry_policy.execute(self._exporter.export, metrics_data)
                if not result.is_success:
                    logger.warning(f"Failed to flush metrics: {result.description}")
            except Exception as e:
                logger.error(f"Exception during flush: {e}")

        # Also flush underlying exporter
        try:
            self._exporter.force_flush(timeout_millis=int(timeout_millis))
        except Exception as e:
            logger.error(f"Error flushing underlying exporter: {e}")

        logger.info("Flush completed")
        return self._queue.size() == 0

    def shutdown(self) -> None:
        """Shutdown exporter gracefully.

        Stops background worker, flushes remaining metrics, and cleans up resources.

        Example:
            >>> exporter.shutdown()
        """
        logger.info("Shutting down buffered exporter")

        # Stop background worker
        self.stop_background_worker()

        # Final flush
        self.flush(timeout_millis=5000)

        # Shutdown underlying exporter
        try:
            self._exporter.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down underlying exporter: {e}")

        logger.info(
            f"Buffered exporter shutdown complete. Stats: "
            f"attempts={self._export_attempts}, "
            f"successes={self._export_successes}, "
            f"failures={self._export_failures}, "
            f"queued={self._items_queued}, "
            f"requeued={self._items_requeued}"
        )

    def get_stats(self) -> dict:
        """Get exporter statistics.

        Returns:
            Dictionary with export statistics

        Example:
            >>> stats = exporter.get_stats()
            >>> print(f"Success rate: {stats['successes'] / stats['attempts']:.2%}")
        """
        return {
            "export_attempts": self._export_attempts,
            "export_successes": self._export_successes,
            "export_failures": self._export_failures,
            "items_queued": self._items_queued,
            "items_requeued": self._items_requeued,
            "queue_size": self._queue.size(),
        }
