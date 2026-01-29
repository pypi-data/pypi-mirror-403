"""Data models for registry responses.

This module defines dataclasses for model and deployment configurations
retrieved from the Model Registry API.
"""

from dataclasses import dataclass, field
from typing import Dict

# Valid model types (not to be confused with model_category which is "internal" or "vendor")
VALID_MODEL_TYPES = [
    "regression",
    "time-series",
    "classification",
    "generative",
    "agentic",
    "internal",  # Kept for backward compatibility
]


@dataclass
class ModelConfig:
    """Model configuration from registry.

    Contains model metadata, thresholds, and additional resource attributes
    retrieved from the registry.

    Attributes:
        service_name: Name of the service/application
        model_id: Unique model identifier
        model_version: Model version string
        team_name: Team responsible for the model
        model_type: One of "regression", "time-series", "classification", "generative", "agentic", or "internal" (legacy)
        thresholds: Alert thresholds for metrics (e.g., {"latency_warn_ms": 500})
        extra_resource: Additional OpenTelemetry resource attributes

    Example:
        >>> config = ModelConfig(
        ...     service_name="readmission-model",
        ...     model_id="mdl-001",
        ...     model_version="2.0.0",
        ...     team_name="clinical-ai",
        ...     model_type="internal",
        ...     thresholds={"latency_warn_ms": 500, "error_rate_warn": 0.05},
        ...     extra_resource={"deployment.env": "production"}
        ... )
    """

    service_name: str
    model_id: str
    model_version: str
    team_name: str
    model_type: str
    thresholds: Dict[str, float] = field(default_factory=dict)
    extra_resource: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Validate model configuration after initialization."""
        if self.model_type not in VALID_MODEL_TYPES:
            raise ValueError(
                f"model_type must be one of {VALID_MODEL_TYPES}, got '{self.model_type}'"
            )


@dataclass
class DeploymentConfig:
    """Deployment-specific configuration from registry.

    Contains deployment metadata and resource attribute overrides
    for runtime-specific configuration.

    Attributes:
        deployment_id: Unique deployment identifier
        environment: Deployment environment (e.g., "production", "staging")
        region: Geographic region or datacenter
        resource_overrides: Resource attributes specific to this deployment

    Example:
        >>> config = DeploymentConfig(
        ...     deployment_id="dep-prod-001",
        ...     environment="production",
        ...     region="us-east-1",
        ...     resource_overrides={"deployment.zone": "az-1"}
        ... )
    """

    deployment_id: str
    environment: str
    region: str
    resource_overrides: Dict[str, str] = field(default_factory=dict)
