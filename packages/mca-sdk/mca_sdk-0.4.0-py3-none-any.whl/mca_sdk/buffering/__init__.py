"""Buffering and resilience module for MCA SDK.

This module provides telemetry queueing and retry logic to ensure
reliability when the collector is temporarily unreachable.
"""

from .queue import TelemetryQueue
from .retry import RetryPolicy

__all__ = [
    "TelemetryQueue",
    "RetryPolicy",
]
