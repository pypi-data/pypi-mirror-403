"""Custom exceptions for MCA SDK.

This module defines exception classes used throughout the SDK for
error handling and validation failures.
"""


class MCASDKError(Exception):
    """Base exception class for all MCA SDK errors.

    Use this to catch any SDK-related exception.

    Examples:
        - Catching all SDK errors:
          try:
              client = MCAClient(...)
          except MCASDKError as e:
              print(f"SDK error: {e}")
    """


class ValidationError(MCASDKError):
    """Raised when validation fails.

    Examples:
        - Metric name doesn't follow naming conventions
        - Required resource attributes are missing
        - Invalid configuration values
    """


class BufferingError(MCASDKError):
    """Raised when buffering operations fail.

    Examples:
        - Queue is full and cannot accept more items
        - Disk persistence failure
        - Background worker thread failure
    """


class ConfigurationError(MCASDKError):
    """Raised when configuration is invalid or incomplete.

    Examples:
        - Missing required configuration fields
        - Invalid configuration file format
        - Conflicting configuration values
    """


class RegistryError(MCASDKError):
    """Base exception for registry operations.

    Examples:
        - Registry communication failures
        - Invalid registry responses
        - Registry configuration errors
    """


class RegistryConnectionError(RegistryError):
    """Raised when unable to connect to the registry.

    Examples:
        - Network timeout
        - DNS resolution failure
        - Connection refused
    """


class RegistryConfigNotFoundError(RegistryError):
    """Raised when model configuration not found in registry.

    Examples:
        - Model ID does not exist
        - Deployment ID not found
        - Version not available
    """


class RegistryAuthError(RegistryError):
    """Raised when registry authentication fails.

    Examples:
        - Invalid or expired token
        - Missing authentication credentials
        - Insufficient permissions
    """
