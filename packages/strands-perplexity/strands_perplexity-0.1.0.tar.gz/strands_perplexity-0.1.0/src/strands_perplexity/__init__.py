"""Strands Perplexity Package.

This package provides tools for integrating Perplexity's Search API with Strands Agents,
enabling real-time web search capabilities with citations.
"""

from strands_perplexity.tool import (
    PerplexitySearchError,
    perplexity_multi_search,
    perplexity_search,
)

__all__ = [
    "perplexity_search",
    "perplexity_multi_search",
    "PerplexitySearchError",
]
