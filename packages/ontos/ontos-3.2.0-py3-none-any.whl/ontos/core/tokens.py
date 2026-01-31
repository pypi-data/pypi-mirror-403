"""
Token estimation utilities for context map generation.

Extracted from ontos_generate_context_map.py lines 71-102 during Phase 2 decomposition.
"""


def estimate_tokens(content: str) -> int:
    """Estimate token count using character-based heuristic.

    Uses ~4 characters per token (standard GPT approximation).

    Args:
        content: Text content to estimate

    Returns:
        Estimated token count
    """
    if not content:
        return 0
    return len(content) // 4


def format_token_count(tokens: int) -> str:
    """Format token count for display with thousand separators.

    Args:
        tokens: Token count to format

    Returns:
        Formatted string like "~2,500 tokens" or "~12k tokens"
    """
    if tokens < 1000:
        return f"~{tokens} tokens"
    elif tokens < 10000:
        return f"~{tokens:,} tokens"
    else:
        k = tokens // 1000
        return f"~{k}k tokens"
