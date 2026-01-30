"""MCA SDK - Model Collector Agent SDK for OpenTelemetry instrumentation.

This SDK simplifies model instrumentation by providing schema validation,
buffering, and resilience features while reducing boilerplate code from
170+ lines to ~10 lines.

Example:
    >>> from mca_sdk import MCAClient
    >>>
    >>> client = MCAClient(
    ...     service_name="readmission-model",
    ...     model_id="mdl-001",
    ...     team_name="clinical-ai"
    ... )
    >>>
    >>> def predict(data):
    ...     with client.trace("model.predict"):
    ...         result = model.predict(data)
    ...         client.record_prediction(data, result, latency=0.15)
    ...         return result
    >>>
    >>> client.shutdown()
"""

__version__ = "0.4.0"

from .core import MCAClient
from .config import MCAConfig
from .registry import RegistryClient, ModelConfig, DeploymentConfig
from .utils.exceptions import (
    MCASDKError,
    ConfigurationError,
    RegistryError,
    RegistryConnectionError,
    RegistryConfigNotFoundError,
    RegistryAuthError,
    ValidationError,
    BufferingError,
)

__all__ = [
    "MCAClient",
    "MCAConfig",
    "RegistryClient",
    "ModelConfig",
    "DeploymentConfig",
    "MCASDKError",
    "ConfigurationError",
    "RegistryError",
    "RegistryConnectionError",
    "RegistryConfigNotFoundError",
    "RegistryAuthError",
    "ValidationError",
    "BufferingError",
    "__version__",
]
