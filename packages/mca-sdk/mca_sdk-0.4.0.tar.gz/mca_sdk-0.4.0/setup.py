"""Setup configuration for MCA SDK.

This file enables pip installation of the MCA SDK package.
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_file(filename):
    """Read file contents."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# Version
VERSION = "0.1.0"

# Core dependencies required for basic SDK functionality
INSTALL_REQUIRES = [
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-otlp-proto-http>=1.20.0",
    "pyyaml>=6.0",
]

# Optional dependencies for development
EXTRAS_REQUIRE = {
    # Development dependencies (testing, linting, etc.)
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "pytest-asyncio>=0.21.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=0.3.0",
        "pip-audit==2.10.0",
        "wheel>=0.46.2",
    ],
    # GenAI model integration dependencies
    "genai": [
        "litellm>=1.61.15",
    ],
    # Vendor integration dependencies (if needed)
    "vendor": [
        "requests>=2.32.4",
    ],
}

# All optional dependencies combined (excluding genai to avoid heavy transitive dependencies)
EXTRAS_REQUIRE["all"] = (
    EXTRAS_REQUIRE["dev"] + EXTRAS_REQUIRE["vendor"]
)

setup(
    name="mca-sdk",
    version=VERSION,
    description="Model & Clinical AI (MCA) SDK for HIPAA-compliant OpenTelemetry instrumentation",
    long_description=read_file("mca-prototype/README.md"),
    long_description_content_type="text/markdown",
    author="Baptist Health South Florida",
    author_email="mlops@baptisthealth.net",
    url="https://github.com/baptisthealth/mca-sdk",
    project_urls={
        "Documentation": "https://github.com/baptisthealth/mca-sdk#readme",
        "Source": "https://github.com/baptisthealth/mca-sdk",
        "Bug Tracker": "https://github.com/baptisthealth/mca-sdk/issues",
    },
    packages=find_packages(where="mca-prototype", exclude=["tests", "tests.*", "sdk-examples", "sdk-examples.*", "demo", "demo.*", "config", "config.*"]),
    package_dir={"": "mca-prototype"},
    python_requires=">=3.10",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="opentelemetry monitoring telemetry healthcare hipaa ml ai",
    license="Apache-2.0",
    zip_safe=False,
    include_package_data=True,
)
