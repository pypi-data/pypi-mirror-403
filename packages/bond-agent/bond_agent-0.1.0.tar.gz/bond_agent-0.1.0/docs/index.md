---
hide:
  - navigation
  - toc
---

<div align="center" style="margin-top: 4rem; margin-bottom: 4rem;" markdown="1">

<h1 class="hero-text">Bond</h1>

<p class="hero-subtitle">
The Forensic Runtime for AI Agents
</p>

<p style="max-width: 600px; margin: 0 auto;">
See exactly what your agent is thinking. Watch tool calls form in real-time.
Observe every execution and result. Full transparency—nothing hidden.
</p>

<div class="install-cmd" markdown>
```bash
pip install bond
```
</div>

[Get Started](quickstart.md){ .md-button .md-button--primary }
&nbsp;&nbsp;
[API Reference](api/index.md){ .md-button }

</div>

<div class="grid cards" markdown>

-   :material-eye: **Full-Spectrum Streaming**

    ---

    See every thought, tool call, and result as it happens. `on_thinking_delta`, `on_tool_call_delta`, `on_tool_result`—nothing is hidden.

    [:octicons-arrow-right-24: Architecture](architecture.md)

-   :material-account-switch: **Dynamic Personas**

    ---

    Switch agent personas mid-conversation without creating new instances. The same agent, different cognitive frames.

    [:octicons-arrow-right-24: Quickstart](quickstart.md)

-   :material-shield-check: **Type-Safe Tools**

    ---

    Built on PydanticAI. All tool inputs and outputs are validated against schemas—no hallucinated arguments.

    [:octicons-arrow-right-24: API Reference](api/index.md)

-   :material-lightning-bolt: **Production Ready**

    ---

    WebSocket, SSE, and print handlers included. Plug Bond into any UI framework with minimal glue code.

    [:octicons-arrow-right-24: Architecture](architecture.md)

</div>

---

## Quick Example

```python
from bond import BondAgent, StreamHandlers

# Create handlers for transparency
handlers = StreamHandlers(
    on_thinking_delta=lambda t: print(f"[Thinking] {t}", end=""),
    on_tool_call_delta=lambda name, args: print(f"[Tool] {name}: {args}"),
    on_tool_result=lambda id, name, res: print(f"[Result] {name}: {res}"),
    on_complete=lambda data: print(f"\n[Done] {data}"),
)

# Create agent with streaming
agent = BondAgent(
    name="forensic-assistant",
    instructions="You are a helpful assistant. Think step by step.",
    model="anthropic:claude-sonnet-4-20250514",
)

# Run with full observability
result = await agent.run(
    "What's 2 + 2?",
    handlers=handlers,
)
```

---

## Why Bond?

| Feature | Raw API | LangChain | Bond |
|---------|---------|-----------|------|
| Streaming | Text only | Callback-based | Full-spectrum events |
| Thinking visibility | Hidden | Partial | Real-time deltas |
| Tool call streaming | After completion | After completion | As it forms |
| Persona switching | New client | New chain | Same instance |
| Type safety | Manual | Optional | Built-in (PydanticAI) |

**Bond's philosophy**: The agent's reasoning should be as observable as its output.

---

## StreamHandlers: The Forensic Core

```python
@dataclass
class StreamHandlers:
    # Lifecycle: Block open/close
    on_block_start: Callable[[str, int], None] | None = None
    on_block_end: Callable[[str, int], None] | None = None

    # Content: Incremental deltas
    on_text_delta: Callable[[str], None] | None = None
    on_thinking_delta: Callable[[str], None] | None = None
    on_tool_call_delta: Callable[[str, str], None] | None = None

    # Execution: Tool running/results
    on_tool_execute: Callable[[str, str, dict], None] | None = None
    on_tool_result: Callable[[str, str, str], None] | None = None

    # Lifecycle: Response complete
    on_complete: Callable[[Any], None] | None = None
```

Eight callbacks. Complete observability. Zero black boxes.

---

## Get Started

[Quickstart Guide :material-arrow-right:](quickstart.md){ .md-button .md-button--primary }
