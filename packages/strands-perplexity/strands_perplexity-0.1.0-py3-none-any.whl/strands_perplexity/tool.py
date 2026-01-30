"""Perplexity Search API Tool for Strands Agents.

This module provides a tool for performing web searches using the Perplexity Search API,
allowing Strands Agents to access real-time web search results with citations.
"""

import logging
import os
from typing import Any, Optional

import httpx
from strands import tool

logger = logging.getLogger(__name__)

# API configuration
PERPLEXITY_API_URL = "https://api.perplexity.ai/search"
DEFAULT_MAX_RESULTS = 5
DEFAULT_MAX_TOKENS_PER_PAGE = 2048
DEFAULT_MAX_TOKENS = 25000


class PerplexitySearchError(Exception):
    """Custom exception for Perplexity Search API errors."""

    pass


def _get_api_key() -> str:
    """Get the Perplexity API key from environment variables.

    Returns:
        The API key string.

    Raises:
        PerplexitySearchError: If the API key is not set.
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise PerplexitySearchError(
            "PERPLEXITY_API_KEY environment variable is not set. Please set it to your Perplexity API key."
        )
    return api_key


def _make_search_request(
    query: str | list[str],
    max_results: int,
    max_tokens_per_page: int,
    max_tokens: int,
    search_domain_filter: Optional[list[str]],
    search_language_filter: Optional[list[str]],
    country: Optional[str],
) -> dict[str, Any]:
    """Make a request to the Perplexity Search API.

    Args:
        query: The search query or list of queries.
        max_results: Maximum number of results to return.
        max_tokens_per_page: Maximum tokens to extract per page.
        max_tokens: Maximum total tokens across all results.
        search_domain_filter: List of domains to include or exclude.
        search_language_filter: List of language codes to filter by.
        country: ISO country code for regional search.

    Returns:
        The API response as a dictionary.

    Raises:
        PerplexitySearchError: If the API request fails.
    """
    api_key = _get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {
        "query": query,
        "max_results": max_results,
        "max_tokens_per_page": max_tokens_per_page,
        "max_tokens": max_tokens,
    }

    # Add optional parameters if provided
    if search_domain_filter:
        payload["search_domain_filter"] = search_domain_filter

    if search_language_filter:
        payload["search_language_filter"] = search_language_filter

    if country:
        payload["country"] = country

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(PERPLEXITY_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
    except httpx.HTTPStatusError as e:
        error_message = f"Perplexity API request failed with status {e.response.status_code}"
        try:
            error_detail = e.response.json()
            error_message += f": {error_detail}"
        except Exception:
            error_message += f": {e.response.text}"
        logger.error(error_message)
        raise PerplexitySearchError(error_message) from e
    except httpx.RequestError as e:
        error_message = f"Network error while calling Perplexity API: {str(e)}"
        logger.error(error_message)
        raise PerplexitySearchError(error_message) from e


def _format_results(api_response: dict[str, Any], query: str | list[str]) -> dict[str, Any]:
    """Format the API response into a structured result.

    Args:
        api_response: The raw API response.
        query: The original search query.

    Returns:
        A formatted dictionary with search results and citations.
    """
    results = api_response.get("results", [])
    search_id = api_response.get("id", "")

    formatted_results: list[Any] = []

    # Handle both single query (flat list) and multi-query (nested list) responses
    if results and isinstance(results[0], list):
        # Multi-query response - results are nested
        for query_results in results:
            query_formatted: list[dict[str, Any]] = []
            for result in query_results:
                query_formatted.append(_format_single_result(result))
            formatted_results.append(query_formatted)
    else:
        # Single query response - flat list
        for result in results:
            formatted_results.append(_format_single_result(result))

    return {
        "query": query,
        "search_id": search_id,
        "results": formatted_results,
        "result_count": (
            len(results) if not (results and isinstance(results[0], list)) else sum(len(r) for r in results)
        ),
    }


def _format_single_result(result: dict[str, Any]) -> dict[str, Any]:
    """Format a single search result.

    Args:
        result: A single result from the API.

    Returns:
        A formatted result dictionary.
    """
    return {
        "title": result.get("title", ""),
        "url": result.get("url", ""),
        "snippet": result.get("snippet", ""),
        "date": result.get("date"),
        "last_updated": result.get("last_updated"),
    }


@tool
def perplexity_search(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    max_tokens_per_page: int = DEFAULT_MAX_TOKENS_PER_PAGE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    search_domain_filter: Optional[list[str]] = None,
    search_language_filter: Optional[list[str]] = None,
    country: Optional[str] = None,
) -> dict[str, Any]:
    """Search the web using Perplexity's Search API.

    This tool provides real-time access to ranked web search results with advanced filtering
    capabilities. It returns structured results with titles, URLs, snippets, and dates.

    Args:
        query: The search query string. Be specific for better results.
            Example: "artificial intelligence medical diagnosis accuracy 2024"
        max_results: Maximum number of results to return (1-20, default 5).
        max_tokens_per_page: Maximum tokens to extract from each webpage (default 2048).
            Higher values provide more comprehensive content but may increase processing time.
        max_tokens: Maximum total tokens of webpage content across all results (default 25000).
            This controls the total content budget for snippets.
        search_domain_filter: Optional list of domains to filter results.
            - For allowlist (include only): ["science.org", "nature.com"]
            - For denylist (exclude): ["-pinterest.com", "-reddit.com"]
            Note: Cannot mix allowlist and denylist in the same request. Max 20 domains.
        search_language_filter: Optional list of ISO 639-1 language codes to filter by.
            Example: ["en", "fr", "de"] for English, French, and German results. Max 10 codes.
        country: Optional ISO 3166-1 alpha-2 country code for regional search.
            Example: "US", "GB", "DE", "JP"

    Returns:
        Dict containing:
            - query: The original search query
            - search_id: Unique identifier for this search
            - results: List of search results, each with:
                - title: Page title
                - url: Page URL (citation source)
                - snippet: Extracted content from the page
                - date: Publication date (if available)
                - last_updated: Last update date (if available)
            - result_count: Total number of results returned

    Raises:
        PerplexitySearchError: If the API key is not set or the request fails.

    Examples:
        Basic search:
            perplexity_search(query="latest AI developments 2024")

        Search with domain filter:
            perplexity_search(
                query="climate change research",
                search_domain_filter=["science.org", "nature.com"]
            )

        Regional search:
            perplexity_search(
                query="government policies on renewable energy",
                country="US"
            )
    """
    logger.info(f"Performing Perplexity search for query: {query}")

    try:
        api_response = _make_search_request(
            query=query,
            max_results=max_results,
            max_tokens_per_page=max_tokens_per_page,
            max_tokens=max_tokens,
            search_domain_filter=search_domain_filter,
            search_language_filter=search_language_filter,
            country=country,
        )

        formatted_response = _format_results(api_response, query)
        logger.info(f"Search completed with {formatted_response['result_count']} results")

        return formatted_response

    except PerplexitySearchError:
        raise
    except Exception as e:
        error_message = f"Unexpected error during Perplexity search: {str(e)}"
        logger.error(error_message)
        raise PerplexitySearchError(error_message) from e


@tool
def perplexity_multi_search(
    queries: list[str],
    max_results: int = DEFAULT_MAX_RESULTS,
    max_tokens_per_page: int = DEFAULT_MAX_TOKENS_PER_PAGE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    search_domain_filter: Optional[list[str]] = None,
    search_language_filter: Optional[list[str]] = None,
    country: Optional[str] = None,
) -> dict[str, Any]:
    """Execute multiple search queries in a single request for comprehensive research.

    This tool allows you to search for multiple related topics at once, which is ideal
    for research tasks where you need to explore different angles of a subject.

    Args:
        queries: List of search query strings (max 5 queries).
            Example: ["AI trends 2024", "machine learning breakthroughs", "AI in healthcare"]
        max_results: Maximum number of results per query (1-20, default 5).
        max_tokens_per_page: Maximum tokens to extract from each webpage (default 2048).
        max_tokens: Maximum total tokens across all results (default 25000).
        search_domain_filter: Optional list of domains to filter results.
            - For allowlist: ["arxiv.org", "nature.com"]
            - For denylist: ["-wikipedia.org"]
        search_language_filter: Optional list of ISO 639-1 language codes.
            Example: ["en"] for English only.
        country: Optional ISO 3166-1 alpha-2 country code for regional search.

    Returns:
        Dict containing:
            - queries: The original list of search queries
            - search_id: Unique identifier for this search
            - results: Nested list of results, grouped by query in the same order
            - result_count: Total number of results across all queries

    Raises:
        PerplexitySearchError: If the API key is not set or the request fails.
        ValueError: If more than 5 queries are provided.

    Examples:
        Multi-query research:
            perplexity_multi_search(
                queries=[
                    "artificial intelligence trends 2024",
                    "machine learning breakthroughs recent",
                    "AI applications in healthcare"
                ]
            )
    """
    if len(queries) > 5:
        raise ValueError("Maximum of 5 queries allowed per multi-query request")

    if not queries:
        raise ValueError("At least one query is required")

    logger.info(f"Performing Perplexity multi-search for {len(queries)} queries")

    try:
        api_response = _make_search_request(
            query=queries,
            max_results=max_results,
            max_tokens_per_page=max_tokens_per_page,
            max_tokens=max_tokens,
            search_domain_filter=search_domain_filter,
            search_language_filter=search_language_filter,
            country=country,
        )

        formatted_response = _format_results(api_response, queries)
        # Rename 'query' to 'queries' for multi-search response
        formatted_response["queries"] = formatted_response.pop("query")

        logger.info(f"Multi-search completed with {formatted_response['result_count']} total results")

        return formatted_response

    except PerplexitySearchError:
        raise
    except Exception as e:
        error_message = f"Unexpected error during Perplexity multi-search: {str(e)}"
        logger.error(error_message)
        raise PerplexitySearchError(error_message) from e
