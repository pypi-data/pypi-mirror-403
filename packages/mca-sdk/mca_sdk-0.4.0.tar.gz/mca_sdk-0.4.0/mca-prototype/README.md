# MCA Prototype - Model Collector Agent

[![Pipeline Status](https://gitlab.com/bhsf/ai_ml/monitoring/badges/main/pipeline.svg)](https://gitlab.com/bhsf/ai_ml/monitoring/-/pipelines)
[![Security Scan](https://img.shields.io/badge/security-pip--audit-blue)](https://gitlab.com/bhsf/ai_ml/monitoring/-/pipelines)

A working prototype of an OpenTelemetry-based telemetry collection system for healthcare ML model monitoring. Demonstrates metric, log, and trace collection from both internally instrumented models and third-party vendor APIs, with automatic metadata enrichment before export.

## Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Internal     │  │  Vendor API  │  │  GenAI       │  │  E2E Tests   │
│ Model        │  │  (FastAPI)   │  │  Assistant   │  │  (pytest)    │
│ (Py + SDK)   │  │              │  │  (LiteLLM)   │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                  │                  │                  │
       │ OTLP/HTTP        │ Custom JSON      │ OTLP/HTTP        │ OTLP/HTTP
       │ :4318            │                  │ :4318            │ :4318
       │                  ▼                  │                  │
       │         ┌─────────────────┐         │                  │
       │         │ Vendor Bridge   │         │                  │
       │         │ (Polling 30s)   │         │                  │
       │         │ JSON→OTLP       │         │                  │
       │         └────────┬────────┘         │                  │
       │                  │ OTLP/HTTP        │                  │
       │                  │ :4318            │                  │
       ▼                  ▼                  ▼                  ▼
    ┌──────────────────────────────────────────────────────────────┐
    │           OpenTelemetry Collector (Port 4318)                │
    │                                                               │
    │  ┌──────────┐    ┌────────────────┐    ┌──────────────┐     │
    │  │  Batch   │ →  │  Attributes    │ →  │    Debug     │     │
    │  │Processor │    │  Processor     │    │  Exporter    │     │
    │  │(10s/100) │    │(region, env)   │    │  (stdout)    │     │
    │  └──────────┘    └────────────────┘    └──────────────┘     │
    └──────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                            Docker Logs / Console
                         (Simulates GCP Backend)
```

## Installation

### From PyPI (Recommended)

Install the MCA SDK from PyPI:

```bash
pip install mca-sdk
```

### With Optional Dependencies

Install with specific optional dependency groups:

```bash
# For GenAI/LLM monitoring (includes LiteLLM)
pip install mca-sdk[genai]

# For vendor integration (includes requests for Model Registry)
pip install mca-sdk[vendor]

# For development (includes pytest, black, mypy, etc.)
pip install mca-sdk[dev]

# All optional dependencies
pip install mca-sdk[all]
```

### Version Pinning

Pin to a specific version for production deployments:

```bash
# Install exact version
pip install mca-sdk==0.3.0

# Install with version constraints
pip install "mca-sdk>=0.3.0,<2.0.0"
```

### Verify Installation

```bash
# Check installed version
pip show mca-sdk

# Test import
python -c "from mca_sdk import MCAClient; print('MCA SDK installed successfully')"
```

### Troubleshooting

**Import Error after installation:**
- Verify installation: `pip show mca-sdk`
- Check Python version: `python --version` (requires Python 3.10+)
- Test import: `python -c "from mca_sdk import MCAClient"`

**Dependency conflicts:**
- Use a virtual environment:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install mca-sdk
  ```
- Clear pip cache: `pip cache purge`

**OpenTelemetry version conflicts:**
- The SDK requires `opentelemetry-sdk>=1.20.0`
- Check installed versions: `pip list | grep opentelemetry`
- Upgrade if needed: `pip install --upgrade mca-sdk`

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.10+ (for running tests and standalone examples)
- No GCP account needed (uses debug exporter)

### Step 1: Start the Stack
```bash
cd mca-prototype
docker-compose up
```

Expected output indicators:
- `mca-otel-collector` container starts and shows collector startup
- `mca-vendor-api` shows FastAPI startup on port 8080
- `mca-vendor-bridge` begins polling and exporting metrics every 30s

### Step 2: Run the Demo Model

#### Option A: Using PyPI Package (Recommended)
 In another terminal, install mca-sdk from PyPI and run the standalone demo:
```bash
# Install package
pip install mca-sdk

# Run standalone demo (can be executed from any directory)
python mca-prototype/demo_installed_package.py
```

#### Option B: Development Mode
Install dependencies and run example from repository:
```bash
cd mca-prototype
pip install -r sdk-examples/internal-model/requirements.txt
python sdk-examples/internal-model/instrumented_model.py
```

Expected behavior (both options):
- Runs predictions with 1-second intervals
- Prints prediction latency for each iteration
- Sends metrics, logs, and traces to collector
- Flushes all telemetry at completion

### Step 3: Observe the Collector Logs

Look for output in the collector terminal showing received telemetry:

**Metrics from Internal Model**:
```
ResourceMetrics #0
Resource attributes:
     -> service.name: Str(demo-readmission-model)
     -> model.id: Str(mdl-001)
     -> gcp.region: Str(us-central1)        ← Added by collector
     -> environment: Str(prototype)         ← Added by collector
Metric #0
     -> Name: model_predictions_total
     -> Value: 10
```

**Metrics from Vendor API** (appears every 30 seconds):
```
Resource attributes:
     -> service.name: Str(vendor-sepsis-v2)
     -> model.type: Str(vendor)
     -> gcp.region: Str(us-central1)        ← Added by collector
     -> environment: Str(prototype)         ← Added by collector
Metric #0
     -> Name: model.accuracy
     -> Value: 0.89
```

**Traces from Internal Model**:
```
Span #0
     -> Name: model.predict
     -> Attributes:
          -> model.id: Str(mdl-001)
          -> prediction_id: Str(pred-1234)
```

### Step 4: Run E2E Tests
```bash
# Collector must be running from Step 1
cd mca-prototype
pip install -r requirements.txt
pytest tests/test_e2e_flow.py -v -s
```

Expected output:
- Health check passes
- Counter metric test sends value 42, verifies in logs (waits 12s for batch timeout)
- Histogram test sends 5 values, verifies in logs
- Attribute enrichment test confirms `gcp.region` and `environment` added

### Step 5: Run Unit Tests
```bash
pytest tests/test_sdk_integration.py -v
```

Expected: ~20 tests pass covering provider initialization, metric operations, graceful failure handling, and resource attribute propagation

## PyPI Package Verification

If you've installed `mca-sdk` from PyPI, you can verify it works correctly without any local repository dependencies.

### Standalone Demo

The standalone demo demonstrates using the PyPI-installed package:

```bash
# Install from PyPI
pip install mca-sdk

# Start collector
cd mca-prototype && docker-compose up otel-collector

# Run demo (works from any directory - no sys.path manipulation)
python mca-prototype/demo_installed_package.py
```

**Key Points**:
- No `sys.path.insert()` needed
- Clean imports: `from mca_sdk import MCAClient`
- Works from any directory (not just inside cloned repo)
- All dependencies auto-installed

### PyPI Package Tests

Run verification tests to ensure the package is properly installed:

```bash
# Install package first
pip install mca-sdk

# Run PyPI verification tests
pytest tests/test_pypi_package.py -v
```

These tests verify:
- Package is installed from PyPI (not local)
- Imports work without path manipulation
- Client can be instantiated
- Metrics can be created and recorded
- Dependencies are properly installed
- Optional dependencies (genai, vendor) work if installed

### Example Requirements Files

All examples have been updated to use the PyPI package:

**internal-model/requirements.txt**:
```txt
mca-sdk>=0.3.0
opentelemetry-semantic-conventions==0.48b0
```

**internal-genai/requirements.txt**:
```txt
mca-sdk[genai]>=0.3.0
tiktoken>=0.5.2
```

**internal-agentic/requirements.txt**:
```txt
mca-sdk>=0.3.0
langchain>=0.1.0
```

**vendor-model/requirements.txt**:
```txt
mca-sdk[vendor]>=0.3.0
fastapi>=0.115.6
uvicorn>=0.34.0
```

## Development Setup

For developers contributing to the MCA Prototype, we provide a reproducible development environment with Docker Compose, hot-reload, pre-commit hooks, and IDE configurations.

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Git
- Make (optional, but recommended)

### One-Time Setup

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd monitoring-3

# Run the automated setup script
make dev-setup
# OR manually:
./scripts/setup-dev.sh
```

This script will:
1. Create a Python virtual environment
2. Install all Python dependencies (SDK, dev tools, pre-commit)
3. Install pre-commit hooks for automatic code quality checks
4. Build Docker images for all services
5. Create a `.env` file from `.env.example`

**Setup time:** <10 minutes (depending on internet speed)

### Starting Development Services

```bash
# Start all services (collector, examples, vendor API)
make dev-start

# View logs from all services
make logs

# Stop all services
make dev-stop
```

**Available Services:**
- OTel Collector: `http://localhost:4318` (OTLP), `http://localhost:13133` (health)
- Vendor API: `http://localhost:8080`
- Internal Model: Container `mca-internal-model`
- Internal Agentic: Container `mca-internal-agentic`
- GenAI Assistant: Container `mca-genai-assistant`
- Vendor Bridge: Container `mca-vendor-bridge`

### Hot-Reload for Fast Iteration

All services have volume mounts configured for live code reload:
```yaml
volumes:
  - ./mca_sdk:/app/mca_sdk  # Changes to SDK reflected immediately
```

**To test hot-reload:**
1. Start services: `make dev-start`
2. Modify code in `mca_sdk/`
3. Check container logs: `docker logs mca-internal-model -f`
4. Changes are reflected without restarting containers

### Running Tests

```bash
# Run all tests with coverage (requires 85% coverage)
make test

# Run tests manually
pytest tests/ -v --cov=mca-prototype/mca_sdk --cov-fail-under=85
```

### Code Quality & Linting

```bash
# Run all linting checks (Black, isort, pylint, mypy, bandit)
make lint

# Auto-format code (Black + isort)
make format

# Run pre-commit hooks manually
make pre-commit
```

**Pre-commit hooks run automatically** on every `git commit` and check:
- Python formatting (Black)
- Import sorting (isort)
- Python linting (pylint)
- Type checking (mypy)
- Security scanning (Bandit)
- YAML/JSON formatting (Prettier)
- Dockerfile linting (hadolint)

### IDE Setup (VS Code)

VS Code configurations are included in `.vscode/`:
- **settings.json**: Python linting, formatting, testing
- **launch.json**: Debug configurations for tests and examples

**Recommended Extensions:**
- Python (ms-python.python)
- Black Formatter (ms-python.black-formatter)
- Pylance (ms-python.vscode-pylance)
- Docker (ms-azuretools.vscode-docker)
- Prettier (esbenp.prettier-vscode)

**Debug Examples:**
1. Open VS Code
2. Go to Run & Debug (Ctrl+Shift+D)
3. Select debug configuration (e.g., "Python: Debug SDK Internal Model Example")
4. Press F5 to start debugging

### Common Development Tasks

```bash
# Run a specific example locally
source venv/bin/activate
export PYTHONPATH=$(pwd)/mca-prototype
python mca-prototype/sdk-examples/internal-model/instrumented_model.py

# View logs from a specific service
docker logs mca-internal-model -f

# Rebuild a specific service after Dockerfile changes
cd mca-prototype && docker-compose build internal-model

# Clean up build artifacts
make clean

# Full clean including virtual environment
make clean-all
```

### Development Workflow

1. **Create a feature branch**: `git checkout -b feature/your-feature`
2. **Make code changes** in `mca_sdk/` or examples
3. **Run tests locally**: `make test`
4. **Run linting**: `make lint` (or let pre-commit handle it)
5. **Commit changes**: `git commit -m "description"` (pre-commit hooks run automatically)
6. **Push and create PR**: `git push origin feature/your-feature`

### Troubleshooting Development Setup

**Issue: Pre-commit hooks failing**
```bash
# Run hooks manually to see errors
pre-commit run --all-files

# Auto-fix formatting issues
make format

# Update pre-commit hooks
pre-commit autoupdate
```

**Issue: Docker containers not starting**
```bash
# Check Docker daemon is running
docker ps

# Rebuild containers
cd mca-prototype && docker-compose build

# Check logs
docker-compose logs
```

**Issue: Tests failing with import errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r mca-prototype/mca_sdk/requirements.txt
```

**Issue: Port conflicts**
```bash
# Check what's using ports 4318 or 8080
lsof -i :4318
lsof -i :8080

# Stop conflicting services or change ports in docker-compose.yml
```

### Environment Variables

Development environment variables are configured in `.env` (created from `.env.example`):

```bash
# Key development settings
DEBUG_MODE=true
LOG_LEVEL=DEBUG
COLLECTOR_ENDPOINT=http://localhost:4318
REGISTRY_URL=http://localhost:8000  # Mock registry for local dev
```

See `.env.example` for all available configuration options.

## Project Structure

```
mca-prototype/
│
├── docker-compose.yml              # Orchestrates 3 services
│
├── config/
│   └── otel-collector-config.yaml  # Collector pipelines: OTLP → Batch → Attributes → Debug
│
├── mca/
│   └── Dockerfile                  # OpenTelemetry Collector (contrib:0.91.0)
│
├── sdk-examples/
│   ├── internal-model/
│   │   ├── instrumented_model.py   # Demo: Metrics, Logs, Traces instrumentation
│   │   └── requirements.txt        # OpenTelemetry SDK 1.27.0
│   │
│   ├── internal-genai/
│   │   ├── litellm_instrumented.py # GenAI assistant with LiteLLM + MCA SDK
│   │   ├── Dockerfile              # Python 3.11-slim with SDK
│   │   └── requirements.txt        # LiteLLM + OpenTelemetry SDK
│   │
│   ├── internal-agentic/
│   │   ├── agent_instrumented.py   # Medical research agent with multi-step reasoning
│   │   ├── tools.py                # Mock tools (PubMed, drug database, calculator)
│   │   ├── README.md               # Agentic AI example documentation
│   │   └── requirements.txt        # LangChain + OpenTelemetry SDK
│   │
│   └── vendor-model/
│       ├── mock_vendor_api.py      # FastAPI server returning JSON metrics
│       ├── api_to_otlp_bridge.py   # Polls API → Converts to OTLP → Sends to collector
│       ├── Dockerfile              # Python 3.11-slim for both services
│       └── requirements.txt        # FastAPI + OpenTelemetry SDK
│
├── tests/
│   ├── conftest.py                 # Pytest fixtures (in-memory exporters)
│   ├── test_sdk_integration.py     # Unit tests (~20 tests)
│   └── test_e2e_flow.py            # Integration tests (requires Docker)
│
├── requirements.txt                # Testing deps + SDK (for project-level tests)
└── pytest.ini                      # Test configuration
```

### Key Components

| Component | Purpose | Port |
|-----------|---------|------|
| **OpenTelemetry Collector** | Receives OTLP data, enriches with metadata, outputs to debug exporter | 4318, 13133 |
| **Internal Model** | Demonstrates full SDK instrumentation (metrics/logs/traces) for predictive ML | - |
| **Internal GenAI** | Demonstrates LLM monitoring with LiteLLM + MCA SDK integration | - |
| **Internal Agentic** | Demonstrates agentic AI with goal tracking, tool execution, and multi-step reasoning | - |
| **Vendor API** | Simulates third-party model API with proprietary JSON format | 8080 |
| **Vendor Bridge** | Converts vendor JSON to OTLP metrics every 30 seconds | - |
| **E2E Tests** | Validates collector receives and processes data | - |
| **Unit Tests** | Tests SDK integration patterns without network | - |

### Data Pipelines

1. **Metrics Pipeline**: `OTLP Receiver` → `Attributes Processor` (adds region/env) → `Batch Processor` (10s/100 metrics) → `Debug Exporter` (stdout)
2. **Logs Pipeline**: Same processors, OTLP logs input
3. **Traces Pipeline**: Same processors, OTLP traces input

### Enrichment Strategy
- All telemetry signals enriched with `gcp.region: us-central1` and `environment: prototype`
- Demonstrates how to add organizational metadata at collector level
- Resource attributes from application (service name, model ID) preserved

## Demo Scenarios

### Scenario 1: Internal Model Monitoring
**Use Case**: Hospital's readmission prediction model with full instrumentation

**Steps**:
1. Start collector: `docker-compose up`
2. Run model: `python sdk-examples/internal-model/instrumented_model.py`
3. Show collector logs with metrics, logs, and traces
4. Point out enriched attributes (`gcp.region`, `environment`)

**Key Points**:
- Full observability: metrics (counter/histogram), logs (structured), traces (nested spans)
- Resource attributes identify model, version, team
- Collector adds deployment context automatically

### Scenario 2: Vendor API Integration
**Use Case**: Third-party sepsis model doesn't support OTLP natively

**Steps**:
1. Collector already running from Scenario 1
2. Show vendor API JSON: `curl http://localhost:8080/metrics`
3. Observe bridge logs converting and exporting
4. Show collector receiving vendor metrics with `model.type: vendor` attribute

**Key Points**:
- Bridge pattern for non-OTLP APIs
- Delta calculation for counters (converts 24h rolling count to cumulative)
- Dynamic resource attributes from API response
- Polling every 30 seconds

### Scenario 3: E2E Validation
**Use Case**: Verify collector pipeline works correctly

**Steps**:
1. Run E2E tests: `pytest tests/test_e2e_flow.py -v -s`
2. Show test sending metrics with known values (42)
3. Show test parsing Docker logs to verify receipt
4. Demonstrate attribute enrichment validation

**Key Points**:
- Tests send real OTLP data to running collector
- Verifies batch processing (12s wait for 10s timeout)
- Log-based verification for manual inspection
- Validates enrichment pipeline

### Scenario 4: GenAI/LLM Monitoring
**Use Case**: Clinical documentation assistant with LLM observability

**Steps**:
1. Services already running from `docker-compose up`
2. Check GenAI logs: `docker logs mca-genai-assistant -f`
3. Observe collector receiving LLM traces with token counts
4. Show custom metrics in collector logs: `docker logs mca-otel-collector | grep genai`

**Key Points**:
- LiteLLM's automatic trace instrumentation for LLM calls
- Token usage tracking (prompt and completion tokens)
- Cost estimation based on token counts
- Latency monitoring for LLM requests
- Mock mode for demo purposes (no API calls)
- Continuous 30-second loop demonstrates ongoing LLM usage patterns

**Expected Telemetry**:
- Metrics: `genai.tokens.prompt`, `genai.tokens.completion`, `genai.request.cost_usd`, `genai.request.latency_seconds`
- Traces: Automatic spans from LiteLLM with model, token counts, and latency
- Resource attributes: `service.name=genai-clinical-assistant`, `model.type=generative`, `llm.provider=openai-mock`

### Scenario 5: Agentic AI with Multi-Step Reasoning
**Use Case**: Medical research assistant agent that uses multiple tools to answer clinical questions

**Steps**:
1. Collector already running from previous scenarios
2. Run agent: `python sdk-examples/internal-agentic/agent_instrumented.py`
3. Watch agent execute multi-step workflow (planning → research → analysis → synthesis)
4. Show agent metrics: `docker logs mca-otel-collector | grep agent`

**Key Points**:
- **Goal Tracking**: Monitors when goals start/complete with success/failure status
- **Tool Execution**: Tracks PubMed searches, drug database queries with latency metrics
- **Multi-Step Reasoning**: Nested spans show planning, research, analysis, synthesis steps
- **Human Intervention**: Tracks when human review is requested
- **Mock Mode**: All tools use predefined responses (no external APIs)

**Expected Telemetry**:
- Metrics:
  - `agent.goals_started_total`, `agent.goals_completed_total` (counters)
  - `agent.tool_calls_total` (counter with tool_name label)
  - `agent.tool_latency_seconds` (histogram per tool)
  - `agent.human_interventions_total` (counter)
  - `agent.reasoning_steps_total` (counter)
- Traces:
  - `agent.goal` (parent span for entire goal)
    - `agent.planning` (search strategy)
    - `agent.tool_execution` (PubMed, drug database)
    - `agent.reasoning` (analysis)
    - `agent.synthesis` (answer creation)
    - `agent.human_intervention` (review request)
- Resource attributes: `service.name=medical-research-agent`, `model.type=agentic`, `team.name=ai-research-team`

## Model Registry Integration

The MCA SDK now supports centralized configuration management through a Model Registry API. This enables:
- Dynamic model metadata and thresholds
- Automatic periodic refresh (default 10 minutes)
- Graceful fallback when registry is unavailable
- Security: HTTPS required for non-localhost, bearer token authentication

### Usage

**With Environment Variables:**
```bash
export MCA_REGISTRY_URL="https://registry.example.com"
export MCA_REGISTRY_TOKEN="your-secret-token"
export MCA_MODEL_ID="mdl-001"
export MCA_MODEL_VERSION="2.0.0"

python your_model.py
```

**With Code:**
```python
from mca_sdk import MCAClient, MCAConfig

config = MCAConfig(
    service_name="readmission-model",
    model_id="mdl-001",
    model_version="2.0.0",
    registry_url="https://registry.example.com",
    registry_token="your-secret-token",
    refresh_interval_secs=600,  # 10 minutes
)

client = MCAClient(config=config)

# Access registry-provided thresholds
if client.thresholds.get("latency_warn_ms", 0) < latency_ms:
    client.logger.warning("Latency threshold exceeded")

client.shutdown()
```

### Registry API Contract

**Model Config Endpoint:**
```http
GET /models/{model_id}?version=2.0.0
Authorization: Bearer <token>

Response:
{
  "service_name": "readmission-model",
  "model_id": "mdl-001",
  "model_version": "2.0.0",
  "team_name": "clinical-ai",
  "model_type": "internal",
  "thresholds": {
    "latency_warn_ms": 500,
    "error_rate_warn": 0.05
  },
  "extra_resource": {
    "deployment.env": "production"
  }
}
```

**Deployment Config Endpoint (optional):**
```http
GET /deployments/{deployment_id}
Authorization: Bearer <token>

Response:
{
  "deployment_id": "dep-001",
  "environment": "production",
  "region": "us-east-1",
  "resource_overrides": {
    "deployment.zone": "az-1"
  }
}
```

### Features

- **Config Precedence**: kwargs > registry > env > YAML > defaults
- **Background Refresh**: Updates thresholds every 10 minutes (configurable)
- **Identity Immutability**: service_name, model_id changes require restart
- **Resilience**: Telemetry continues if registry is down (uses last-known config)
- **Security**: HTTPS required, token never logged
- **Telemetry**: Self-monitoring metrics for registry operations

### Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `MCA_REGISTRY_URL` | Registry service URL (HTTPS required) | None |
| `MCA_REGISTRY_TOKEN` | Bearer token for authentication | None |
| `MCA_REFRESH_SECS` | Refresh interval in seconds | 600 |
| `MCA_PREFER_REGISTRY` | Registry overrides local config | True |
| `MCA_DEPLOYMENT_ID` | Optional deployment identifier | None |

## Next Steps / Known Limitations

### Implemented (Phase 1)
- ✅ OTLP HTTP receiver for metrics, logs, traces
- ✅ Batch processing (10s timeout or 100 metrics)
- ✅ Attribute enrichment (region, environment)
- ✅ Debug exporter for prototype validation
- ✅ Vendor API bridge pattern
- ✅ Full SDK instrumentation example
- ✅ GenAI/LLM monitoring with LiteLLM integration
- ✅ **Model Registry Integration**: Centralized config management with automatic refresh
- ✅ Comprehensive testing (unit + e2e)
- ✅ Docker Compose orchestration
- ✅ Health check endpoint

### Phase 2: Production Readiness
- [ ] **GCP Integration**: Replace debug exporter with Cloud Monitoring/Logging
  - OTLP/gRPC exporter to GCP endpoints
  - Service account authentication
  - Metric descriptor configuration
- [ ] **Security**: Add authentication to OTLP receiver
  - mTLS for service-to-collector communication
  - API keys for vendor bridge
- [ ] **High Availability**: Multi-instance collector with load balancing
- [ ] **Persistent Storage**: Add file exporter for backup/replay
- [ ] **Alerting**: Configure processor for alert generation on metric thresholds
- [ ] **Schema Validation**: Enforce metric naming conventions
- [ ] **Cost Optimization**: Sampling strategies for high-volume traces

### Phase 3: Scale & Features
- [ ] **Additional Vendors**: More bridge implementations
- [ ] **Real Models**: Production model integrations
- [ ] **Dashboards**: Grafana/GCP console visualizations
- [ ] **SLO Monitoring**: Track model performance SLIs
- [ ] **Anomaly Detection**: Statistical outlier identification
- [ ] **Data Retention**: Policies for metric aggregation/archival

### Known Limitations
- **No Authentication**: Open OTLP endpoint (prototype only)
- **No Persistence**: Metrics lost on collector restart
- **Batch Timeout**: Up to 10s delay in data visibility
- **Single Instance**: No redundancy or failover
- **Debug Exporter Only**: Not connected to real backend
- **Hardcoded Region**: Attribute processor has static region value
- **Manual Verification**: E2E tests rely on Docker log parsing

### Security Considerations (For Production)
- **Audit Logs**: Implement comprehensive access logging for collector
- **Encryption**: Require TLS for all OTLP communication
- **Access Control**: Implement RBAC for collector configuration
- **Data Residency**: Ensure GCP region meets compliance requirements

## Troubleshooting

### Collector not receiving metrics
**Symptom**: No output in collector logs after running model

**Solutions**:
- Check collector is healthy: `curl http://localhost:13133/`
- Verify port 4318 is accessible: `docker ps`
- Check model completed and flushed: Look for "Flushing metrics" in model output
- Increase batch timeout: Metrics may be waiting for 10s batch window

### Vendor bridge failing to start
**Symptom**: `mca-vendor-bridge` container exits with error

**Solutions**:
- Check vendor-api is healthy: `docker ps` (should show healthy status)
- Verify API is accessible: `curl http://localhost:8080/health`
- Check environment variables in docker-compose.yml
- Review bridge logs: `docker logs mca-vendor-bridge`

### E2E tests skipped
**Symptom**: Tests show "SKIPPED - Collector is not running"

**Solutions**:
- Start collector first: `docker-compose up`
- Wait for health endpoint: May take 10-15 seconds on first start
- Check health manually: `curl http://localhost:13133/`
- Rebuild if config changed: `docker-compose up --build`

### Import errors in tests
**Symptom**: `ImportError: cannot import name 'InMemorySpanExporter'`

**Solutions**:
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: Requires 3.10+
- Virtual environment recommended: `python -m venv venv && source venv/bin/activate`

## Additional Resources

- **OpenTelemetry Docs**: https://opentelemetry.io/docs/
- **Collector Configuration**: https://opentelemetry.io/docs/collector/configuration/
- **Python SDK**: https://opentelemetry-python.readthedocs.io/
- **OTLP Specification**: https://opentelemetry.io/docs/specs/otlp/

## Contributing

This is a prototype project for demonstration purposes. For production deployment:
1. Review security considerations
2. Implement authentication
3. Configure real GCP backend exporters
4. Set up monitoring for the collector itself
5. Establish metric retention policies
