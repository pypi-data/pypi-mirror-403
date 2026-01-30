# Strands Perplexity

A [Strands Agents](https://github.com/strands-agents/sdk-python) tool for performing real-time web searches using the [Perplexity Search API](https://docs.perplexity.ai/guides/search-quickstart).

## Features

- 🔍 **Real-time web search** - Access ranked web search results from Perplexity's continuously refreshed index
- 📝 **Citations included** - Every result includes URLs for proper attribution
- 🌍 **Regional search** - Filter results by country using ISO country codes
- 🔤 **Language filtering** - Filter results by language using ISO 639-1 codes
- 🌐 **Domain filtering** - Include or exclude specific domains from results
- 📊 **Multi-query support** - Execute up to 5 related queries in a single request

## Installation

```bash
pip install strands-perplexity
```

## Configuration

Set your Perplexity API key as an environment variable:

```bash
export PERPLEXITY_API_KEY="your_api_key_here"
```

You can get an API key from the [Perplexity API Settings](https://perplexity.ai/account/api).

## Usage

### Basic Usage with Strands Agent

```python
from strands import Agent
from strands_perplexity import perplexity_search

# Create an agent with the Perplexity search tool
agent = Agent(tools=[perplexity_search])

# The agent can now search the web
response = agent("What are the latest developments in AI?")
print(response)
```

### Direct Tool Usage

```python
from strands_perplexity import perplexity_search, perplexity_multi_search

# Basic search
results = perplexity_search(query="artificial intelligence trends 2024")
for result in results["results"]:
    print(f"{result['title']}: {result['url']}")

# Search with domain filter (allowlist)
results = perplexity_search(
    query="climate change research",
    search_domain_filter=["science.org", "nature.com", "cell.com"],
    max_results=10
)

# Search with domain filter (denylist)
results = perplexity_search(
    query="renewable energy innovations",
    search_domain_filter=["-pinterest.com", "-reddit.com", "-quora.com"]
)

# Regional search
results = perplexity_search(
    query="government policies on renewable energy",
    country="US",
    max_results=5
)

# Language-filtered search
results = perplexity_search(
    query="latest AI news",
    search_language_filter=["en", "fr", "de"]
)

# Multi-query search for comprehensive research
results = perplexity_multi_search(
    queries=[
        "artificial intelligence trends 2024",
        "machine learning breakthroughs recent",
        "AI applications in healthcare"
    ],
    max_results=5
)
```

## API Reference

### `perplexity_search`

Search the web using Perplexity's Search API.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | Required | The search query string |
| `max_results` | `int` | `5` | Maximum results to return (1-20) |
| `max_tokens_per_page` | `int` | `2048` | Maximum tokens to extract per webpage |
| `max_tokens` | `int` | `25000` | Maximum total tokens across all results |
| `search_domain_filter` | `list[str]` | `None` | Domains to include or exclude (max 20) |
| `search_language_filter` | `list[str]` | `None` | ISO 639-1 language codes (max 10) |
| `country` | `str` | `None` | ISO 3166-1 alpha-2 country code |

**Returns:**

```python
{
    "query": "your search query",
    "search_id": "unique-search-id",
    "results": [
        {
            "title": "Page Title",
            "url": "https://example.com/page",
            "snippet": "Extracted content from the page...",
            "date": "2024-01-15",
            "last_updated": "2024-01-20"
        },
        # ... more results
    ],
    "result_count": 5
}
```

### `perplexity_multi_search`

Execute multiple search queries in a single request.

**Parameters:**

Same as `perplexity_search`, except:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `queries` | `list[str]` | Required | List of search queries (max 5) |

**Returns:**

```python
{
    "queries": ["query1", "query2", "query3"],
    "search_id": "unique-search-id",
    "results": [
        [  # Results for query1
            {"title": "...", "url": "...", "snippet": "..."},
            # ...
        ],
        [  # Results for query2
            {"title": "...", "url": "...", "snippet": "..."},
            # ...
        ],
        # ...
    ],
    "result_count": 15  # Total across all queries
}
```

## Domain Filtering

The `search_domain_filter` parameter supports two modes:

### Allowlist Mode (include only specified domains)

```python
results = perplexity_search(
    query="AI research",
    search_domain_filter=["arxiv.org", "openai.com", "deepmind.com"]
)
```

### Denylist Mode (exclude specified domains)

Use a `-` prefix to exclude domains:

```python
results = perplexity_search(
    query="AI news",
    search_domain_filter=["-pinterest.com", "-facebook.com"]
)
```

**Note:** You cannot mix allowlist and denylist modes in the same request.

## Best Practices

1. **Write specific queries** - Use detailed queries with context for better results:
   ```python
   # Better
   perplexity_search(query="artificial intelligence medical diagnosis accuracy 2024")
   
   # Avoid
   perplexity_search(query="AI medical")
   ```

2. **Use multi-query for research** - When exploring a topic, use related queries:
   ```python
   perplexity_multi_search(queries=[
       "quantum computing current state 2024",
       "quantum computing practical applications",
       "quantum computing vs classical computing advantages"
   ])
   ```

3. **Adjust token budgets** - Use lower `max_tokens_per_page` for quick lookups:
   ```python
   # Quick lookup
   perplexity_search(query="Python release date", max_tokens_per_page=512)
   
   # Deep research
   perplexity_search(query="Python GIL removal proposal", max_tokens_per_page=2048)
   ```

## Error Handling

```python
from strands_perplexity import perplexity_search, PerplexitySearchError

try:
    results = perplexity_search(query="AI news")
except PerplexitySearchError as e:
    print(f"Search failed: {e}")
```

Common errors:
- Missing `PERPLEXITY_API_KEY` environment variable
- API rate limits exceeded
- Invalid parameters (e.g., more than 5 queries in multi-search)

## Development

### Setup

```bash
git clone https://github.com/mkmeral/strands-perplexity
cd strands-perplexity
pip install -e ".[dev]"
```

### Running Tests

```bash
hatch run test
```

### Running All Checks

```bash
hatch run prepare  # Runs format, lint, typecheck, and test
```

## License

Apache 2.0 - see [LICENSE](LICENSE) for details.

## Resources

- [Perplexity Search API Documentation](https://docs.perplexity.ai/guides/search-quickstart)
- [Perplexity Search Best Practices](https://docs.perplexity.ai/guides/search-best-practices)
- [Strands Agents Documentation](https://strandsagents.com/)
- [Strands Agents SDK](https://github.com/strands-agents/sdk-python)
