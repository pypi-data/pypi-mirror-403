"""Resource attribute validation for MCA SDK.

This module validates that all required OpenTelemetry resource attributes
are present based on the model type.

Resource attributes are key-value pairs attached to all telemetry (metrics,
logs, traces) that provide context about the source of the data.
"""

from typing import Any, Dict, List

from ..utils.exceptions import ValidationError


# Required resource attributes by model type
REQUIRED_ATTRIBUTES = {
    "internal": [
        "service.name",  # Service name (required by OTel spec)
        "model.id",  # Unique model identifier
        "model.version",  # Model version string
        "team.name",  # Team responsible for model
    ],
    "generative": [
        "service.name",  # Service name (required by OTel spec)
        "llm.provider",  # LLM provider (openai, anthropic, etc.)
        "llm.model",  # Model name (gpt-4, claude-3, etc.)
        "team.name",  # Team responsible for integration
    ],
    "vendor": [
        "service.name",  # Service name (required by OTel spec)
        "model.type",  # Type of vendor model
        "vendor.name",  # Vendor name (epic, cerner, etc.)
        "team.name",  # Team responsible for integration
    ],
}

# Optional but recommended attributes (for all model types)
RECOMMENDED_ATTRIBUTES = [
    "service.version",  # Service/application version
    "deployment.environment",  # Environment (dev, staging, prod)
]


def validate_resource_attributes(
    attributes: Dict[str, Any], model_type: str = "internal", strict: bool = True
) -> None:
    """Validate that all required resource attributes are present.

    Args:
        attributes: Dictionary of resource attributes to validate
        model_type: Type of model (internal, generative, vendor)
        strict: If True, raise error on missing required attributes

    Raises:
        ValidationError: If required attributes are missing (strict mode only)

    Example:
        >>> attrs = {
        ...     "service.name": "my-model",
        ...     "model.id": "mdl-001",
        ...     "model.version": "1.0.0",
        ...     "team.name": "ml-team"
        ... }
        >>> validate_resource_attributes(attrs, "internal")  # OK
        >>> validate_resource_attributes({"service.name": "test"}, "internal")  # Raises ValidationError
    """
    # SECURITY: Input validation
    if not isinstance(attributes, dict):
        raise ValidationError(f"Attributes must be a dictionary, got {type(attributes)}")

    # Non-strict mode: skip validation (but still check input types)
    if not strict:
        return

    # Validate model type
    if model_type not in REQUIRED_ATTRIBUTES:
        raise ValidationError(
            f"Invalid model_type: {model_type}. "
            f"Must be one of: {', '.join(REQUIRED_ATTRIBUTES.keys())}"
        )

    # Get required attributes for this model type
    required = REQUIRED_ATTRIBUTES[model_type]

    # Check for missing attributes
    missing = []
    for attr_name in required:
        value = attributes.get(attr_name)

        # SECURITY: Check for None, empty strings, and validate string length
        if value is None or value == "":
            missing.append(attr_name)
        elif isinstance(value, str):
            # SECURITY: Limit attribute value length to prevent DoS
            MAX_ATTRIBUTE_VALUE_LENGTH = 1024
            if len(value) > MAX_ATTRIBUTE_VALUE_LENGTH:
                raise ValidationError(
                    f"Attribute '{attr_name}' value exceeds maximum length of "
                    f"{MAX_ATTRIBUTE_VALUE_LENGTH} characters. Got {len(value)} characters."
                )

    # Raise error if any required attributes are missing
    if missing:
        _raise_missing_attributes_error(missing, model_type, attributes)


def _raise_missing_attributes_error(
    missing: List[str], model_type: str, provided: Dict[str, Any]
) -> None:
    """Raise a detailed ValidationError for missing attributes.

    Args:
        missing: List of missing attribute names
        model_type: The model type being validated
        provided: The attributes that were provided
    """
    error_msg = f"Missing required resource attributes for model_type='{model_type}':\n" f"\n"

    # List missing attributes
    for attr in missing:
        error_msg += f"  - {attr}\n"

    error_msg += "\n"
    error_msg += f"Required attributes for '{model_type}' models:\n"
    for attr in REQUIRED_ATTRIBUTES[model_type]:
        status = "✓" if attr in provided and provided[attr] is not None else "✗"
        error_msg += f"  {status} {attr}\n"

    # Provide configuration example
    error_msg += "\n"
    error_msg += "Example configuration:\n"
    if model_type == "internal":
        error_msg += (
            "  client = MCAClient(\n"
            "      service_name='readmission-model',\n"
            "      model_id='mdl-001',\n"
            "      model_version='1.0.0',\n"
            "      team_name='clinical-ai'\n"
            "  )\n"
        )
    elif model_type == "generative":
        error_msg += (
            "  client = MCAClient(\n"
            "      service_name='clinical-note-summarizer',\n"
            "      model_type='generative',\n"
            "      llm_provider='openai',\n"
            "      llm_model='gpt-4',\n"
            "      team_name='clinical-ai'\n"
            "  )\n"
        )
    else:  # vendor
        error_msg += (
            "  client = MCAClient(\n"
            "      service_name='vendor-epic-sepsis',\n"
            "      model_type='vendor',\n"
            "      vendor_name='epic',\n"
            "      team_name='integrations'\n"
            "  )\n"
        )

    error_msg += "\n" "To disable validation, set strict_validation=False in MCAClient."

    raise ValidationError(error_msg)


def get_required_attributes(model_type: str) -> List[str]:
    """Get list of required attributes for a model type.

    Args:
        model_type: Type of model (internal, generative, vendor)

    Returns:
        List of required attribute names

    Raises:
        ValidationError: If model_type is not recognized

    Example:
        >>> get_required_attributes("internal")
        ['service.name', 'model.id', 'model.version', 'team.name']
    """
    if model_type not in REQUIRED_ATTRIBUTES:
        raise ValidationError(
            f"Invalid model_type: {model_type}. "
            f"Must be one of: {', '.join(REQUIRED_ATTRIBUTES.keys())}"
        )

    return REQUIRED_ATTRIBUTES[model_type].copy()


def get_recommended_attributes() -> List[str]:
    """Get list of recommended attributes for all model types.

    Returns:
        List of recommended attribute names

    Example:
        >>> get_recommended_attributes()
        ['service.version', 'deployment.environment']
    """
    return RECOMMENDED_ATTRIBUTES.copy()
