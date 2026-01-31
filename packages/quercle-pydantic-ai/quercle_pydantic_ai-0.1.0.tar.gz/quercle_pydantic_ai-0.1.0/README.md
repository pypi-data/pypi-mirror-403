# quercle-pydantic-ai

Quercle web search and URL fetch tools for [Pydantic AI](https://ai.pydantic.dev/) agents.

## Installation

```bash
uv add quercle-pydantic-ai
```

Or with pip:

```bash
pip install quercle-pydantic-ai
```

## Quick Start

```python
from pydantic_ai import Agent
from quercle_pydantic_ai import quercle_tools

# Create an agent with Quercle tools
agent = Agent(
    'openai:gpt-4o',
    tools=quercle_tools(),
)

# Run the agent
result = agent.run_sync("Search for the latest Python 3.13 features")
print(result.data)
```

## Configuration

### API Key

Set your Quercle API key via environment variable:

```bash
export QUERCLE_API_KEY=qk_your_api_key
```

Or pass it directly:

```python
from quercle_pydantic_ai import quercle_tools

tools = quercle_tools(api_key="qk_your_api_key")
```

Get your API key at [quercle.dev](https://quercle.dev).

## Usage

### Individual Tools

Use search or fetch tools separately:

```python
from pydantic_ai import Agent
from quercle_pydantic_ai import quercle_search_tool, quercle_fetch_tool

# Search-only agent
search_agent = Agent(
    'openai:gpt-4o',
    tools=[quercle_search_tool()],
)

# Fetch-only agent
fetch_agent = Agent(
    'openai:gpt-4o',
    tools=[quercle_fetch_tool()],
)
```

### Domain Filtering

Restrict search to specific domains:

```python
from quercle_pydantic_ai import quercle_search_tool

# Only search official documentation sites
tool = quercle_search_tool(
    allowed_domains=["*.python.org", "docs.*.dev"],
)

# Exclude certain domains
tool = quercle_search_tool(
    blocked_domains=["reddit.com", "*.social"],
)
```

### QuercleToolset

Use the toolset for composition with other Pydantic AI toolsets:

```python
from pydantic_ai import Agent
from pydantic_ai.toolsets import CombinedToolset
from quercle_pydantic_ai import QuercleToolset

# Create a Quercle toolset
quercle = QuercleToolset(
    search_allowed_domains=["*.org", "*.edu"],
)

# Combine with other toolsets
combined = CombinedToolset([quercle, other_toolset])

agent = Agent('openai:gpt-4o', toolsets=[combined])
```

Configure which tools to include:

```python
# Search only
toolset = QuercleToolset(include_fetch=False)

# Fetch only
toolset = QuercleToolset(include_search=False)
```

## Examples

### Research Agent

```python
from pydantic_ai import Agent
from quercle_pydantic_ai import quercle_tools

agent = Agent(
    'openai:gpt-4o',
    tools=quercle_tools(),
    system_prompt="""You are a research assistant. Use web search to find
    accurate, up-to-date information. Always cite your sources.""",
)

result = agent.run_sync(
    "What are the key differences between Python 3.12 and 3.13?"
)
print(result.data)
```

### Web Analyzer Agent

```python
from pydantic_ai import Agent
from quercle_pydantic_ai import quercle_fetch_tool

agent = Agent(
    'openai:gpt-4o',
    tools=[quercle_fetch_tool()],
    system_prompt="""You analyze web pages and extract key information.
    When given a URL, fetch it and provide a structured summary.""",
)

result = agent.run_sync(
    "Analyze the documentation at https://ai.pydantic.dev/tools/"
)
print(result.data)
```

### Async Usage

```python
import asyncio
from pydantic_ai import Agent
from quercle_pydantic_ai import quercle_tools

agent = Agent('openai:gpt-4o', tools=quercle_tools())

async def main():
    result = await agent.run("Search for async Python best practices")
    print(result.data)

asyncio.run(main())
```

## API Reference

### Factory Functions

#### `quercle_search_tool()`

Creates a web search tool.

```python
def quercle_search_tool(
    api_key: str | None = None,
    allowed_domains: list[str] | None = None,
    blocked_domains: list[str] | None = None,
    timeout: float | None = None,
) -> Tool[Any]
```

#### `quercle_fetch_tool()`

Creates a URL fetch tool.

```python
def quercle_fetch_tool(
    api_key: str | None = None,
    timeout: float | None = None,
) -> Tool[Any]
```

#### `quercle_tools()`

Creates both search and fetch tools.

```python
def quercle_tools(
    api_key: str | None = None,
    timeout: float | None = None,
) -> list[Tool[Any]]
```

### QuercleToolset

A composable toolset for use with Pydantic AI's toolset system.

```python
class QuercleToolset(FunctionToolset):
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float | None = None,
        *,
        include_search: bool = True,
        include_fetch: bool = True,
        search_allowed_domains: list[str] | None = None,
        search_blocked_domains: list[str] | None = None,
    )
```

## License

MIT
