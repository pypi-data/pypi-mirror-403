# Changelog

All notable changes to the MCA SDK will be documented in this file.

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

## [0.1.0] - 2025-12-15

### Added
- Initial MCA SDK implementation
- OpenTelemetry provider setup (metrics, logs, traces)
- PHI masking with multiple strategies (hash, redact, partial, tokenize)
- Metric naming validation for model types (internal, generative, vendor)
- Resource attribute validation
- Buffering with queue and retry policies
- Configuration management (kwargs, env, YAML)
- Comprehensive test suite (199 tests)
- Docker Compose orchestration
- Vendor API bridge pattern
- GenAI/LLM monitoring with LiteLLM
- Streamlit model monitoring with ML metrics
