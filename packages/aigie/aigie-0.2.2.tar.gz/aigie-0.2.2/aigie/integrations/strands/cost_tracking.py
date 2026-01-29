"""
Cost tracking for Strands Agents.

Provides pricing information and cost calculation for various model providers
supported by Strands Agents (Bedrock, Anthropic, OpenAI, Gemini, etc.).
"""

from typing import Dict, Optional, Tuple

# Model pricing per 1M tokens (input/output)
# Prices are approximate and may vary by region/provider
STRANDS_MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Amazon Bedrock - Claude models
    "us.amazon.nova-pro-v1:0": {
        "input": 3.00,
        "output": 15.00,
    },
    "us.amazon.nova-lite-v1:0": {
        "input": 0.10,
        "output": 0.40,
    },
    "us.amazon.nova-micro-v1:0": {
        "input": 0.05,
        "output": 0.20,
    },
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "input": 3.00,
        "output": 15.00,
    },
    "anthropic.claude-3-5-haiku-20241022-v1:0": {
        "input": 1.00,
        "output": 5.00,
    },
    "anthropic.claude-3-opus-20240229-v1:0": {
        "input": 15.00,
        "output": 75.00,
    },
    "anthropic.claude-3-sonnet-20240229-v1:0": {
        "input": 3.00,
        "output": 15.00,
    },
    # Anthropic (direct)
    "claude-3-5-sonnet-20241022": {
        "input": 3.00,
        "output": 15.00,
    },
    "claude-3-5-haiku-20241022": {
        "input": 1.00,
        "output": 5.00,
    },
    "claude-3-opus-20240229": {
        "input": 15.00,
        "output": 75.00,
    },
    "claude-3-sonnet-20240229": {
        "input": 3.00,
        "output": 15.00,
    },
    # OpenAI
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
    },
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00,
    },
    "gpt-4": {
        "input": 30.00,
        "output": 60.00,
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
    },
    # Google Gemini
    "gemini-2.0-flash-exp": {
        "input": 0.075,
        "output": 0.30,
    },
    "gemini-1.5-pro": {
        "input": 1.25,
        "output": 5.00,
    },
    "gemini-1.5-flash": {
        "input": 0.075,
        "output": 0.30,
    },
    # Default fallback (use average pricing)
    "default": {
        "input": 2.00,
        "output": 8.00,
    },
}


def get_model_pricing(model_id: Optional[str]) -> Tuple[float, float]:
    """
    Get pricing for a model (input/output per 1M tokens).

    Args:
        model_id: Model identifier (e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0")

    Returns:
        Tuple of (input_price, output_price) per 1M tokens
    """
    if not model_id:
        pricing = STRANDS_MODEL_PRICING["default"]
        return pricing["input"], pricing["output"]

    # Try exact match first
    if model_id in STRANDS_MODEL_PRICING:
        pricing = STRANDS_MODEL_PRICING[model_id]
        return pricing["input"], pricing["output"]

    # Try partial matches (for version variations)
    model_id_lower = model_id.lower()
    for key, pricing in STRANDS_MODEL_PRICING.items():
        if key.lower() in model_id_lower or model_id_lower in key.lower():
            return pricing["input"], pricing["output"]

    # Fallback to default
    pricing = STRANDS_MODEL_PRICING["default"]
    return pricing["input"], pricing["output"]


def calculate_strands_cost(
    model_id: Optional[str],
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> float:
    """
    Calculate cost for a Strands agent invocation.

    Args:
        model_id: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Total cost in USD
    """
    input_price, output_price = get_model_pricing(model_id)

    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price

    return input_cost + output_cost
