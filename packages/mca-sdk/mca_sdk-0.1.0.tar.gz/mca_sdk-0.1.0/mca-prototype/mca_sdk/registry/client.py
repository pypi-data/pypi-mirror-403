"""Registry client for fetching model and deployment configurations.

This module provides the RegistryClient for communicating with the
Model Registry API to retrieve configuration at runtime.
"""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlencode

import requests

from ..buffering.retry import RetryPolicy
from ..utils.exceptions import (
    RegistryError,
    RegistryConnectionError,
    RegistryConfigNotFoundError,
    RegistryAuthError,
)
from .models import ModelConfig, DeploymentConfig
from .telemetry import RegistryTelemetry

logger = logging.getLogger(__name__)

# Constants for default configuration values
DEFAULT_CACHE_TTL_SECS = 600  # 10 minutes
DEFAULT_TIMEOUT_SECS = 5.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 10.0


@dataclass
class CacheEntry:
    """Cache entry with expiration time."""

    value: Any  # Can be ModelConfig or DeploymentConfig
    expires_at: float


class RegistryClient:
    """Client for fetching configurations from the Model Registry.

    Provides methods to fetch model and deployment configurations from
    a central registry service with automatic retry, caching, and security.

    Features:
        - Automatic retry with exponential backoff
        - In-memory cache with TTL
        - HTTPS enforcement for non-localhost endpoints
        - Bearer token authentication
        - Request timeout protection

    Example:
        >>> client = RegistryClient(
        ...     url="https://registry.example.com",
        ...     token="secret-token",
        ...     timeout=5.0,
        ...     cache_ttl_secs=600
        ... )
        >>> config = client.fetch_model_config("mdl-001", version="2.0.0")
    """

    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECS,
        cache_ttl_secs: int = DEFAULT_CACHE_TTL_SECS,
        meter=None,
    ):
        """Initialize registry client.

        Args:
            url: Base URL of the registry service
            token: Bearer token for authentication (optional)
            timeout: Request timeout in seconds (default: 5.0)
            cache_ttl_secs: Cache TTL in seconds (default: 600 = 10 minutes)
            meter: OpenTelemetry Meter for telemetry (optional)

        Raises:
            RegistryError: If URL validation fails
        """
        self._validate_url(url)
        self._url = url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_lock = threading.RLock()  # Thread-safe cache access
        self._cache_ttl = cache_ttl_secs
        self._retry_policy = RetryPolicy(
            max_attempts=DEFAULT_MAX_RETRIES,
            base_delay=DEFAULT_BASE_DELAY,
            max_delay=DEFAULT_MAX_DELAY
        )
        self._session = requests.Session()

        # Initialize telemetry if meter provided
        self._telemetry = RegistryTelemetry(meter) if meter else None

        # Set up authentication header if token provided
        if self._token:
            self._session.headers.update({"Authorization": f"Bearer {self._token}"})

    def _validate_url(self, url: str) -> None:
        """Validate registry URL for security.

        Args:
            url: URL to validate

        Raises:
            RegistryError: If URL is invalid or insecure
        """
        if not url.startswith(("http://", "https://")):
            raise RegistryError(f"Registry URL must start with http:// or https://, got: {url}")

        # SECURITY: Require HTTPS for non-localhost
        if url.startswith("http://"):
            if "localhost" not in url and "127.0.0.1" not in url:
                raise RegistryError(
                    "Registry URL must use HTTPS for non-localhost endpoints. " f"Got: {url}"
                )
            logger.warning(
                f"Using HTTP for registry URL: {url}. "
                "This should only be used for local development."
            )

    def fetch_model_config(self, model_id: str, version: Optional[str] = None) -> ModelConfig:
        """Fetch model configuration from registry.

        Args:
            model_id: Unique model identifier
            version: Model version (optional, defaults to latest)

        Returns:
            ModelConfig with fetched configuration

        Raises:
            RegistryConnectionError: If unable to connect to registry
            RegistryConfigNotFoundError: If model not found
            RegistryAuthError: If authentication fails
            RegistryError: For other registry errors
        """
        cache_key = f"model:{model_id}:{version or 'latest'}"

        # Check cache first
        cached = self._get_cached(cache_key)
        if cached:
            logger.debug(f"Cache hit for {cache_key}")
            return cached

        # Fetch from registry with retry
        logger.info(f"Fetching model config for {model_id} version {version or 'latest'}")
        start_time = time.time()

        # First try without retry to catch non-retryable errors immediately
        try:
            config = self._fetch_model_config_internal(model_id, version)
            self._set_cache(cache_key, config)

            # Record telemetry success
            if self._telemetry:
                latency = time.time() - start_time
                self._telemetry.record_success(latency)

            return config
        except (RegistryAuthError, RegistryConfigNotFoundError) as e:
            # Don't retry permanent failures (401/403/404) - fail immediately
            if self._telemetry:
                self._telemetry.record_error(type(e).__name__)
            raise
        except (RegistryConnectionError, RegistryError) as e:
            # Retry transient failures
            logger.warning(f"Retrying model config fetch for {model_id} due to: {e}")

            def _fetch_with_retry():
                return self._fetch_model_config_internal(model_id, version)

            try:
                config = self._retry_policy.execute(_fetch_with_retry)
                self._set_cache(cache_key, config)

                # Record telemetry success
                if self._telemetry:
                    latency = time.time() - start_time
                    self._telemetry.record_success(latency)

                return config
            except Exception as retry_e:
                if self._telemetry:
                    self._telemetry.record_error(type(retry_e).__name__)
                logger.error(f"Failed to fetch model config for {model_id} after retries: {retry_e}")
                raise

    def _fetch_model_config_internal(self, model_id: str, version: Optional[str]) -> ModelConfig:
        """Internal method to fetch model config (called by retry policy).

        Args:
            model_id: Model identifier
            version: Model version (optional)

        Returns:
            ModelConfig from registry response

        Raises:
            RegistryConnectionError: On connection failures
            RegistryConfigNotFoundError: If model not found
            RegistryAuthError: On auth failures
            RegistryError: On other errors
        """
        # Build URL
        endpoint = f"/models/{model_id}"
        params = {}
        if version:
            params["version"] = version

        url = urljoin(self._url + "/", endpoint.lstrip("/"))
        if params:
            url = f"{url}?{urlencode(params)}"

        # Make request
        try:
            # SECURITY: Don't log full URL (may contain query params)
            logger.debug(f"GET {endpoint}")
            response = self._session.get(url, timeout=self._timeout)

            # Handle HTTP errors
            if response.status_code == 404:
                raise RegistryConfigNotFoundError(
                    f"Model config not found: {model_id} version {version or 'latest'}"
                )
            elif response.status_code in (401, 403):
                raise RegistryAuthError(f"Registry authentication failed: {response.status_code}")
            elif response.status_code >= 400:
                # SECURITY: Don't log response body (may contain sensitive data)
                raise RegistryError(f"Registry returned error {response.status_code}")

        except requests.exceptions.Timeout as e:
            raise RegistryConnectionError(
                f"Registry request timed out after {self._timeout}s"
            ) from e
        except requests.exceptions.ConnectionError as e:
            # SECURITY: Redact full URL, show only hostname
            hostname = self._url.split("//")[-1].split("/")[0]
            raise RegistryConnectionError(f"Failed to connect to registry at {hostname}") from e
        except (RegistryConfigNotFoundError, RegistryAuthError):
            # Re-raise our custom exceptions
            raise
        except requests.exceptions.RequestException as e:
            raise RegistryConnectionError(f"Registry request failed: {e}") from e

        # Parse response
        try:
            data = response.json()
        except ValueError as e:
            raise RegistryError(f"Invalid JSON response from registry: {e}") from e

        # Convert to ModelConfig
        try:
            config = ModelConfig(
                service_name=data["service_name"],
                model_id=data["model_id"],
                model_version=data["model_version"],
                team_name=data["team_name"],
                model_type=data["model_type"],
                thresholds=data.get("thresholds", {}),
                extra_resource=data.get("extra_resource", {}),
            )
            return config
        except KeyError as e:
            raise RegistryError(f"Registry response missing required field: {e}") from e
        except (TypeError, ValueError) as e:
            raise RegistryError(f"Invalid registry response format: {e}") from e

    def fetch_deployment_config(self, deployment_id: str) -> DeploymentConfig:
        """Fetch deployment configuration from registry.

        Args:
            deployment_id: Unique deployment identifier

        Returns:
            DeploymentConfig with fetched configuration

        Raises:
            RegistryConnectionError: If unable to connect to registry
            RegistryConfigNotFoundError: If deployment not found
            RegistryAuthError: If authentication fails
            RegistryError: For other registry errors
        """
        # Check cache first
        cache_key = f"deployment:{deployment_id}"
        cached = self._get_cached(cache_key)
        if cached:
            logger.debug(f"Cache hit for {cache_key}")
            return cached

        logger.info(f"Fetching deployment config for {deployment_id}")
        start_time = time.time()

        # First try without retry to catch non-retryable errors immediately
        try:
            config = self._fetch_deployment_config_internal(deployment_id)
            self._set_cache(cache_key, config)

            # Record telemetry success
            if self._telemetry:
                latency = time.time() - start_time
                self._telemetry.record_success(latency)

            return config
        except (RegistryAuthError, RegistryConfigNotFoundError) as e:
            # Don't retry permanent failures (401/403/404) - fail immediately
            if self._telemetry:
                self._telemetry.record_error(type(e).__name__)
            raise
        except (RegistryConnectionError, RegistryError) as e:
            # Retry transient failures
            logger.warning(f"Retrying deployment config fetch for {deployment_id} due to: {e}")

            def _fetch_with_retry():
                return self._fetch_deployment_config_internal(deployment_id)

            try:
                config = self._retry_policy.execute(_fetch_with_retry)
                self._set_cache(cache_key, config)

                # Record telemetry success
                if self._telemetry:
                    latency = time.time() - start_time
                    self._telemetry.record_success(latency)

                return config
            except Exception as retry_e:
                if self._telemetry:
                    self._telemetry.record_error(type(retry_e).__name__)
                logger.error(f"Failed to fetch deployment config for {deployment_id} after retries: {retry_e}")
                raise

    def _fetch_deployment_config_internal(self, deployment_id: str) -> DeploymentConfig:
        """Internal method to fetch deployment config.

        Args:
            deployment_id: Deployment identifier

        Returns:
            DeploymentConfig from registry response

        Raises:
            Similar exceptions as _fetch_model_config_internal
        """
        # Build URL
        endpoint = f"/deployments/{deployment_id}"
        url = urljoin(self._url + "/", endpoint.lstrip("/"))

        # Make request
        try:
            logger.debug(f"GET {endpoint}")
            response = self._session.get(url, timeout=self._timeout)

            if response.status_code == 404:
                raise RegistryConfigNotFoundError(f"Deployment config not found: {deployment_id}")
            elif response.status_code in (401, 403):
                raise RegistryAuthError(f"Registry authentication failed: {response.status_code}")
            elif response.status_code >= 400:
                # SECURITY: Don't log response body (may contain sensitive data)
                raise RegistryError(f"Registry returned error {response.status_code}")

        except requests.exceptions.Timeout as e:
            raise RegistryConnectionError(
                f"Registry request timed out after {self._timeout}s"
            ) from e
        except requests.exceptions.ConnectionError as e:
            # SECURITY: Redact full URL, show only hostname
            hostname = self._url.split("//")[-1].split("/")[0]
            raise RegistryConnectionError(f"Failed to connect to registry at {hostname}") from e
        except (RegistryConfigNotFoundError, RegistryAuthError):
            raise
        except requests.exceptions.RequestException as e:
            raise RegistryConnectionError(f"Registry request failed: {e}") from e

        # Parse response
        try:
            data = response.json()
        except ValueError as e:
            raise RegistryError(f"Invalid JSON response from registry: {e}") from e

        # Convert to DeploymentConfig
        try:
            config = DeploymentConfig(
                deployment_id=data["deployment_id"],
                environment=data["environment"],
                region=data["region"],
                resource_overrides=data.get("resource_overrides", {}),
            )
            return config
        except KeyError as e:
            raise RegistryError(f"Registry response missing required field: {e}") from e
        except (TypeError, ValueError) as e:
            raise RegistryError(f"Invalid registry response format: {e}") from e

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached config if not expired.

        Args:
            key: Cache key

        Returns:
            Cached config (ModelConfig or DeploymentConfig) or None if not found/expired
        """
        with self._cache_lock:
            entry = self._cache.get(key)
            if entry and time.time() < entry.expires_at:
                return entry.value
            elif entry:
                # Expired, remove from cache
                del self._cache[key]
            return None

    def _set_cache(self, key: str, value: Any) -> None:
        """Cache a config with TTL.

        Args:
            key: Cache key
            value: Config to cache (ModelConfig or DeploymentConfig)
        """
        with self._cache_lock:
            self._cache[key] = CacheEntry(value=value, expires_at=time.time() + self._cache_ttl)

    def clear_cache(self) -> None:
        """Clear all cached configurations."""
        with self._cache_lock:
            self._cache.clear()
            logger.debug("Registry cache cleared")

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()
