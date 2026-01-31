# llama-index-tools-quercle

Quercle tools for LlamaIndex - AI-powered web fetch and search.

## Installation

```bash
pip install llama-index-tools-quercle
```

## Quick Start

### Using QuercleToolSpec (Recommended)

```python
from llama_index.tools.quercle import QuercleToolSpec
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI

# Create the tool spec
quercle = QuercleToolSpec(api_key="qk_...")  # Or set QUERCLE_API_KEY env var

# Get all tools and create an agent
agent = ReActAgent.from_tools(quercle.to_tool_list(), llm=OpenAI())

# Use the agent
response = agent.chat("Search for the latest Python news")
print(response)
```

### Using Standalone Tools

```python
from llama_index.tools.quercle import create_quercle_fetch_tool, create_quercle_search_tool

# Create individual tools
fetch_tool = create_quercle_fetch_tool(api_key="qk_...")
search_tool = create_quercle_search_tool(api_key="qk_...")

# Use directly
result = fetch_tool.call(url="https://example.com", prompt="Summarize this page")
result = search_tool.call(query="Python web frameworks")
```

### Direct Usage

```python
from llama_index.tools.quercle import QuercleToolSpec

quercle = QuercleToolSpec()

# Fetch and analyze a web page
content = quercle.fetch(
    url="https://docs.python.org/3/whatsnew/3.12.html",
    prompt="List the main new features"
)

# Search the web
results = quercle.search(
    query="best practices for Python async programming",
    allowed_domains=["python.org", "realpython.com"]
)
```

## Tools

### fetch

Fetch a web page and analyze its content using AI.

**Parameters:**
- `url` (str): The URL to fetch and analyze
- `prompt` (str): Instructions for how to analyze the page content

**Returns:** AI-processed analysis of the page content

### search

Search the web and get AI-synthesized answers with citations.

**Parameters:**
- `query` (str): The search query
- `allowed_domains` (list[str], optional): Only include results from these domains
- `blocked_domains` (list[str], optional): Exclude results from these domains

**Returns:** AI-synthesized answer with source citations

## Async Support

Both tools support async operations:

```python
import asyncio
from llama_index.tools.quercle import QuercleToolSpec

async def main():
    quercle = QuercleToolSpec()

    # Async fetch
    content = await quercle.afetch(
        url="https://example.com",
        prompt="Summarize this page"
    )

    # Async search
    results = await quercle.asearch(query="Python news")

asyncio.run(main())
```

## Configuration

### API Key

Set your Quercle API key either:

1. Pass directly: `QuercleToolSpec(api_key="qk_...")`
2. Environment variable: `export QUERCLE_API_KEY=qk_...`

### Timeout

Configure request timeout in seconds:

```python
quercle = QuercleToolSpec(timeout=60.0)
```

## License

MIT
