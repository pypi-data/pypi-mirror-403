"""
Cost tracking for Claude Agent SDK.

Provides pricing information and cost calculation for Claude models.
"""

from typing import Dict, Optional

# Claude model pricing (per 1M tokens)
# Updated as of January 2025
CLAUDE_MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Claude 4 models
    "claude-opus-4-20250514": {
        "input": 15.00,
        "output": 75.00,
        "cache_read": 1.50,
        "cache_write": 18.75,
    },
    "claude-opus-4": {
        "input": 15.00,
        "output": 75.00,
        "cache_read": 1.50,
        "cache_write": 18.75,
    },
    "claude-sonnet-4-20250514": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_write": 3.75,
    },
    "claude-sonnet-4": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_write": 3.75,
    },
    # Claude 3.5 models
    "claude-3-5-sonnet-20241022": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_write": 3.75,
    },
    "claude-3-5-sonnet-latest": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_write": 3.75,
    },
    "claude-3-5-haiku-20241022": {
        "input": 1.00,
        "output": 5.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
    },
    "claude-3-5-haiku-latest": {
        "input": 1.00,
        "output": 5.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
    },
    # Claude 3 models
    "claude-3-opus-20240229": {
        "input": 15.00,
        "output": 75.00,
        "cache_read": 1.50,
        "cache_write": 18.75,
    },
    "claude-3-opus-latest": {
        "input": 15.00,
        "output": 75.00,
        "cache_read": 1.50,
        "cache_write": 18.75,
    },
    "claude-3-sonnet-20240229": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_write": 3.75,
    },
    "claude-3-haiku-20240307": {
        "input": 0.25,
        "output": 1.25,
        "cache_read": 0.03,
        "cache_write": 0.30,
    },
}

# Aliases for common model names
MODEL_ALIASES: Dict[str, str] = {
    "claude-4-opus": "claude-opus-4-20250514",
    "claude-4-sonnet": "claude-sonnet-4-20250514",
    "claude-4": "claude-sonnet-4-20250514",
    "claude-3.5-sonnet": "claude-3-5-sonnet-20241022",
    "claude-3.5-haiku": "claude-3-5-haiku-20241022",
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-haiku": "claude-3-haiku-20240307",
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-20250514",
    "haiku": "claude-3-5-haiku-20241022",
}


def get_model_pricing(model: str) -> Optional[Dict[str, float]]:
    """
    Get pricing for a Claude model.

    Args:
        model: Model name or alias

    Returns:
        Pricing dict with input/output/cache_read/cache_write rates per 1M tokens,
        or None if model not found
    """
    # Check aliases first
    resolved_model = MODEL_ALIASES.get(model, model)

    # Direct lookup
    if resolved_model in CLAUDE_MODEL_PRICING:
        return CLAUDE_MODEL_PRICING[resolved_model]

    # Try partial matching
    for model_key in CLAUDE_MODEL_PRICING:
        if model_key in resolved_model or resolved_model in model_key:
            return CLAUDE_MODEL_PRICING[model_key]

    return None


def calculate_claude_cost(
    model: str,
    usage: Dict[str, int],
    pricing: Optional[Dict[str, float]] = None,
) -> float:
    """
    Calculate cost for Claude API usage.

    Args:
        model: Model name or alias
        usage: Usage dict with:
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - cache_read_input_tokens: Tokens read from cache (optional)
            - cache_creation_input_tokens: Tokens written to cache (optional)
        pricing: Optional custom pricing dict (uses default if not provided)

    Returns:
        Total cost in USD
    """
    if pricing is None:
        pricing = get_model_pricing(model)

    if pricing is None:
        # Use default Claude 3.5 Sonnet pricing if model not found
        pricing = CLAUDE_MODEL_PRICING.get("claude-3-5-sonnet-20241022", {
            "input": 3.00,
            "output": 15.00,
            "cache_read": 0.30,
            "cache_write": 3.75,
        })

    # Calculate cost per million tokens
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cache_read_tokens = usage.get("cache_read_input_tokens", 0)
    cache_creation_tokens = usage.get("cache_creation_input_tokens", 0)

    cost = 0.0

    # Input tokens (excluding cache read tokens which are cheaper)
    regular_input_tokens = max(0, input_tokens - cache_read_tokens)
    cost += (regular_input_tokens / 1_000_000) * pricing.get("input", 0)

    # Output tokens
    cost += (output_tokens / 1_000_000) * pricing.get("output", 0)

    # Cache read tokens (cheaper rate)
    cost += (cache_read_tokens / 1_000_000) * pricing.get("cache_read", 0)

    # Cache creation tokens (premium rate)
    cost += (cache_creation_tokens / 1_000_000) * pricing.get("cache_write", 0)

    return cost


def estimate_cost(
    model: str,
    input_text: str,
    estimated_output_tokens: int = 500,
) -> float:
    """
    Estimate cost for a Claude API call.

    This is a rough estimate using character count / 4 for input tokens.

    Args:
        model: Model name or alias
        input_text: Input text to estimate
        estimated_output_tokens: Expected output tokens (default 500)

    Returns:
        Estimated cost in USD
    """
    # Rough estimate: ~4 characters per token
    estimated_input_tokens = len(input_text) // 4

    return calculate_claude_cost(model, {
        "input_tokens": estimated_input_tokens,
        "output_tokens": estimated_output_tokens,
    })
