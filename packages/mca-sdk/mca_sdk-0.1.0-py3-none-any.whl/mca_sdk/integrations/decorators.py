"""Instrumentation decorators for MCA SDK.

This module provides decorators for automatic model instrumentation,
making it easy to add telemetry to prediction functions.
"""

import functools
import time
from typing import Callable, Optional, Any

from ..core.client import MCAClient


def instrument_model(
    client: MCAClient,
    metric_name: Optional[str] = None,
    capture_input: bool = False,
    capture_output: bool = False,
):
    """Decorator for automatic model instrumentation.

    Wraps a prediction function to automatically record metrics including
    latency, call counts, and optionally input/output data.

    Args:
        client: MCAClient instance for recording telemetry
        metric_name: Custom metric name prefix (default: function name)
        capture_input: Whether to capture input data (default: False)
        capture_output: Whether to capture output data (default: False)

    Returns:
        Decorated function with automatic instrumentation

    Examples:
        Basic usage:
        >>> client = MCAClient(...)
        >>> @instrument_model(client)
        ... def predict(input_data):
        ...     return model.predict(input_data)

        With custom metric name:
        >>> @instrument_model(client, metric_name="readmission_prediction")
        ... def predict_readmission(patient_data):
        ...     return model.predict(patient_data)

        Capturing input/output:
        >>> @instrument_model(client, capture_input=True, capture_output=True)
        ... def predict(input_data):
        ...     return model.predict(input_data)
    """

    def decorator(func: Callable) -> Callable:
        # Use function name if metric_name not provided
        name = metric_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Start timing
            start_time = time.time()

            # Create trace span
            with client.trace(f"{name}.predict") as span:
                try:
                    # Call the original function
                    result = func(*args, **kwargs)

                    # Calculate latency
                    latency = time.time() - start_time

                    # Prepare input/output for recording
                    input_data = None
                    output_data = None

                    if capture_input and args:
                        input_data = args[0]  # First positional arg
                    if capture_output:
                        output_data = result

                    # Record prediction
                    client.record_prediction(
                        input_data=input_data or {}, output=output_data or {}, latency=latency
                    )

                    # Add span attributes
                    span.set_attribute(f"{name}.latency_seconds", latency)
                    span.set_attribute(f"{name}.status", "success")

                    return result

                except Exception as e:
                    # Calculate latency even on error
                    latency = time.time() - start_time

                    # Record error
                    span.set_attribute(f"{name}.status", "error")
                    span.set_attribute(f"{name}.error", str(e))

                    # Record error metric
                    client.record_metric(
                        "model.errors_total", 1, function=name, error_type=type(e).__name__
                    )

                    # Re-raise the exception
                    raise

        return wrapper

    return decorator


def instrument_async_model(
    client: MCAClient,
    metric_name: Optional[str] = None,
    capture_input: bool = False,
    capture_output: bool = False,
):
    """Decorator for automatic async model instrumentation.

    Wraps an async prediction function to automatically record metrics.

    Args:
        client: MCAClient instance for recording telemetry
        metric_name: Custom metric name prefix (default: function name)
        capture_input: Whether to capture input data (default: False)
        capture_output: Whether to capture output data (default: False)

    Returns:
        Decorated async function with automatic instrumentation

    Example:
        >>> @instrument_async_model(client)
        ... async def predict_async(input_data):
        ...     result = await model.predict_async(input_data)
        ...     return result
    """

    def decorator(func: Callable) -> Callable:
        # Use function name if metric_name not provided
        name = metric_name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Start timing
            start_time = time.time()

            # Create trace span
            with client.trace(f"{name}.predict") as span:
                try:
                    # Call the original async function
                    result = await func(*args, **kwargs)

                    # Calculate latency
                    latency = time.time() - start_time

                    # Prepare input/output for recording
                    input_data = None
                    output_data = None

                    if capture_input and args:
                        input_data = args[0]
                    if capture_output:
                        output_data = result

                    # Record prediction
                    client.record_prediction(
                        input_data=input_data or {}, output=output_data or {}, latency=latency
                    )

                    # Add span attributes
                    span.set_attribute(f"{name}.latency_seconds", latency)
                    span.set_attribute(f"{name}.status", "success")

                    return result

                except Exception as e:
                    # Calculate latency even on error
                    latency = time.time() - start_time

                    # Record error
                    span.set_attribute(f"{name}.status", "error")
                    span.set_attribute(f"{name}.error", str(e))

                    # Record error metric
                    client.record_metric(
                        "model.errors_total", 1, function=name, error_type=type(e).__name__
                    )

                    # Re-raise the exception
                    raise

        return wrapper

    return decorator


def track_batch_prediction(client: MCAClient, batch_size_metric: str = "model.batch_size_count"):
    """Decorator for tracking batch prediction metrics.

    Automatically tracks batch size and per-item latency for batch
    prediction functions.

    Args:
        client: MCAClient instance
        batch_size_metric: Metric name for batch size (default: "model.batch_size_count")

    Returns:
        Decorated function with batch tracking

    Example:
        >>> @track_batch_prediction(client)
        ... def predict_batch(inputs):
        ...     return [model.predict(x) for x in inputs]
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Start timing
            start_time = time.time()

            # Get batch from first argument
            batch = args[0] if args else []
            batch_size = len(batch) if hasattr(batch, "__len__") else 0

            try:
                # Call the original function
                result = func(*args, **kwargs)

                # Calculate metrics
                total_latency = time.time() - start_time
                per_item_latency = total_latency / batch_size if batch_size > 0 else 0

                # Record batch size
                client.record_metric(batch_size_metric, batch_size)

                # Record total latency
                client.record_metric(
                    "model.batch_latency_seconds", total_latency, batch_size=str(batch_size)
                )

                # Record per-item latency
                client.record_metric(
                    "model.per_item_latency_seconds", per_item_latency, batch_size=str(batch_size)
                )

                return result

            except Exception as e:
                # Record batch error
                client.record_metric(
                    "model.batch_errors_total",
                    1,
                    error_type=type(e).__name__,
                    batch_size=str(batch_size),
                )
                raise

        return wrapper

    return decorator
