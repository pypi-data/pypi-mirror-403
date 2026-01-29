"""Metric naming convention validation for MCA SDK.

This module enforces metric naming conventions to ensure consistency
across all model types (internal, generative, vendor).

Naming conventions:
- Internal models: model.*_total, model.*_seconds, model.*_ratio
- GenAI models: genai.*_total, genai.*_seconds, genai.*_ratio
- Vendor models: vendor.*_total, vendor.*_seconds, vendor.*_ratio
"""

import re
from typing import Set

from ..utils.exceptions import ValidationError


# Valid metric name patterns by model type
METRIC_PATTERNS = {
    "internal": [
        re.compile(r"^model\.[a-z_]+_total$"),  # Counters: model.predictions_total
        re.compile(r"^model\.[a-z_]+_seconds$"),  # Latency: model.latency_seconds
        re.compile(r"^model\.[a-z_]+_ratio$"),  # Ratios: model.accuracy_ratio
        re.compile(r"^model\.[a-z_]+_milliseconds$"),  # Milliseconds: model.inference_milliseconds
        re.compile(r"^model\.[a-z_]+_count$"),  # Counts: model.error_count
    ],
    "generative": [
        re.compile(r"^genai\.[a-z_]+_total$"),  # Counters: genai.requests_total
        re.compile(r"^genai\.[a-z_]+_seconds$"),  # Latency: genai.latency_seconds
        re.compile(r"^genai\.[a-z_]+_ratio$"),  # Ratios: genai.success_ratio
        re.compile(r"^genai\.[a-z_]+_count$"),  # Counts: genai.token_count
        re.compile(r"^genai\.[a-z_]+_dollars$"),  # Cost: genai.cost_dollars
    ],
    "vendor": [
        re.compile(r"^vendor\.[a-z_]+_total$"),  # Counters: vendor.predictions_total
        re.compile(r"^vendor\.[a-z_]+_seconds$"),  # Latency: vendor.latency_seconds
        re.compile(r"^vendor\.[a-z_]+_ratio$"),  # Ratios: vendor.accuracy_ratio
        re.compile(r"^vendor\.[a-z_]+_count$"),  # Counts: vendor.error_count
    ],
}

# Valid metric units (suffixes)
VALID_UNITS: Set[str] = {
    "total",  # Counters (monotonically increasing)
    "seconds",  # Time duration in seconds
    "milliseconds",  # Time duration in milliseconds
    "ratio",  # Ratios and percentages (0.0-1.0)
    "count",  # Counts (may decrease)
    "dollars",  # Cost in dollars (GenAI only)
}

# Valid metric prefixes by model type
VALID_PREFIXES = {
    "internal": "model",
    "generative": "genai",
    "vendor": "vendor",
}


class MetricNamingConvention:
    """Validator for metric naming conventions.

    Enforces consistent metric naming across different model types to ensure
    metrics can be properly categorized and queried in monitoring systems.

    Examples:
        >>> validator = MetricNamingConvention(model_type="internal")
        >>> validator.validate("model.predictions_total")  # OK
        >>> validator.validate("custom_metric")  # Raises ValidationError

        >>> validator = MetricNamingConvention(model_type="internal", strict=False)
        >>> validator.validate("custom_metric")  # OK (non-strict mode)
    """

    def __init__(self, model_type: str = "internal", strict: bool = True):
        """Initialize metric naming validator.

        Args:
            model_type: Type of model (internal, generative, vendor)
            strict: If True, enforce naming conventions. If False, allow any name.

        Raises:
            ValidationError: If model_type is not recognized
        """
        if model_type not in VALID_PREFIXES:
            raise ValidationError(
                f"Invalid model_type: {model_type}. "
                f"Must be one of: {', '.join(VALID_PREFIXES.keys())}"
            )

        self.model_type = model_type
        self.strict = strict
        self.patterns = METRIC_PATTERNS.get(model_type, [])
        self.expected_prefix = VALID_PREFIXES[model_type]

    def validate(self, metric_name: str) -> None:
        """Validate a metric name against conventions.

        Args:
            metric_name: The metric name to validate

        Raises:
            ValidationError: If metric name doesn't follow conventions (strict mode only)
        """
        # SECURITY: Input validation to prevent DoS/ReDoS attacks
        if not isinstance(metric_name, str):
            raise ValidationError(f"Metric name must be a string, got {type(metric_name)}")

        # SECURITY: Limit metric name length to prevent DoS
        MAX_METRIC_NAME_LENGTH = 256
        if len(metric_name) > MAX_METRIC_NAME_LENGTH:
            raise ValidationError(
                f"Metric name exceeds maximum length of {MAX_METRIC_NAME_LENGTH} characters. "
                f"Got {len(metric_name)} characters."
            )

        # SECURITY: Sanitize input - only allow alphanumeric, dots, underscores
        # This prevents regex injection and reduces ReDoS risk
        if metric_name and not all(c.isalnum() or c in "._" for c in metric_name):
            raise ValidationError(
                "Metric name contains invalid characters. "
                "Only alphanumeric characters, dots, and underscores are allowed."
            )

        # Non-strict mode: allow any name (after security checks)
        if not self.strict:
            return

        # Check if name matches any pattern for this model type
        for pattern in self.patterns:
            if pattern.match(metric_name):
                return  # Valid!

        # If we get here, name doesn't match any pattern
        self._raise_validation_error(metric_name)

    def _raise_validation_error(self, metric_name: str) -> None:
        """Raise a detailed ValidationError with suggestions.

        Args:
            metric_name: The invalid metric name
        """
        # Provide helpful error message with examples
        examples = self._get_examples()

        error_msg = (
            f"Invalid metric name: '{metric_name}'\n"
            f"\n"
            f"For model_type='{self.model_type}', metric names must follow these patterns:\n"
            f"  - {self.expected_prefix}.*_total (counters)\n"
            f"  - {self.expected_prefix}.*_seconds (latency)\n"
            f"  - {self.expected_prefix}.*_ratio (ratios)\n"
            f"  - {self.expected_prefix}.*_count (counts)\n"
        )

        if self.model_type == "generative":
            error_msg += f"  - {self.expected_prefix}.*_dollars (cost)\n"

        error_msg += "\nExamples:\n"
        for example in examples:
            error_msg += f"  - {example}\n"

        error_msg += "\nTo disable validation, set strict_validation=False in MCAConfig."

        raise ValidationError(error_msg)

    def _get_examples(self) -> list:
        """Get example metric names for this model type."""
        if self.model_type == "internal":
            return [
                "model.predictions_total",
                "model.latency_seconds",
                "model.accuracy_ratio",
                "model.error_count",
            ]
        elif self.model_type == "generative":
            return [
                "genai.requests_total",
                "genai.latency_seconds",
                "genai.token_count",
                "genai.cost_dollars",
            ]
        else:  # vendor
            return [
                "vendor.predictions_total",
                "vendor.latency_seconds",
                "vendor.accuracy_ratio",
            ]


def validate_metric_name(
    metric_name: str, model_type: str = "internal", strict: bool = True
) -> None:
    """Convenience function to validate a metric name.

    Args:
        metric_name: The metric name to validate
        model_type: Type of model (internal, generative, vendor)
        strict: If True, enforce naming conventions

    Raises:
        ValidationError: If metric name doesn't follow conventions (strict mode only)

    Example:
        >>> validate_metric_name("model.predictions_total", "internal")  # OK
        >>> validate_metric_name("custom_metric", "internal")  # Raises ValidationError
    """
    validator = MetricNamingConvention(model_type=model_type, strict=strict)
    validator.validate(metric_name)
