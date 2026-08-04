"""Token-to-USD cost estimator for LLM calls.

Pricing defaults to GPT-4o public list rates (2025) and can be overridden
via COST_INPUT_PER_1K_TOKENS and COST_OUTPUT_PER_1K_TOKENS env vars.
"""

from __future__ import annotations

from app.core.config import get_settings


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Return estimated USD cost rounded to 6 decimal places."""
    s = get_settings()
    cost = (prompt_tokens / 1000 * s.cost_input_per_1k_tokens) + (
        completion_tokens / 1000 * s.cost_output_per_1k_tokens
    )
    return round(cost, 6)
