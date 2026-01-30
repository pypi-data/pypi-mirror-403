# Changelog

All notable changes to the MCA SDK will be documented in this file.

## [0.4.0] - 2026-01-26

### Added
- **Background Registry Refresh Thread** (Story 2.3)
  - Automatic refresh of registry config at configurable intervals
  - Daemon thread with graceful shutdown
  - Thread-safe config updates with locking
  - Comprehensive unit tests for thread safety and lifecycle

- **Attributes Processor Integration** (Story 4.3)
  - OpenTelemetry Collector attributes processor for metadata enrichment
  - Automatic addition of `gcp.region` and `environment` attributes
  - Non-overwriting insertion semantics to preserve existing attributes
  - Integration tests covering all telemetry types (metrics, logs, traces)

- **Enhanced Demo Scripts**
  - OTLP endpoint configuration for better local development
  - Improved logging and error handling

### Changed
- **OpenTelemetry Dependencies** - Updated from 1.20.0 to 1.39.0
  - `opentelemetry-api>=1.39.0`
  - `opentelemetry-sdk>=1.39.0`
  - `opentelemetry-exporter-otlp-proto-http>=1.39.0`

### Fixed
- CI pipeline refinements for better reliability
- Removed orphaned pyproject.toml scan after merge
- Updated pip-audit command to skip editable packages
- Security: Temporarily ignore CVE-2026-0994 until protobuf patch available

## [0.3.0] - 2026-01-22

### Added
- **Custom Exception Hierarchy** (Story 1.14)
  - `MCASDKError` - Base exception class for all SDK errors
  - `ValidationError` - Raised when validation fails (metric names, attributes)
  - `BufferingError` - Raised when buffering operations fail (queue full, disk failure)
  - `ConfigurationError` - Raised when configuration is invalid or incomplete
  - `RegistryError` - Base exception for registry operations
  - `RegistryConnectionError` - Raised when unable to connect to registry
  - `RegistryConfigNotFoundError` - Raised when model config not found in registry
  - `RegistryAuthError` - Raised when registry authentication fails
  - All exceptions exported from main `mca_sdk` package for easy catching
  - Helpful error messages with context for debugging

### Changed
- **Enhanced Configuration Validation** (Story 1.15)
  - `MCAConfig.__post_init__` now raises `ConfigurationError` (was generic `Exception`)
  - `MCAConfig.from_env` raises `ConfigurationError` for invalid integer values
  - `MCAConfig.from_file` raises `ConfigurationError` for file/parsing errors
  - `MCAConfig.load` enforces security: `registry_token` via environment only
  - Better error messages with suggested fixes for missing `service_name`
  - URL validation for `collector_endpoint` and `registry_url`
  - Security warnings for HTTP endpoints (non-localhost) using `SecurityWarning` category

## [0.2.0] - 2026-01-12

### Added
- **Model Registry Integration**: Centralized configuration management system
  - `RegistryClient` for fetching model config from registry API
  - Support for `GET /models/{model_id}` and `GET /deployments/{deployment_id}` endpoints
  - Automatic retry with exponential backoff using existing `RetryPolicy`
  - In-memory cache with configurable TTL (default 10 minutes)
  - Bearer token authentication with HTTPS enforcement

- **Dynamic Configuration**
  - `MCAConfig` extended with 5 new fields: `registry_url`, `registry_token`, `refresh_interval_secs`, `prefer_registry`, `deployment_id`
  - Environment variable support: `MCA_REGISTRY_URL`, `MCA_REGISTRY_TOKEN`, etc.
  - Config precedence: kwargs > registry > env > YAML > defaults

- **Background Refresh**
  - Automatic refresh of thresholds and PHI fields every 10 minutes (configurable)
  - Identity fields (service_name, model_id) are immutable after startup
  - Graceful handling of registry failures with fallback to last-known config

- **PHI Fields Management**
  - Union of local and registry PHI fields for comprehensive masking
  - Dynamic updates via background refresh

- **Registry Telemetry**
  - Self-monitoring metrics: `mca.registry.refresh_success_total`, `mca.registry.refresh_latency_seconds`, `mca.registry.errors_total`

- **Security**
  - HTTPS required for non-localhost registry endpoints
  - Token never logged (even at DEBUG level)
  - Query parameters excluded from logs

- **Testing**
  - 22 unit tests for RegistryClient (fetch, cache, retry, auth)
  - 11 unit tests for hydration flow and config precedence
  - 8 integration tests with FastAPI mock registry

### Changed
- `MCAClient.__init__` now performs registry hydration before provider setup
- `MCAClient.shutdown` now stops background refresh thread and closes registry client
- `setup_all_providers` accepts `extra_resource` parameter for registry attributes
- Provider resource attributes now include registry-provided `extra_resource` fields

### API Additions
- `MCAClient.thresholds` property - Access current thresholds from registry
- `RegistryClient` class exported from main package
- `ModelConfig` and `DeploymentConfig` dataclasses exported from main package

## [0.1.0] - 2026-01-21

### Added
- Core MCA SDK with `MCAClient` for HIPAA-compliant OpenTelemetry instrumentation
- Multi-source configuration system with precedence: kwargs > registry > env > YAML > defaults
- Registry integration with automatic caching and retry mechanisms
- Validation and buffering systems for telemetry data
- Schema validation for metric naming and resource attributes
- Four working SDK examples:
  - Internal model instrumentation
  - GenAI model integration
  - Agentic AI workflows
  - Vendor model integration
- Docker Compose orchestration for local development
- Integration helpers for vendor models, GenAI, and Python decorators
- Comprehensive test suite with unit and integration tests
- Support for Python 3.10, 3.11, and 3.12

### Changed
- Buffering disabled by default for backward compatibility
- Improved demo scripts with better logging and metric handling
- Refactored metric names for consistency and clarity

### Removed
- PHI detection and masking features (architectural decision to simplify initial release)

### Fixed
- Buffering backward compatibility in `from_env()` configuration
- Critical `SecurityWarning` class placement in `MCAConfig`
- Multiple security and reliability issues identified in code review
- Test coverage expanded to meet 85% requirement

### Security
- Security hardening for multi-source configuration system
- Registry token blocked from YAML configuration files to prevent credential exposure
- Localhost validation fixed to prevent substring attacks
- Comprehensive security review addressing CRITICAL and HIGH priority issues

[unreleased]: https://github.com/baptisthealth/mca-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/baptisthealth/mca-sdk/releases/tag/v0.1.0