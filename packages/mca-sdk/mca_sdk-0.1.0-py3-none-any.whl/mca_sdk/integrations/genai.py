"""GenAI/LLM integration helpers for MCA SDK.

This module provides helper functions and utilities for instrumenting
GenAI and LLM models (OpenAI, LiteLLM, etc.) with the MCA SDK.
"""

import logging
from typing import Dict, Optional

from ..core.client import MCAClient

logger = logging.getLogger(__name__)


# OpenAI pricing per 1K tokens (as of Jan 2025)
# Update these as pricing changes
OPENAI_PRICING = {
    "gpt-4": {
        "prompt": 0.03,
        "completion": 0.06,
    },
    "gpt-4-32k": {
        "prompt": 0.06,
        "completion": 0.12,
    },
    "gpt-3.5-turbo": {
        "prompt": 0.0015,
        "completion": 0.002,
    },
    "gpt-3.5-turbo-16k": {
        "prompt": 0.003,
        "completion": 0.004,
    },
}


def create_genai_client(
    service_name: str, llm_provider: str, llm_model: str, team_name: Optional[str] = None, **kwargs
) -> MCAClient:
    """Create MCAClient preconfigured for GenAI/LLM models.

    Convenience function that creates an MCAClient with appropriate
    defaults for GenAI models.

    Args:
        service_name: Name of the LLM service
        llm_provider: LLM provider (e.g., "openai", "anthropic", "azure")
        llm_model: Model name (e.g., "gpt-4", "claude-2")
        team_name: Team responsible for the service
        **kwargs: Additional arguments for MCAClient

    Returns:
        Configured MCAClient instance

    Example:
        >>> client = create_genai_client(
        ...     service_name="clinical-summarization",
        ...     llm_provider="openai",
        ...     llm_model="gpt-4",
        ...     team_name="ai-team"
        ... )
    """
    return MCAClient(
        service_name=service_name,
        model_type="generative",
        llm_provider=llm_provider,
        llm_model=llm_model,
        team_name=team_name,
        **kwargs,
    )


def estimate_openai_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate cost for OpenAI API call.

    Calculates estimated cost based on token usage and model pricing.
    Pricing is updated as of January 2025.

    Args:
        model: OpenAI model name (e.g., "gpt-4", "gpt-3.5-turbo")
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens

    Returns:
        Estimated cost in USD

    Example:
        >>> cost = estimate_openai_cost(
        ...     model="gpt-4",
        ...     prompt_tokens=100,
        ...     completion_tokens=50
        ... )
        >>> print(f"Estimated cost: ${cost:.4f}")
        Estimated cost: $0.0060
    """
    # Default to gpt-3.5-turbo pricing if model not found
    pricing = OPENAI_PRICING.get(model, OPENAI_PRICING["gpt-3.5-turbo"])

    prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * pricing["completion"]

    return prompt_cost + completion_cost


def track_llm_completion(
    client: MCAClient,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency: float,
    status: str = "success",
    error: Optional[str] = None,
):
    """Track LLM completion metrics.

    Records standard GenAI metrics for an LLM completion request.

    Args:
        client: MCAClient instance
        model: LLM model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        latency: Request latency in seconds
        status: Request status ("success" or "error")
        error: Error message if status is "error"

    Example:
        >>> client = create_genai_client(...)
        >>> track_llm_completion(
        ...     client=client,
        ...     model="gpt-4",
        ...     prompt_tokens=100,
        ...     completion_tokens=50,
        ...     latency=1.5,
        ...     status="success"
        ... )
    """
    # Record request count
    client.record_metric("genai.requests_total", 1, model=model, status=status)

    # Record token counts
    total_tokens = prompt_tokens + completion_tokens
    client.record_metric("genai.tokens_total", total_tokens, model=model, token_type="total")
    client.record_metric("genai.tokens_total", prompt_tokens, model=model, token_type="prompt")
    client.record_metric(
        "genai.tokens_total", completion_tokens, model=model, token_type="completion"
    )

    # Record latency
    client.record_metric("genai.latency_seconds", latency, model=model)

    # Estimate and record cost (for OpenAI models)
    if model in OPENAI_PRICING:
        cost = estimate_openai_cost(model, prompt_tokens, completion_tokens)
        client.record_metric("genai.cost_dollars", cost, model=model)

    # Record error if present
    if error:
        logger.error(
            f"LLM completion error: {error}",
            extra={
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "error": error,
            },
        )


def track_llm_embedding(
    client: MCAClient,
    model: str,
    tokens: int,
    latency: float,
    dimensions: int,
    status: str = "success",
):
    """Track LLM embedding generation metrics.

    Records metrics for embedding generation requests.

    Args:
        client: MCAClient instance
        model: Embedding model name
        tokens: Number of tokens processed
        latency: Request latency in seconds
        dimensions: Embedding vector dimensions
        status: Request status

    Example:
        >>> track_llm_embedding(
        ...     client=client,
        ...     model="text-embedding-ada-002",
        ...     tokens=100,
        ...     latency=0.5,
        ...     dimensions=1536
        ... )
    """
    client.record_metric("genai.embedding_requests_total", 1, model=model, status=status)

    client.record_metric("genai.embedding_tokens_total", tokens, model=model)

    client.record_metric("genai.embedding_latency_seconds", latency, model=model)

    client.record_metric("genai.embedding_dimensions_count", dimensions, model=model)


def calculate_token_rate(
    prompt_tokens: int, completion_tokens: int, latency: float
) -> Dict[str, float]:
    """Calculate token generation rates.

    Args:
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        latency: Request latency in seconds

    Returns:
        Dictionary with token rates (tokens per second)

    Example:
        >>> rates = calculate_token_rate(100, 50, 1.5)
        >>> print(f"Completion rate: {rates['completion_rate']:.2f} tokens/sec")
    """
    if latency == 0:
        return {"total_rate": 0.0, "prompt_rate": 0.0, "completion_rate": 0.0}

    total_tokens = prompt_tokens + completion_tokens

    return {
        "total_rate": total_tokens / latency,
        "prompt_rate": prompt_tokens / latency,
        "completion_rate": completion_tokens / latency,
    }
