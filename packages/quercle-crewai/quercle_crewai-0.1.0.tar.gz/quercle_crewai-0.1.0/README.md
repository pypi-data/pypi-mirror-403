# quercle-crewai

CrewAI tools for [Quercle](https://quercle.dev) web search and URL fetching.

## Installation

```bash
uv add quercle-crewai
```

Or with pip:

```bash
pip install quercle-crewai
```

## Quick Start

```python
from quercle_crewai import QuercleSearchTool, QuercleFetchTool

# Initialize tools (uses QUERCLE_API_KEY env var by default)
search = QuercleSearchTool()
fetch = QuercleFetchTool()

# Or with explicit API key
search = QuercleSearchTool(api_key="qk_...")
fetch = QuercleFetchTool(api_key="qk_...")
```

## Standalone Tool Usage

Use the tools directly without any agent:

### Search

```python
from quercle_crewai import QuercleSearchTool

search = QuercleSearchTool()

# Basic search
result = search.run(query="What is TypeScript?")
print(result)

# With domain filtering
result = search.run(
    query="machine learning tutorials",
    allowed_domains=["*.edu", "*.org"],
    blocked_domains=["ads.com"],
)
```

### Fetch

```python
from quercle_crewai import QuercleFetchTool

fetch = QuercleFetchTool()

result = fetch.run(
    url="https://docs.python.org/3/whatsnew/3.12.html",
    prompt="Summarize the key new features in bullet points",
)
print(result)
```

## Usage with CrewAI Agents

### Basic Agent Setup

```python
from crewai import Agent, Task, Crew
from quercle_crewai import QuercleSearchTool, QuercleFetchTool

# Initialize tools
search_tool = QuercleSearchTool()
fetch_tool = QuercleFetchTool()

# Create an agent with Quercle tools
researcher = Agent(
    role="Research Analyst",
    goal="Find and analyze information from the web",
    backstory="You are an expert researcher who finds accurate information.",
    tools=[search_tool, fetch_tool],
    verbose=True,
)

# Create a task
research_task = Task(
    description="Research the latest features in Python 3.13 and summarize them.",
    expected_output="A summary of Python 3.13 features with key highlights.",
    agent=researcher,
)

# Run the crew
crew = Crew(
    agents=[researcher],
    tasks=[research_task],
    verbose=True,
)

result = crew.kickoff()
print(result)
```

### Multi-Agent Example

```python
from crewai import Agent, Task, Crew
from quercle_crewai import QuercleSearchTool, QuercleFetchTool

# Tools
search_tool = QuercleSearchTool()
fetch_tool = QuercleFetchTool()

# Research agent - finds information
researcher = Agent(
    role="Web Researcher",
    goal="Find relevant information from the web",
    backstory="Expert at finding and extracting information from web sources.",
    tools=[search_tool, fetch_tool],
)

# Writer agent - synthesizes information
writer = Agent(
    role="Content Writer",
    goal="Write clear and engaging content based on research",
    backstory="Skilled writer who creates well-structured content.",
)

# Tasks
research_task = Task(
    description="Research the benefits and challenges of remote work in 2024.",
    expected_output="Detailed research findings with sources.",
    agent=researcher,
)

writing_task = Task(
    description="Write a blog post based on the research findings.",
    expected_output="A well-written blog post about remote work.",
    agent=writer,
    context=[research_task],
)

# Create and run crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    verbose=True,
)

result = crew.kickoff()
```

## Configuration

### Environment Variable

Set your API key as an environment variable:

```bash
export QUERCLE_API_KEY=qk_your_api_key_here
```

### Tool Parameters

Both tools accept these optional parameters:

- `api_key`: Your Quercle API key (falls back to `QUERCLE_API_KEY` env var)
- `timeout`: Request timeout in seconds

```python
tool = QuercleSearchTool(
    api_key="qk_...",
    timeout=60.0,
)
```

## Tool Descriptions

### QuercleSearchTool

- **Name**: `quercle_search`
- **Description**: Search the web and get AI-synthesized answers with citations
- **Arguments**:
  - `query` (required): The search query
  - `allowed_domains` (optional): List of domains to include (e.g., `["*.edu"]`)
  - `blocked_domains` (optional): List of domains to exclude

### QuercleFetchTool

- **Name**: `quercle_fetch`
- **Description**: Fetch a URL and analyze its content with AI
- **Arguments**:
  - `url` (required): The URL to fetch
  - `prompt` (required): Instructions for content analysis

## License

MIT
