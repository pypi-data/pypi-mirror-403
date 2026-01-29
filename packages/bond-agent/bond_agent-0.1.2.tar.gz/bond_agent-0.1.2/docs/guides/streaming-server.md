# Streaming Server Integration

The Bond server module provides production-ready SSE and WebSocket endpoints for any Bond agent. This enables real-time streaming to web UIs, mobile apps, and other clients.

## Overview

Bond's server module wraps your agent in an ASGI application with:

- **SSE streaming** - Server-Sent Events for one-way real-time updates
- **WebSocket** - Bidirectional streaming for interactive chat
- **Session management** - Multi-turn conversations with history
- **CORS support** - Configurable cross-origin requests

## Installation

Install the server dependencies:

```bash
pip install bond-agent[server]
```

This adds `starlette`, `uvicorn`, and `sse-starlette`.

## Quick Start

```python
from bond import BondAgent
from bond.server import create_bond_server

# Create your agent
agent = BondAgent(
    name="assistant",
    instructions="You are a helpful assistant.",
    model="openai:gpt-4o",
)

# Create ASGI app
app = create_bond_server(agent)
```

Run with uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST /ask

Start a new streaming session.

**Request:**
```json
{
  "prompt": "What is the capital of France?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stream_url": "/stream/550e8400-e29b-41d4-a716-446655440000"
}
```

### GET /stream/{session_id}

SSE endpoint for receiving streaming events.

**Event Types:**

| Event | Data | Description |
|-------|------|-------------|
| `text` | `{"content": "..."}` | Text token delta |
| `thinking` | `{"content": "..."}` | Reasoning/thinking content |
| `tool_exec` | `{"id": "...", "name": "...", "args": {...}}` | Tool execution started |
| `tool_result` | `{"id": "...", "name": "...", "result": "..."}` | Tool returned result |
| `block_start` | `{"kind": "...", "idx": 0}` | New content block started |
| `block_end` | `{"kind": "...", "idx": 0}` | Content block finished |
| `complete` | `{"data": ...}` | Stream complete |
| `error` | `{"error": "..."}` | Error occurred |

### WS /ws

WebSocket endpoint for bidirectional streaming.

**Send:**
```json
{"prompt": "Hello, how are you?"}
```

**Receive:** Same event types as SSE, plus:
```json
{"t": "done"}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "agent_name": "assistant"
}
```

## Client Integration

### JavaScript/TypeScript (SSE)

```typescript
async function askAgent(prompt: string): Promise<void> {
  // 1. Start session
  const response = await fetch('http://localhost:8000/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  const { session_id, stream_url } = await response.json();

  // 2. Connect to SSE stream
  const eventSource = new EventSource(`http://localhost:8000${stream_url}`);

  eventSource.addEventListener('text', (event) => {
    const { content } = JSON.parse(event.data);
    process.stdout.write(content); // Stream tokens
  });

  eventSource.addEventListener('tool_exec', (event) => {
    const { name, args } = JSON.parse(event.data);
    console.log(`\n[Running ${name}...]`);
  });

  eventSource.addEventListener('complete', () => {
    eventSource.close();
    console.log('\n[Done]');
  });

  eventSource.addEventListener('error', (event) => {
    console.error('Stream error:', event);
    eventSource.close();
  });
}
```

### JavaScript/TypeScript (WebSocket)

```typescript
function connectAgent(): WebSocket {
  const ws = new WebSocket('ws://localhost:8000/ws');

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.t) {
      case 'text':
        process.stdout.write(data.c);
        break;
      case 'tool_exec':
        console.log(`\n[Running ${data.name}...]`);
        break;
      case 'done':
        console.log('\n[Complete]');
        break;
    }
  };

  return ws;
}

// Usage
const ws = connectAgent();
ws.send(JSON.stringify({ prompt: 'Hello!' }));
```

### Python Client

```python
import httpx
import json

async def stream_response(prompt: str) -> None:
    async with httpx.AsyncClient() as client:
        # Start session
        response = await client.post(
            "http://localhost:8000/ask",
            json={"prompt": prompt},
        )
        data = response.json()

        # Stream events
        async with client.stream(
            "GET",
            f"http://localhost:8000{data['stream_url']}",
        ) as stream:
            async for line in stream.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    if "content" in event_data:
                        print(event_data["content"], end="", flush=True)
```

### React Hook

```typescript
import { useState, useCallback } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function useAgent(baseUrl: string = 'http://localhost:8000') {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sendMessage = useCallback(async (prompt: string) => {
    setMessages(prev => [...prev, { role: 'user', content: prompt }]);
    setIsStreaming(true);

    // Start session
    const response = await fetch(`${baseUrl}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, session_id: sessionId }),
    });
    const { session_id, stream_url } = await response.json();
    setSessionId(session_id);

    // Stream response
    let assistantContent = '';
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

    const eventSource = new EventSource(`${baseUrl}${stream_url}`);

    eventSource.addEventListener('text', (event) => {
      const { content } = JSON.parse(event.data);
      assistantContent += content;
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: assistantContent },
      ]);
    });

    eventSource.addEventListener('complete', () => {
      eventSource.close();
      setIsStreaming(false);
    });

    eventSource.addEventListener('error', () => {
      eventSource.close();
      setIsStreaming(false);
    });
  }, [baseUrl, sessionId]);

  return { messages, sendMessage, isStreaming };
}
```

## Configuration

Customize server behavior with `ServerConfig`:

```python
from bond.server import create_bond_server, ServerConfig

config = ServerConfig(
    host="0.0.0.0",
    port=8000,
    cors_origins=["http://localhost:3000", "https://myapp.com"],
    session_timeout_seconds=3600,  # 1 hour
    max_concurrent_sessions=100,
)

app = create_bond_server(agent, config=config)
```

## Multi-Turn Conversations

Sessions maintain conversation history automatically:

```typescript
// First message
const { session_id } = await startSession("My name is Alice.");

// Continue with same session_id
await startSession("What's my name?", session_id);
// Agent responds: "Your name is Alice."
```

## Adding Tools

Agents with tools stream tool execution events:

```python
from bond.tools import github_toolset, GitHubAdapter

agent = BondAgent(
    name="code-assistant",
    instructions="You help analyze code repositories.",
    model="openai:gpt-4o",
    toolsets=[github_toolset],
    deps=GitHubAdapter(token=os.environ["GITHUB_TOKEN"]),
)

app = create_bond_server(agent)
```

Clients receive `tool_exec` and `tool_result` events:

```json
{"event": "tool_exec", "data": {"id": "call_123", "name": "github_get_repo", "args": {"owner": "facebook", "repo": "react"}}}
{"event": "tool_result", "data": {"id": "call_123", "name": "github_get_repo", "result": "{...}"}}
```

## Production Deployment

### With Gunicorn

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### With Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Behind Nginx

```nginx
upstream bond {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://bond;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # SSE support
        proxy_buffering off;
        proxy_cache off;
    }
}
```

## Error Handling

Handle connection errors and timeouts:

```typescript
eventSource.onerror = (event) => {
  if (eventSource.readyState === EventSource.CLOSED) {
    // Connection was closed
    console.log('Stream ended');
  } else {
    // Connection error - retry
    console.error('Connection error, retrying...');
    setTimeout(() => reconnect(), 1000);
  }
};
```

## See Also

- [API Reference: Server](../api/server.md) - Full type definitions
- [GitHub Toolset](./github.md) - Adding GitHub tools to your agent
- [Architecture](../architecture.md) - How streaming works internally
