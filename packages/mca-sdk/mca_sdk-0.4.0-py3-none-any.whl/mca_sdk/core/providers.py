"""Provider setup functions for OpenTelemetry.

This module provides functions to initialize MeterProvider, LoggerProvider,
and TracerProvider with proper configuration and exporters.
"""

import warnings
from typing import Dict, Optional
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry._logs import set_logger_provider, get_logger_provider
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


class ProviderAlreadySetWarning(UserWarning):
    """Warning when attempting to set a provider that's already configured."""


def create_resource_attributes(
    service_name: str,
    model_id: Optional[str] = None,
    model_version: str = "0.3.0",
    team_name: Optional[str] = None,
    model_type: str = "internal",
    extra_resource: Optional[Dict[str, str]] = None,
    **kwargs,
) -> Resource:
    """Create OpenTelemetry Resource with model metadata.

    Args:
        service_name: Name of the service
        model_id: Unique model identifier
        model_version: Model version string
        team_name: Team responsible for the model
        model_type: Type of model (internal, generative, vendor)
        extra_resource: Additional resource attributes from registry
        **kwargs: Additional resource attributes

    Returns:
        Resource instance with model metadata
    """
    attributes = {
        "service.name": service_name,
        "model.version": model_version,
        "model.type": model_type,
    }

    if model_id:
        attributes["model.id"] = model_id
    if team_name:
        attributes["team.name"] = team_name

    # Merge extra_resource attributes from registry
    if extra_resource:
        attributes.update(extra_resource)

    # Add any additional attributes
    attributes.update(kwargs)

    return Resource.create(attributes)


def setup_meter_provider(
    resource: Resource,
    endpoint: str = "http://localhost:4318/v1/metrics",
    export_interval_ms: int = 5000,
) -> MeterProvider:
    """Set up and configure MeterProvider for metrics collection.

    Args:
        resource: OpenTelemetry Resource with metadata
        endpoint: OTLP HTTP endpoint for metrics
        export_interval_ms: Interval for periodic metric export

    Returns:
        Configured MeterProvider instance

    Note:
        If a MeterProvider is already set globally, a warning is issued and
        the new provider overwrites it. Creating multiple MCAClient instances
        will overwrite the global provider configuration.
    """
    # Check if meter provider already set
    existing_provider = metrics.get_meter_provider()
    if existing_provider is not None and hasattr(existing_provider, "_sdk_config"):
        warnings.warn(
            "MeterProvider is already set globally. Creating multiple MCAClient "
            "instances will overwrite the global provider. Consider reusing a "
            "single MCAClient instance across your application.",
            ProviderAlreadySetWarning,
            stacklevel=3,
        )

    # Create OTLP metric exporter
    exporter = OTLPMetricExporter(endpoint=endpoint)

    # Create periodic reader with export interval
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=export_interval_ms)

    # Initialize meter provider
    provider = MeterProvider(resource=resource, metric_readers=[reader])

    # Set global meter provider
    metrics.set_meter_provider(provider)

    return provider


def setup_logger_provider(
    resource: Resource,
    endpoint: str = "http://localhost:4318/v1/logs",
    batch_size: int = 512,
) -> LoggerProvider:
    """Set up and configure LoggerProvider for structured logging.

    Args:
        resource: OpenTelemetry Resource with metadata
        endpoint: OTLP HTTP endpoint for logs
        batch_size: Maximum batch size for log export

    Returns:
        Configured LoggerProvider instance

    Note:
        If a LoggerProvider is already set globally, a warning is issued and
        the new provider overwrites it. Creating multiple MCAClient instances
        will overwrite the global provider configuration.
    """
    # Check if logger provider already set
    try:
        existing_provider = get_logger_provider()
        if existing_provider is not None and hasattr(existing_provider, "_resource"):
            warnings.warn(
                "LoggerProvider is already set globally. Creating multiple MCAClient "
                "instances will overwrite the global provider. Consider reusing a "
                "single MCAClient instance across your application.",
                ProviderAlreadySetWarning,
                stacklevel=3,
            )
    except Exception:
        # get_logger_provider() may not be available in all OpenTelemetry versions
        pass

    # Create OTLP log exporter
    log_exporter = OTLPLogExporter(endpoint=endpoint)

    # Create batch log processor with configured batch size
    log_processor = BatchLogRecordProcessor(log_exporter, max_export_batch_size=batch_size)

    # Initialize logger provider
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(log_processor)

    # Set global logger provider
    set_logger_provider(logger_provider)

    return logger_provider


def setup_tracer_provider(
    resource: Resource,
    endpoint: str = "http://localhost:4318/v1/traces",
    batch_size: int = 512,
) -> TracerProvider:
    """Set up and configure TracerProvider for distributed tracing.

    Args:
        resource: OpenTelemetry Resource with metadata
        endpoint: OTLP HTTP endpoint for traces
        batch_size: Maximum batch size for trace export

    Returns:
        Configured TracerProvider instance

    Note:
        If a TracerProvider is already set globally, a warning is issued and
        the new provider overwrites it. Creating multiple MCAClient instances
        will overwrite the global provider configuration.
    """
    # Check if tracer provider already set
    existing_provider = trace.get_tracer_provider()
    if existing_provider is not None and hasattr(existing_provider, "_resource"):
        warnings.warn(
            "TracerProvider is already set globally. Creating multiple MCAClient "
            "instances will overwrite the global provider. Consider reusing a "
            "single MCAClient instance across your application.",
            ProviderAlreadySetWarning,
            stacklevel=3,
        )

    # Create OTLP trace exporter
    trace_exporter = OTLPSpanExporter(endpoint=endpoint)

    # Create batch span processor with configured batch size
    span_processor = BatchSpanProcessor(trace_exporter, max_export_batch_size=batch_size)

    # Initialize tracer provider
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(span_processor)

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    return tracer_provider


def setup_all_providers(
    service_name: str,
    model_id: Optional[str] = None,
    model_version: str = "0.3.0",
    team_name: Optional[str] = None,
    model_type: str = "internal",
    collector_endpoint: str = "http://localhost:4318",
    metric_export_interval_ms: int = 5000,
    log_batch_size: int = 100,
    trace_batch_size: int = 100,
    extra_resource: Optional[Dict[str, str]] = None,
    **resource_kwargs,
) -> tuple[MeterProvider, LoggerProvider, TracerProvider, Resource]:
    """Set up all OpenTelemetry providers with consistent configuration.

    This is a convenience function that sets up metrics, logs, and traces
    with a single call.

    Args:
        service_name: Name of the service
        model_id: Unique model identifier
        model_version: Model version string
        team_name: Team responsible for the model
        model_type: Type of model (internal, generative, vendor)
        collector_endpoint: Base OTLP collector endpoint (without /v1/metrics suffix)
        metric_export_interval_ms: Interval for metric export in milliseconds
        log_batch_size: Batch size for log export
        trace_batch_size: Batch size for trace export
        extra_resource: Additional resource attributes from registry
        **resource_kwargs: Additional resource attributes

    Returns:
        Tuple of (MeterProvider, LoggerProvider, TracerProvider, Resource)
    """
    # Create resource with model metadata
    resource = create_resource_attributes(
        service_name=service_name,
        model_id=model_id,
        model_version=model_version,
        team_name=team_name,
        model_type=model_type,
        extra_resource=extra_resource,
        **resource_kwargs,
    )

    # Setup providers
    meter_provider = setup_meter_provider(
        resource=resource,
        endpoint=f"{collector_endpoint}/v1/metrics",
        export_interval_ms=metric_export_interval_ms,
    )

    logger_provider = setup_logger_provider(
        resource=resource,
        endpoint=f"{collector_endpoint}/v1/logs",
        batch_size=log_batch_size,
    )

    tracer_provider = setup_tracer_provider(
        resource=resource,
        endpoint=f"{collector_endpoint}/v1/traces",
        batch_size=trace_batch_size,
    )

    return meter_provider, logger_provider, tracer_provider, resource
