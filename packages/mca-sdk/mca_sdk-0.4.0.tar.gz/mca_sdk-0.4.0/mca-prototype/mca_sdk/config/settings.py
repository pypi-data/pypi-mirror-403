"""Configuration settings for MCA SDK.

This module provides the MCAConfig dataclass for managing SDK configuration
with support for multiple configuration sources.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional

from ..utils.exceptions import ConfigurationError


# Security warning category
class SecurityWarning(UserWarning):
    """Warning category for security-related issues."""


@dataclass
class MCAConfig:
    """Configuration for MCA SDK.

    Supports loading from multiple sources with precedence:
    kwargs > environment variables > YAML file > defaults

    Attributes:
        service_name: Name of the service (required)
        model_id: Unique model identifier
        model_version: Model version string
        team_name: Team responsible for the model
        model_type: Type of model (internal, generative, vendor)

        collector_endpoint: OTLP collector endpoint
        collector_timeout: Timeout for collector requests in seconds

        buffering_enabled: Whether to enable buffering
        max_queue_size: Maximum number of items in queue
        retry_attempts: Number of retry attempts
        persist_queue: Whether to persist queue to disk
        persist_path: Path for queue persistence

        strict_validation: Whether to enforce strict validation
        metric_export_interval_ms: Interval for metric export in milliseconds
        log_batch_size: Batch size for log export
        trace_batch_size: Batch size for trace export

        registry_url: URL of the model registry service
        registry_token: Bearer token for registry authentication
        refresh_interval_secs: Interval for refreshing config from registry
        prefer_registry: Whether registry values override local config
        deployment_id: Optional deployment identifier for registry lookup
    """

    # Model metadata (required)
    service_name: str

    # Model metadata (optional)
    model_id: Optional[str] = None
    model_version: str = "0.3.0"
    team_name: Optional[str] = None
    model_type: str = "internal"  # internal, generative, vendor
    model_category: str = "internal"  # internal or vendor (Epic 2 taxonomy)

    # Collector settings
    # SECURITY: Default to HTTP for localhost only
    # Production deployments should explicitly set HTTPS endpoint via MCA_COLLECTOR_ENDPOINT
    collector_endpoint: str = "http://localhost:4318"
    collector_timeout: int = 10

    # Buffering
    buffering_enabled: bool = False  # Disabled by default for backward compatibility
    max_queue_size: int = 1000
    retry_attempts: int = 3
    persist_queue: bool = False
    # SECURITY: Use user-specific secure directory instead of world-readable /tmp
    # Default path uses user's home directory with restricted permissions
    persist_path: str = field(default_factory=lambda: os.path.expanduser("~/.mca_sdk/queue.pkl"))

    # Validation
    strict_validation: bool = True

    # Debug mode
    debug_mode: bool = False  # Disabled by default for production

    # Export intervals
    metric_export_interval_ms: int = 5000
    log_batch_size: int = 512  # Maximum batch size for log export
    trace_batch_size: int = 512  # Maximum batch size for trace export

    # Optional vendor-specific fields
    vendor_name: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None

    # Registry integration
    registry_url: Optional[str] = None
    registry_token: Optional[str] = None  # SECURITY: From env only, never logged
    refresh_interval_secs: int = 600  # 10 minutes
    prefer_registry: bool = True  # Registry > local when True
    deployment_id: Optional[str] = None  # Optional deployment indirection

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.service_name:
            raise ConfigurationError(
                "service_name is required. "
                "Set via: MCA_SERVICE_NAME environment variable, YAML config file, or pass as kwarg to MCAConfig()"
            )

        if self.model_type not in ["internal", "generative", "vendor"]:
            raise ConfigurationError(
                f"model_type must be one of: internal, generative, vendor. Got: {self.model_type}"
            )

        if self.model_category not in ["internal", "vendor"]:
            raise ConfigurationError(
                f"model_category must be one of: internal, vendor. Got: {self.model_category}"
            )

        # Validate collector endpoint URL
        if self.collector_endpoint:
            if not (
                self.collector_endpoint.startswith("http://")
                or self.collector_endpoint.startswith("https://")
            ):
                raise ConfigurationError(
                    f"collector_endpoint must start with http:// or https://. Got: {self.collector_endpoint}"
                )

            # Warn if using HTTP for non-localhost endpoints
            if self.collector_endpoint.startswith("http://"):
                from urllib.parse import urlparse

                parsed = urlparse(self.collector_endpoint)
                hostname = parsed.hostname or ""
                # Only allow HTTP for actual localhost (not domains containing "localhost")
                if hostname not in ("localhost", "127.0.0.1", "::1"):
                    import warnings

                    warnings.warn(
                        f"Using HTTP for non-localhost endpoint: {self.collector_endpoint}. "
                        "This transmits telemetry unencrypted. Use HTTPS in production.",
                        SecurityWarning,
                    )

        # Validate registry URL if configured
        if self.registry_url:
            # Check for valid URL format
            if not (
                self.registry_url.startswith("http://") or self.registry_url.startswith("https://")
            ):
                # Check if it looks like a URL at all (has dot or colon)
                if "." not in self.registry_url and ":" not in self.registry_url:
                    raise ConfigurationError(
                        f"Invalid registry_url format: {self.registry_url}. "
                        "Expected a valid URL with http:// or https:// protocol."
                    )
                else:
                    raise ConfigurationError(
                        f"registry_url must use http:// or https:// protocol. Got: {self.registry_url}"
                    )

            # SECURITY: Warn if using HTTP for non-localhost registry endpoints
            if self.registry_url.startswith("http://"):
                from urllib.parse import urlparse

                parsed = urlparse(self.registry_url)
                hostname = parsed.hostname or ""
                # Only allow HTTP for actual localhost (not domains containing "localhost")
                if hostname not in ("localhost", "127.0.0.1", "::1"):
                    import warnings

                    warnings.warn(
                        f"Using HTTP for non-localhost registry endpoint: {self.registry_url}. "
                        "This transmits registry requests unencrypted. Use HTTPS in production.",
                        SecurityWarning,
                    )

    @classmethod
    def from_env(cls, prefix: str = "MCA_") -> "MCAConfig":
        """Load configuration from environment variables.

        Environment variables should be prefixed with MCA_ by default.
        Example: MCA_SERVICE_NAME, MCA_MODEL_ID, etc.

        Args:
            prefix: Prefix for environment variables (default: "MCA_")

        Returns:
            MCAConfig instance populated from environment variables
        """

        def get_env(key: str, default=None):
            """Get environment variable with prefix."""
            return os.getenv(f"{prefix}{key}", default)

        def get_env_bool(key: str, default: bool) -> bool:
            """Get boolean environment variable."""
            value = get_env(key)
            if value is None:
                return default
            return value.lower() in ("true", "1", "yes")

        def get_env_int(key: str, default: int) -> int:
            """Get integer environment variable."""
            value = get_env(key)
            if value is None:
                return default
            try:
                return int(value)
            except ValueError:
                raise ConfigurationError(f"Invalid integer value for {prefix}{key}: {value}")

        def get_env_list(key: str, default: List[str]) -> List[str]:
            """Get list environment variable (comma-separated)."""
            value = get_env(key)
            if value is None:
                return default
            return [item.strip() for item in value.split(",")]

        return cls(
            service_name=get_env("SERVICE_NAME", ""),
            model_id=get_env("MODEL_ID"),
            model_version=get_env("MODEL_VERSION", "0.3.0"),
            team_name=get_env("TEAM_NAME"),
            model_type=get_env("MODEL_TYPE", "internal"),
            model_category=get_env("MODEL_CATEGORY", "internal"),
            collector_endpoint=get_env("COLLECTOR_ENDPOINT", "http://localhost:4318"),
            collector_timeout=get_env_int("COLLECTOR_TIMEOUT", 10),
            buffering_enabled=get_env_bool("BUFFERING_ENABLED", False),
            max_queue_size=get_env_int("MAX_QUEUE_SIZE", 1000),
            retry_attempts=get_env_int("RETRY_ATTEMPTS", 3),
            persist_queue=get_env_bool("PERSIST_QUEUE", False),
            # SECURITY: Use secure user-specific directory instead of world-readable /tmp
            persist_path=get_env("PERSIST_PATH", os.path.expanduser("~/.mca_sdk/queue.pkl")),
            strict_validation=get_env_bool("STRICT_VALIDATION", True),
            debug_mode=get_env_bool("DEBUG", False),
            metric_export_interval_ms=get_env_int("METRIC_EXPORT_INTERVAL_MS", 5000),
            # Match dataclass defaults for consistency
            log_batch_size=get_env_int("LOG_BATCH_SIZE", 512),
            trace_batch_size=get_env_int("TRACE_BATCH_SIZE", 512),
            vendor_name=get_env("VENDOR_NAME"),
            llm_provider=get_env("LLM_PROVIDER"),
            llm_model=get_env("LLM_MODEL"),
            registry_url=get_env("REGISTRY_URL"),
            registry_token=get_env("REGISTRY_TOKEN"),
            refresh_interval_secs=get_env_int("REFRESH_SECS", 600),
            prefer_registry=get_env_bool("PREFER_REGISTRY", True),
            deployment_id=get_env("DEPLOYMENT_ID"),
        )

    @classmethod
    def from_file(cls, path: str) -> "MCAConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            MCAConfig instance populated from file

        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        try:
            import yaml
        except ImportError:
            raise ConfigurationError(
                "pyyaml is required for loading config from file. "
                "Install with: pip install pyyaml"
            )

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")

        if not isinstance(data, dict):
            raise ConfigurationError("Configuration file must contain a YAML dictionary")

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "MCAConfig":
        """Load configuration from dictionary.

        Args:
            data: Dictionary with configuration values

        Returns:
            MCAConfig instance populated from dictionary
        """
        # Only pass keys that are valid MCAConfig attributes
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    @classmethod
    def load(
        cls, config_file: Optional[str] = None, env_prefix: str = "MCA_", **kwargs
    ) -> "MCAConfig":
        """Load configuration from multiple sources with precedence chain.

        Precedence order (highest to lowest):
        1. kwargs/constructor arguments
        2. Environment variables (MCA_* prefix by default)
        3. YAML configuration file
        4. Default values

        Args:
            config_file: Optional path to YAML configuration file. If not provided,
                        checks MCA_CONFIG_FILE environment variable, then tries standard locations.
            env_prefix: Prefix for environment variables (default: "MCA_")
            **kwargs: Configuration parameters to override all other sources

        Returns:
            MCAConfig instance with merged configuration from all sources

        Security:
            registry_token MUST be provided via environment variable (MCA_REGISTRY_TOKEN) only.
            Passing registry_token via kwargs or YAML configuration files will raise
            ConfigurationError to prevent accidental token exposure in code, logs, or
            version control.

        Raises:
            ConfigurationError: If required fields are missing or invalid
        """
        config_dict = {}

        # Helper function to extract env value with type conversion
        def get_env_value(key: str):
            """Get raw environment variable value."""
            # Convert key to uppercase to match from_env() behavior and standard env var conventions
            return os.getenv(f"{env_prefix}{key.upper()}")

        def get_env_bool(key: str) -> Optional[bool]:
            """Get boolean environment variable."""
            value = get_env_value(key)
            if value is None:
                return None
            return value.lower() in ("true", "1", "yes")

        def get_env_int(key: str) -> Optional[int]:
            """Get integer environment variable."""
            value = get_env_value(key)
            if value is None:
                return None
            try:
                return int(value)
            except ValueError:
                raise ConfigurationError(f"Invalid integer value for {env_prefix}{key}: {value}")

        # Step 2: Load from YAML file if available
        yaml_file = config_file or os.getenv(f"{env_prefix}CONFIG_FILE")
        if yaml_file and os.path.exists(yaml_file):
            try:
                yaml_config = cls.from_file(yaml_file)
                # Extract all attributes from the YAML config
                for field_name in cls.__dataclass_fields__:
                    config_dict[field_name] = getattr(yaml_config, field_name)

                # SECURITY: Check if registry_token was loaded from YAML
                if config_dict.get("registry_token") is not None:
                    raise ConfigurationError(
                        "Security violation: registry_token must be provided via environment variable "
                        "(MCA_REGISTRY_TOKEN) only, not YAML configuration files. "
                        "This prevents accidental token exposure in version control."
                    )
            except ConfigurationError as e:
                raise ConfigurationError(f"Failed to load configuration from {yaml_file}: {e}")

        # Step 3: Override with environment variables (extract raw values without validation yet)
        # Get raw env values and apply type conversion
        for field_name in cls.__dataclass_fields__:
            cls.__dataclass_fields__[field_name]
            env_value = get_env_value(field_name)

            if env_value is not None:
                # Type conversion based on field type
                if field_name in [
                    "buffering_enabled",
                    "persist_queue",
                    "strict_validation",
                    "prefer_registry",
                    "debug_mode",
                ]:
                    config_dict[field_name] = get_env_bool(field_name)
                elif field_name in [
                    "collector_timeout",
                    "max_queue_size",
                    "retry_attempts",
                    "metric_export_interval_ms",
                    "log_batch_size",
                    "trace_batch_size",
                    "refresh_interval_secs",
                ]:
                    config_dict[field_name] = get_env_int(field_name)
                else:
                    # String fields
                    config_dict[field_name] = env_value

        # Step 4: Override with kwargs (highest precedence)
        # SECURITY: Never accept registry_token via kwargs
        if "registry_token" in kwargs:
            raise ConfigurationError(
                "Security violation: registry_token must be provided via environment variable "
                "(MCA_REGISTRY_TOKEN) only, not kwargs. This prevents accidental token exposure in code."
            )
        config_dict.update(kwargs)

        # Step 5: Ensure service_name is present (even if empty) so validation can catch it
        if "service_name" not in config_dict:
            config_dict["service_name"] = ""

        # Step 6: Create final config and validate
        return cls(**config_dict)
