# RaySurfer Python SDK

Drop-in replacement for Claude Agent SDK with automatic code caching.

## Installation

```bash
pip install raysurfer
```

## Setup

Set your API key:

```bash
export RAYSURFER_API_KEY=your_api_key_here
```

Get your key from the [dashboard](https://raysurfer.com/dashboard/api-keys).

## Usage

Swap your client class and method names. Options come directly from `claude_agent_sdk`:

```python
# Before
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

# After
from raysurfer import RaysurferClient
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],
    system_prompt="You are a helpful assistant.",
)

async with RaysurferClient(options) as client:
    await client.raysurfer_query("Generate quarterly report")
    async for msg in client.raysurfer_response():
        print(msg)
```

## Method Mapping

| Claude SDK | Raysurfer |
|------------|-----------|
| `ClaudeSDKClient(options)` | `RaysurferClient(options)` |
| `await client.query(prompt)` | `await client.raysurfer_query(prompt)` |
| `client.receive_response()` | `client.raysurfer_response()` |

## How It Works

1. **On `raysurfer_query()`**: Retrieves cached code blocks matching your task
2. **Downloads to sandbox**: Files ready for the agent to execute
3. **Injects into prompt**: Agent sees proven code snippets
4. **After success**: New code is cached for next time

Caching is enabled automatically when `RAYSURFER_API_KEY` is set.

## Snippet Retrieval Scope

Control which cached snippets are retrieved using `public_snips` and `snips_desired`:

```python
from raysurfer import RaysurferClient
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],
)

# Include both public and company snippets
client = RaysurferClient(
    options,
    public_snips=True,        # Include public/shared snippets
    snips_desired="company",  # Also include company-level snippets
)

# Enterprise: Retrieve client-specific snippets only
client = RaysurferClient(
    options,
    snips_desired="client",   # Client workspace snippets (Enterprise only)
)
```

| Configuration | Required Tier |
|--------------|---------------|
| `public_snips=True` only | FREE (default) |
| `snips_desired="company"` | TEAM or ENTERPRISE |
| `snips_desired="client"` | ENTERPRISE only |

## Full Example

```python
import asyncio
import os
from raysurfer import RaysurferClient
from claude_agent_sdk import ClaudeAgentOptions

os.environ["RAYSURFER_API_KEY"] = "your_api_key"

async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        system_prompt="You are a helpful assistant.",
    )

    async with RaysurferClient(options) as client:
        # First run: generates and caches code
        await client.raysurfer_query("Fetch GitHub trending repos")
        async for msg in client.raysurfer_response():
            print(msg)

        # Second run: retrieves from cache (instant)
        await client.raysurfer_query("Fetch GitHub trending repos")
        async for msg in client.raysurfer_response():
            print(msg)

asyncio.run(main())
```

## Without Caching

If `RAYSURFER_API_KEY` is not set, `RaysurferClient` behaves exactly like `ClaudeSDKClient` — no caching, just a pass-through wrapper.

## Low-Level API

For custom integrations, use the `RaySurfer` client directly with three core methods:

```python
from raysurfer import RaySurfer

client = RaySurfer(api_key="your_api_key")

# 1. Get cached code snippets for a task
snips = client.get_code_snips(task="Fetch GitHub trending repos")
for match in snips.code_blocks:
    print(f"{match.code_block.name}: {match.score}")

# 2. Upload new code snippets after execution
from raysurfer.types import FileWritten

files = [FileWritten(filename="fetch_repos.py", content="def fetch(): ...")]
client.upload_new_code_snips(
    task="Fetch GitHub trending repos",
    files_written=files,
    succeeded=True,
)

# 3. Vote on whether a cached snippet was useful
client.vote_code_snip(
    task="Fetch GitHub trending repos",
    code_block_id="abc123",
    code_block_name="github_fetcher",
    code_block_description="Fetches trending repos from GitHub",
    succeeded=True,
)
```

### Async Version

```python
from raysurfer import AsyncRaySurfer

async with AsyncRaySurfer(api_key="your_api_key") as client:
    snips = await client.get_code_snips(task="Fetch GitHub trending repos")
    await client.upload_new_code_snips(task, files, succeeded=True)
    await client.vote_code_snip(task, code_block_id, name, description, succeeded=True)
```

### Method Reference

| Method | Description |
|--------|-------------|
| `get_code_snips(task, top_k, min_verdict_score)` | Retrieve cached code snippets by semantic search |
| `upload_new_code_snips(task, files_written, succeeded)` | Store new code files for future reuse |
| `vote_code_snip(task, code_block_id, name, description, succeeded)` | Vote on snippet usefulness |

## License

MIT
