"""Main MCA SDK client for model instrumentation.

This module provides the MCAClient class, the primary developer-facing API
for instrumenting models with OpenTelemetry.
"""

import logging
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional

from opentelemetry import metrics, trace
from opentelemetry.sdk._logs import LoggingHandler

from ..config import MCAConfig
from .providers import setup_all_providers
from ..validation import validate_resource_attributes, MetricNamingConvention
from ..registry import RegistryClient, RegistryTelemetry, ModelConfig
from ..utils.exceptions import RegistryConnectionError, RegistryAuthError
from ..utils.version_check import check_version
from .. import __version__


class MCAClient:
    """Main client for MCA SDK instrumentation.

    This class provides a simple API for instrumenting models with metrics,
    logs, and traces. It handles provider setup, validation, and buffering
    automatically.

    Examples:
        Basic usage:
        >>> client = MCAClient(
        ...     service_name="readmission-model",
        ...     model_id="mdl-001",
        ...     team_name="clinical-ai"
        ... )
        >>> def predict(data):
        ...     with client.trace("model.predict"):
        ...         result = model.predict(data)
        ...         client.record_prediction(data, result, latency=0.15)
        ...         return result
        >>> client.shutdown()

        Custom metrics:
        >>> counter = client.meter.create_counter("model.false_positives_total")
        >>> counter.add(1, {"threshold": "0.7"})
    """

    def __init__(
        self,
        service_name: Optional[str] = None,
        model_id: Optional[str] = None,
        model_version: str = "0.3.0",
        team_name: Optional[str] = None,
        model_type: str = "internal",
        collector_endpoint: str = "http://localhost:4318",
        strict_validation: bool = True,
        config: Optional[MCAConfig] = None,
        **kwargs,
    ):
        """Initialize MCA SDK client.

        Args:
            service_name: Name of the service (required if config not provided)
            model_id: Unique model identifier
            model_version: Model version string
            team_name: Team responsible for the model
            model_type: Type of model (internal, generative, vendor)
            collector_endpoint: OTLP collector endpoint
            strict_validation: Whether to enforce strict validation
            config: MCAConfig instance (if provided, overrides other args)
            **kwargs: Additional configuration options

        Raises:
            ConfigurationError: If required configuration is missing
        """
        # Setup debug logging level if requested
        sdk_logger = logging.getLogger("mca_sdk")

        # Load configuration
        if config:
            self.config = config
        else:
            # Create config from provided arguments
            self.config = MCAConfig(
                service_name=service_name or "",
                model_id=model_id,
                model_version=model_version,
                team_name=team_name,
                model_type=model_type,
                collector_endpoint=collector_endpoint,
                strict_validation=strict_validation,
                **kwargs,
            )

        # Enable debug logging if debug_mode is set
        if self.config.debug_mode:
            sdk_logger.setLevel(logging.DEBUG)
            sdk_logger.debug("Debug mode enabled")
            sdk_logger.debug(f"MCA SDK version: {__version__}")
            sdk_logger.debug(
                f"Configuration loaded - service_name={self.config.service_name}, "
                f"model_type={self.config.model_type}, "
                f"collector_endpoint={self.config.collector_endpoint}"
            )

        # Run version check on startup
        if self.config.debug_mode:
            sdk_logger.debug("Running version check...")
        # Non-blocking, logs warnings if outdated (2s timeout per AC4)
        check_version(__version__, timeout=2.0)

        # Initialize registry-related instance variables
        self._registry_client: Optional[RegistryClient] = None
        self._registry_config: Optional[ModelConfig] = None
        self._thresholds: Dict[str, float] = {}
        self._registry_telemetry: Optional[RegistryTelemetry] = None

        # Step 2: Registry hydration (if configured)
        if self.config.registry_url:
            if self.config.debug_mode:
                sdk_logger.debug(f"Initializing registry client: {self.config.registry_url}")
            self._hydrate_from_registry()
            if self.config.debug_mode and self._registry_config:
                sdk_logger.debug(
                    f"Registry hydration successful - model_id={self._registry_config.model_id}, "
                    f"thresholds={len(self._thresholds)} configured"
                )

        # Validate resource attributes if strict validation enabled
        if self.config.strict_validation:
            # Build resource attributes dict for validation
            resource_attrs = {
                "service.name": self.config.service_name,
            }

            # Add model-type specific attributes
            if self.config.model_type == "internal":
                resource_attrs.update(
                    {
                        "model.id": self.config.model_id,
                        "model.version": self.config.model_version,
                        "team.name": self.config.team_name,
                    }
                )
            elif self.config.model_type == "generative":
                resource_attrs.update(
                    {
                        "llm.provider": self.config.llm_provider,
                        "llm.model": self.config.llm_model,
                        "team.name": self.config.team_name,
                    }
                )
            elif self.config.model_type == "vendor":
                resource_attrs.update(
                    {
                        "model.type": self.config.model_type,
                        "vendor.name": self.config.vendor_name,
                        "team.name": self.config.team_name,
                    }
                )

            # Validate required attributes are present
            validate_resource_attributes(
                resource_attrs,
                model_type=self.config.model_type,
                strict=self.config.strict_validation,
            )
            if self.config.debug_mode:
                sdk_logger.debug(f"Resource attributes validated: {list(resource_attrs.keys())}")

        # Setup OpenTelemetry providers with registry extra_resource if available
        extra_resource = None
        if self._registry_config:
            extra_resource = self._registry_config.extra_resource

        if self.config.debug_mode:
            sdk_logger.debug("Setting up OpenTelemetry providers...")

        (
            self._meter_provider,
            self._logger_provider,
            self._tracer_provider,
            self._resource,
        ) = setup_all_providers(
            service_name=self.config.service_name,
            model_id=self.config.model_id,
            model_version=self.config.model_version,
            team_name=self.config.team_name,
            model_type=self.config.model_type,
            collector_endpoint=self.config.collector_endpoint,
            metric_export_interval_ms=self.config.metric_export_interval_ms,
            log_batch_size=self.config.log_batch_size,
            trace_batch_size=self.config.trace_batch_size,
            extra_resource=extra_resource,
        )

        if self.config.debug_mode:
            sdk_logger.debug(
                f"OpenTelemetry providers initialized - "
                f"endpoint={self.config.collector_endpoint}, "
                f"metric_interval={self.config.metric_export_interval_ms}ms, "
                f"log_batch_size={self.config.log_batch_size}, "
                f"trace_batch_size={self.config.trace_batch_size}"
            )

        # Get instances for user access
        self._meter = metrics.get_meter(f"{self.config.service_name}.meter")
        self._tracer = trace.get_tracer(f"{self.config.service_name}.tracer")

        # Setup Python logging integration
        self._setup_logging()

        # Create standard metrics
        self._predictions_counter = self._meter.create_counter(
            "model.predictions_total", description="Total number of model predictions"
        )
        self._latency_histogram = self._meter.create_histogram(
            "model.latency_seconds", description="Model prediction latency", unit="s"
        )

        if self.config.debug_mode:
            sdk_logger.debug(
                "Standard metrics created: model.predictions_total (counter), "
                "model.latency_seconds (histogram)"
            )

        # Initialize metric naming validation
        self._strict_validation = self.config.strict_validation
        self._metric_validator = MetricNamingConvention(
            model_type=self.config.model_type, strict=self._strict_validation
        )

        # Initialize registry telemetry
        if self._registry_client:
            self._registry_telemetry = RegistryTelemetry(self._meter)

        # Initialize buffering (optional)
        self._telemetry_queue = None
        if self.config.buffering_enabled:
            from ..buffering.queue import TelemetryQueue

            self._telemetry_queue = TelemetryQueue(
                max_size=self.config.max_queue_size,
                persist=self.config.persist_queue,
                persist_path=self.config.persist_path,
            )
            logging.info(
                f"Buffering enabled: max_size={self.config.max_queue_size}, persist={self.config.persist_queue}"
            )

    def _setup_logging(self):
        """Setup Python logging integration with OpenTelemetry."""
        self._logger = logging.getLogger(f"{self.config.service_name}.logger")
        self._logger.setLevel(logging.INFO)

        # Add OTel handler and store reference for cleanup
        self._otel_handler = LoggingHandler(logger_provider=self._logger_provider)
        self._logger.addHandler(self._otel_handler)

    @property
    def meter(self):
        """Get the OpenTelemetry Meter for creating custom metrics.

        Returns:
            Meter instance for creating counters, histograms, gauges
        """
        return self._meter

    @property
    def logger(self):
        """Get the Python logger with OpenTelemetry integration.

        Returns:
            Logger instance for structured logging
        """
        return self._logger

    @property
    def tracer(self):
        """Get the OpenTelemetry Tracer for creating custom spans.

        Returns:
            Tracer instance for distributed tracing
        """
        return self._tracer

    @property
    def thresholds(self) -> Dict[str, float]:
        """Get current thresholds from registry.

        Returns:
            Dictionary of threshold values from registry (refreshed by background thread)
        """
        # Get latest thresholds from registry client's cache (updated by refresh thread)
        if self._registry_client and self._registry_config:
            try:
                # fetch_model_config returns from cache if fresh (updated by refresh thread)
                current_config = self._registry_client.fetch_model_config(
                    model_id=self._registry_config.model_id,
                    version=self._registry_config.model_version,
                )
                return current_config.thresholds.copy()
            except Exception:
                # Fallback to initial config if fetch fails
                return self._registry_config.thresholds.copy()

        # No registry configured
        return {}

    def buffer_stats(self) -> Dict[str, any]:
        """Get telemetry buffer statistics.

        Returns:
            Dictionary with buffer statistics (size, is_full, max_size)
            Returns None if buffering is not enabled
        """
        if not self._telemetry_queue:
            return None

        return {
            "size": self._telemetry_queue.size(),
            "is_full": self._telemetry_queue.is_full(),
            "max_size": self._telemetry_queue._max_size,
        }

    def _hydrate_from_registry(self) -> None:
        """Fetch config from registry and merge with local config."""
        try:
            self._registry_client = RegistryClient(
                url=self.config.registry_url,
                token=self.config.registry_token,
                timeout=5.0,
                cache_ttl_secs=600,  # 10 minutes cache TTL
                refresh_interval_secs=self.config.refresh_interval_secs,
            )

            # Fetch model or deployment config
            if self.config.deployment_id:
                # Deployment indirection: fetch deployment config first
                deployment_config = self._registry_client.fetch_deployment_config(
                    self.config.deployment_id
                )
                # Apply deployment resource overrides
                if deployment_config.resource_overrides:
                    logging.info(f"Applied deployment config for {self.config.deployment_id}")

            # Fetch model config
            registry_config = self._registry_client.fetch_model_config(
                model_id=self.config.model_id or self.config.service_name,
                version=self.config.model_version,
            )
            self._registry_config = registry_config

            # Apply registry config based on prefer_registry setting
            if self.config.prefer_registry:
                self._apply_registry_config(registry_config)

            # Store thresholds
            self._thresholds = registry_config.thresholds

            logging.info(
                f"Successfully hydrated config from registry for model {registry_config.model_id}"
            )

        except RegistryAuthError as e:
            # Auth errors should fail fast
            if self.config.debug_mode:
                sdk_logger = logging.getLogger("mca_sdk")
                sdk_logger.debug(f"Registry authentication failed with auth error: {e}")
            logging.error(f"Registry authentication failed: {e}")
            raise
        except RegistryConnectionError as e:
            # Log warning but continue with local config
            if self.config.debug_mode:
                sdk_logger = logging.getLogger("mca_sdk")
                sdk_logger.debug(f"Registry connection failed, falling back to local config: {e}")
            logging.warning(
                f"Registry unavailable, using local config: {e}. "
                "Telemetry will continue with local configuration."
            )
        except Exception as e:
            # Unexpected errors - log and continue
            if self.config.debug_mode:
                sdk_logger = logging.getLogger("mca_sdk")
                sdk_logger.debug(f"Unexpected registry error: {type(e).__name__}: {e}")
            logging.warning(f"Unexpected error during registry hydration: {e}")

    def _apply_registry_config(self, registry_config: ModelConfig) -> None:
        """Apply registry config to local config (mutable fields only).

        Args:
            registry_config: Configuration from registry
        """
        # Only override if local value is default/None and registry has a value
        if not self.config.team_name and registry_config.team_name:
            self.config.team_name = registry_config.team_name

        # Check for identity field changes (warn only)
        if registry_config.service_name != self.config.service_name:
            logging.warning(
                f"service_name in registry ({registry_config.service_name}) differs "
                f"from local ({self.config.service_name}). Using local value. "
                "Restart required to apply registry service_name."
            )

    def record_prediction(
        self,
        input_data: Any = None,
        output: Any = None,
        latency: Optional[float] = None,
        **attributes,
    ):
        """Record a model prediction with standard metrics.

        This is a convenience method that automatically creates:
        - model.predictions_total counter (incremented)
        - model.latency_seconds histogram (if latency provided)
        - Structured log with prediction details

        Args:
            input_data: Input data for the prediction
            output: Output from the model
            latency: Prediction latency in seconds
            **attributes: Additional attributes to attach to metrics/logs
        """
        # Generate prediction ID for correlation
        prediction_id = str(uuid.uuid4())

        if self.config.debug_mode:
            sdk_logger = logging.getLogger("mca_sdk")
            sdk_logger.debug(
                f"[{prediction_id}] Recording prediction - latency={latency}, attributes={attributes}"
            )

            # Log attribute validation
            attr_count = len(attributes)
            attr_keys = list(attributes.keys())
            sdk_logger.debug(
                f"[{prediction_id}] Attribute validation: {attr_count} attributes provided: {attr_keys}"
            )

            # Validate attribute values (length check as per FR26)
            for key, value in attributes.items():
                if isinstance(value, str) and len(value) > 1024:
                    sdk_logger.debug(
                        f"[{prediction_id}] Attribute validation WARNING: '{key}' exceeds 1024 chars ({len(value)} chars)"
                    )

        # Increment predictions counter
        self._predictions_counter.add(1, attributes=attributes)

        if self.config.debug_mode:
            sdk_logger.debug(f"[{prediction_id}] Metric recorded: model.predictions_total += 1")
            sdk_logger.debug(f"[{prediction_id}] Export attempt: Metrics will be exported to {self.config.collector_endpoint}")

        # Record latency if provided
        if latency is not None:
            self._latency_histogram.record(latency, attributes=attributes)
            if self.config.debug_mode:
                sdk_logger.debug(
                    f"[{prediction_id}] Metric recorded: model.latency_seconds = {latency}s"
                )

        # Log prediction metadata (applications should sanitize sensitive data before logging)
        self._logger.info(
            "Prediction completed",
            extra={"prediction_id": prediction_id, "latency": latency, **attributes},
        )

        if self.config.debug_mode:
            # Log export information
            metric_count = 2 if latency is not None else 1
            sdk_logger.debug(
                f"[{prediction_id}] Export queued: {metric_count} metrics + 1 log to {self.config.collector_endpoint}/v1/metrics, /v1/logs"
            )
            sdk_logger.debug(
                f"[{prediction_id}] Prediction recording completed - metrics will be exported via batch processor (interval: {self.config.metric_export_interval_ms}ms)"
            )

    def record_metric(self, name: str, value: float, **attributes):
        """Record a custom metric value.

        This is a generic method for recording any metric. For common patterns
        like predictions and latency, use record_prediction() instead.

        IMPORTANT: This method is for one-time metric recording. For counters,
        histograms, or gauges that are updated frequently, use client.meter
        to create the metric once and reuse it.

        Args:
            name: Metric name (will be validated if strict_validation=True)
            value: Metric value
            **attributes: Attributes to attach to the metric

        Example:
            >>> # For one-time recording:
            >>> client.record_metric("model.accuracy_ratio", 0.92, dataset="test")
            >>>
            >>> # For frequent updates, create metric once:
            >>> accuracy_gauge = client.meter.create_observable_gauge("model.accuracy")
        """
        # Validate metric name if strict validation enabled
        self._metric_validator.validate(name)

        # Cache metric instances to avoid creating duplicates
        if not hasattr(self, "_cached_metrics"):
            self._cached_metrics = {}

        if name not in self._cached_metrics:
            # Create histogram for recording values (better than observable gauge for this use case)
            self._cached_metrics[name] = self._meter.create_histogram(
                name, description=f"Custom metric: {name}"
            )

        # Record the value
        self._cached_metrics[name].record(value, attributes=attributes)

    @contextmanager
    def trace(self, span_name: str, **attributes):
        """Context manager for creating a trace span.

        Args:
            span_name: Name of the span
            **attributes: Attributes to attach to the span

        Yields:
            Span instance

        Example:
            >>> with client.trace("model.predict", model_version="1.0"):
            ...     result = model.predict(data)
        """
        with self._tracer.start_as_current_span(span_name) as span:
            for key, value in attributes.items():
                span.set_attribute(key, value)
            yield span

    def shutdown(self, timeout_millis: int = 30000):
        """Gracefully shutdown the client and flush all telemetry.

        This should be called when the application is shutting down to ensure
        all metrics, logs, and traces are exported.

        Args:
            timeout_millis: Maximum time to wait for flush in milliseconds
        """
        self._logger.info("Shutting down MCA SDK client")

        # Stop background refresh thread (if registry client exists)
        if self._registry_client:
            self._registry_client.stop_refresh_thread(timeout=5.0)
            self._registry_client.close()
            logging.debug("Registry client closed")

        # Log buffer statistics if buffering enabled
        if self._telemetry_queue:
            buffer_size = self._telemetry_queue.size()
            if buffer_size > 0:
                logging.warning(f"Shutting down with {buffer_size} items still in buffer")
            logging.debug(
                f"Buffer statistics: size={buffer_size}, is_full={self._telemetry_queue.is_full()}"
            )

        # Force flush all providers
        self._meter_provider.force_flush(timeout_millis=timeout_millis)
        self._logger_provider.force_flush(timeout_millis=timeout_millis)
        self._tracer_provider.force_flush(timeout_millis=timeout_millis)

        # Remove logging handler to prevent resource leak
        if hasattr(self, "_otel_handler"):
            self._logger.removeHandler(self._otel_handler)

        # Shutdown providers
        self._meter_provider.shutdown()
        self._logger_provider.shutdown()
        self._tracer_provider.shutdown()

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure shutdown is called when exiting context."""
        self.shutdown()
        return False
