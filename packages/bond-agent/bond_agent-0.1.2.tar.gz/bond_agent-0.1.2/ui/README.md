# Bond UI

Forensic timeline viewer for Bond agent traces.

The timeline shows the agent's thought process as it works:
- **Thinking blocks** - The agent's internal reasoning (collapsible)
- **Text blocks** - Responses streamed to the user
- **Tool blocks** - Tool calls with arguments, execution status, and results

Click any block to inspect its full content in the side panel.

## Quick Start

```bash
pnpm install
pnpm dev
```

Open http://localhost:5173 and click **Run Demo** to see a pre-recorded agent session.

## Connect to a Live Agent

### Option 1: Using bond.server (Recommended)

The `bond.server` module provides a production-ready streaming server. Install with:

```bash
pip install bond-agent[server]
```

Create a server (`server.py`):

```python
import os
from bond import BondAgent
from bond.server import create_bond_server
from bond.tools import github_toolset, GitHubAdapter

# Create your agent
agent = BondAgent(
    name="assistant",
    instructions="You are a helpful assistant.",
    model="openai:gpt-4o",
    toolsets=[github_toolset],  # Optional: add tools
    deps=GitHubAdapter(token=os.environ.get("GITHUB_TOKEN")),
)

# Create ASGI app
app = create_bond_server(agent)
```

Run it:

```bash
uvicorn server:app --reload --port 8000
```

**Connecting the UI:**

The bond.server uses a 2-step flow:
1. `POST /ask` with `{"prompt": "..."}` → returns `{"session_id": "...", "stream_url": "/stream/..."}`
2. Connect SSE to the `stream_url`

To use with the UI's "Connect" button, create a simple wrapper endpoint:

```python
# Add to server.py - a convenience endpoint for the UI
from starlette.routing import Route
from starlette.responses import StreamingResponse
import json

async def ui_stream(request):
    """Single-step SSE endpoint for the Bond UI."""
    prompt = request.query_params.get("prompt", "Hello!")

    async def generate():
        async def send_sse(event: str, data: dict):
            yield f"event: {event}\ndata: {json.dumps(data)}\n\n"

        from bond.utils import create_sse_handlers
        handlers = create_sse_handlers(send_sse)
        await agent.ask(prompt, handlers=handlers)

    return StreamingResponse(generate(), media_type="text/event-stream")

# Add route to your app
app.routes.append(Route("/ui-stream", ui_stream))
```

Then click **Connect** in the UI and enter:
```
http://localhost:8000/ui-stream?prompt=What%20is%202%2B2
```

### Option 2: Custom SSE Endpoint

For simpler setups, create a custom SSE endpoint using `create_sse_handlers()`:

```python
import json
from starlette.applications import Starlette
from starlette.responses import StreamingResponse
from starlette.routing import Route
from bond import BondAgent
from bond.utils import create_sse_handlers

agent = BondAgent(
    name="assistant",
    instructions="You are helpful.",
    model="openai:gpt-4o",
)

async def stream_endpoint(request):
    prompt = request.query_params.get("prompt", "Hello!")

    async def generate():
        async def send_sse(event: str, data: dict):
            yield f"event: {event}\ndata: {json.dumps(data)}\n\n"

        handlers = create_sse_handlers(send_sse)
        await agent.ask(prompt, handlers=handlers)

    return StreamingResponse(generate(), media_type="text/event-stream")

app = Starlette(routes=[Route("/stream", stream_endpoint)])
```

Run with:
```bash
uvicorn server:app --reload --port 8000
```

Click **Connect** and enter: `http://localhost:8000/stream?prompt=Hello`

## SSE Event Format

The UI expects these SSE event types:

| Event | Data | Description |
|-------|------|-------------|
| `block_start` | `{kind, idx}` | New block started |
| `block_end` | `{kind, idx}` | Block finished |
| `text` | `{content}` | Text token |
| `thinking` | `{content}` | Reasoning token |
| `tool_delta` | `{n, a}` | Tool name/args streaming |
| `tool_exec` | `{id, name, args}` | Tool execution started |
| `tool_result` | `{id, name, result}` | Tool returned |
| `complete` | `{data}` | Stream finished |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Pause/Play |
| L | Jump to Live |
| J/K | Step Back/Forward |
| Escape | Close Inspector |

## Future: Full bond.server Integration

The UI's "Connect" button currently expects a single SSE URL. A future update could add support for bond.server's session-based flow:

1. UI prompts for server URL and initial message
2. UI calls `POST /ask` to get session
3. UI connects to `/stream/{session_id}`
4. Multi-turn: UI calls `POST /ask` with same `session_id` for follow-ups

This would enable:
- Persistent conversation history
- Session management
- Multiple concurrent users

See [Streaming Server Guide](../docs/guides/streaming-server.md) for full API documentation.
