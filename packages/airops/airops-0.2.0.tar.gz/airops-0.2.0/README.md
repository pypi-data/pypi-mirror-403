# AirOps Python SDK

Build custom tools that integrate with AirOps' Steps API.

## Installation

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
pip install airops
```

## Quick Start

### Prerequisites

**Docker** is required for building and deploying tools.

Install Docker:
- **macOS/Windows**: Download [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux**: Install via your package manager:
  ```bash
  # Debian/Ubuntu
  sudo apt-get update && sudo apt-get install docker.io

  # Fedora
  sudo dnf install docker

  # Arch
  sudo pacman -S docker
  ```

After installation, verify Docker is running:
```bash
docker --version
```

### Create a Tool

Create a new tool project:

```bash
airops init my-tool
cd my-tool
cp .env.example .env  # add your AIROPS_API_TOKEN
airops run
```

This creates a ready-to-run project with:
- `tool.py` - Example tool implementation
- `Dockerfile` - Container image for deployment
- `.env.example` - Environment variable template
- `tests/` - Example test suite

## Example

```python
from pydantic import Field
from airops import Tool, ToolOutputs, steps
from airops.inputs import ToolInputs, ShortText, Number


class Inputs(ToolInputs):
    url: ShortText = Field(..., description="Domain or URL to search")
    limit: Number = Field(default=5, description="Maximum results")


class Outputs(ToolOutputs):
    results: list[dict]


tool = Tool(
    name="keyword_extractor",
    description="Extract keywords from a URL using Google Search",
    input_model=Inputs,
    output_model=Outputs,
)


@tool.handler
async def run(inputs: Inputs) -> Outputs:
    # Call AirOps Steps API
    serp = await steps.execute(
        "google_search",
        {"query": f"site:{inputs.url}", "limit": inputs.limit},
    )
    return Outputs(results=serp["results"])


if __name__ == "__main__":
    tool.serve()
```

## Input Types

Use AirOps input types for workflow-compatible schemas:

```python
from airops.inputs import (
    ToolInputs,     # Base class for inputs (required)
    ShortText,      # Single-line text (str)
    LongText,       # Multi-line text (str)
    Number,         # Numeric value (int | float)
    Json,           # JSON value (dict, list, primitives)
    SingleSelect,   # Single choice from options
    MultiSelect,    # Multiple choices from options
    KnowledgeBase,  # Knowledge base ID (int)
    Brandkit,       # Brandkit ID (int)
    Database,       # Database ID (int)
)

class Inputs(ToolInputs):
    query: ShortText = Field(..., description="Search query")
    context: LongText = Field(default="", description="Additional context")
    limit: Number = Field(default=10)
    format: SingleSelect("json", "csv", "xml") = Field(default="json")
    tags: MultiSelect("urgent", "important") = Field(default=[])
    kb_id: KnowledgeBase = Field(..., description="Knowledge base to use")
```

Get the AirOps workflow schema:

```python
print(tool.airops_inputs_schema)
# [{"name": "query", "interface": "short_text", "label": "Query", ...}, ...]
```

## Configuration

Set the following environment variables:

```bash
# Required
export AIROPS_API_TOKEN="your-api-token"

# Optional
export AIROPS_API_BASE_URL="https://api.airops.com"  # default
export AIROPS_DEFAULT_TIMEOUT_S="7200"               # 2 hours default
export AIROPS_POLL_INTERVAL_S="2.0"                  # default
```

## MCP Integration

The AirOps MCP provides tools for discovering available steps, schemas, and workspace secrets.

To use the MCP you will have to configure it with your workspace API key, which can be found in the AirOps app under `Settings -> Workspace -> API KEY`

### Claude Desktop

```bash
claude mcp add --transport http airops-sdk-mcp https://app.airops.com/internal_api/sdk/mcp --header "Authorization: Bearer <YOUR_WORKSPACE_TOKEN>"
```

### Cursor

Add to your `mcp.json` file in Cursor Settings:

```json
{
  "mcpServers": {
    "airops-sdk-mcp": {
      "url": "https://app.airops.com/internal_api/sdk/mcp",
      "headers": {
        "Authorization": "Bearer <YOUR_WORKSPACE_TOKEN>"
      }
    }
  }
}
```

The MCP exposes:
- Step discovery and search
- Input/output schema inspection
- Workspace secrets listing
- Tool building guidance at `/airops-internal/tool_building_prompt`

## Usage

### Running Locally

```bash
uv run tool.py
```

This starts a local server with:
- **API**: `http://localhost:8080/runs` - Start and poll tool executions
- **UI**: `http://localhost:8080/` - Browser-based testing interface

### Using the Steps API

```python
from airops import steps

# Execute a step and wait for completion
result = await steps.execute("google_search", {"query": "airops"})

# Or use start/poll for more control
handle = await steps.start("google_search", {"query": "airops"})
status = await steps.poll(handle.step_execution_id)
```

### Tool Runtime API

#### Start a run
```http
POST /runs
Content-Type: application/json

{"inputs": {"url": "example.com"}}
```

Response (202):
```json
{"run_id": "...", "status": "queued"}
```

#### Poll run status
```http
GET /runs/{run_id}
```

Response:
```json
{
  "run_id": "...",
  "status": "success",
  "outputs": {"results": [...]}
}
```

## Publishing to AirOps

Deploy your tool to AirOps for production use:

```bash
airops publish
```

Options:
- `--name`: Override tool name (default: from tool.py)
- `--description`: Override description (default: from tool.py)
- `--timeout`: Deployment timeout in seconds (default: 600)

The command:
1. Validates tool.py and Dockerfile exist
2. Runs type checks with mypy
3. Builds and exports Docker image
4. Uploads to AirOps
5. Monitors deployment until active

## Error Handling

```python
from airops import steps
from airops.errors import (
    AiropsError,
    AuthError,
    InvalidInputError,
    RateLimitedError,
    StepFailedError,
    StepTimeoutError,
    UpstreamUnavailableError,
)

try:
    result = await steps.execute("some_step", inputs)
except StepTimeoutError:
    print("Step timed out")
except StepFailedError as e:
    print(f"Step failed: {e.error_details}")
except AiropsError as e:
    print(f"AirOps error: {e}")
```

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Type checking
uv run mypy src/airops

# Linting
uv run ruff check src/airops
```

## Using custom tools with agents
The custom tools built and published with the AirOps SDK can be used through the Tool Execution MCP server. This MCP server also requires setting it up with your workspace token and will discover all published tools and serve them as MCP tools your agent can use.

### Claude Desktop

```bash
claude mcp add --transport http airops-tools-mcp https://app.airops.com/internal_api/tools/mcp --header "Authorization: Bearer <YOUR_WORKSPACE_TOKEN>"
```

### Cursor

Add to your `mcp.json` file in Cursor Settings:

```json
{
  "mcpServers": {
    "airops-tools-mcp": {
      "url": "https://app.airops.com/internal_api/tools/mcp",
      "headers": {
        "Authorization": "Bearer <YOUR_WORKSPACE_TOKEN>"
      }
    }
  }
}
```