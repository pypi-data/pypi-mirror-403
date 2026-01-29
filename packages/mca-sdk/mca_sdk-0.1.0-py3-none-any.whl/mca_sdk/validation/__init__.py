"""Validation module for MCA SDK.

This module provides validation for metric names and resource attributes
to ensure consistency across different model types.
"""

from .schema import (
    MetricNamingConvention,
    validate_metric_name,
    METRIC_PATTERNS,
    VALID_UNITS,
    VALID_PREFIXES,
)
from .attributes import (
    validate_resource_attributes,
    get_required_attributes,
    get_recommended_attributes,
    REQUIRED_ATTRIBUTES,
    RECOMMENDED_ATTRIBUTES,
)

__all__ = [
    # Schema validation
    "MetricNamingConvention",
    "validate_metric_name",
    "METRIC_PATTERNS",
    "VALID_UNITS",
    "VALID_PREFIXES",
    # Attribute validation
    "validate_resource_attributes",
    "get_required_attributes",
    "get_recommended_attributes",
    "REQUIRED_ATTRIBUTES",
    "RECOMMENDED_ATTRIBUTES",
]
