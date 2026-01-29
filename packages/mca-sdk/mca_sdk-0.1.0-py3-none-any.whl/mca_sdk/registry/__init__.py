"""Model Registry integration module.

This module provides components for integrating with a centralized
Model Registry service to fetch model configuration at runtime.
"""

from .client import RegistryClient
from .models import ModelConfig, DeploymentConfig
from .telemetry import RegistryTelemetry

__all__ = [
    "RegistryClient",
    "ModelConfig",
    "DeploymentConfig",
    "RegistryTelemetry",
]
