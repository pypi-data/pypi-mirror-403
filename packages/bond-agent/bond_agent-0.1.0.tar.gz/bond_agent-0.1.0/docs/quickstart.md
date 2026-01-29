# Quickstart

Get started with Bond in minutes. Build your first transparent AI agent.

## Installation

```bash
pip install bond
```

You'll also need an Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## Your First Agent

The simplest Bond agent looks like this:

=== "Async"

    ```python
    import asyncio
    from bond import BondAgent

    agent = BondAgent(
        name="assistant",
        instructions="You are a helpful assistant.",
        model="anthropic:claude-sonnet-4-20250514",
    )

    async def main():
        result = await agent.ask("What is 2 + 2?")
        print(result)

    asyncio.run(main())
    ```

=== "Sync"

    ```python
    from bond import BondAgent

    agent = BondAgent(
        name="assistant",
        instructions="You are a helpful assistant.",
        model="anthropic:claude-sonnet-4-20250514",
    )

    # Use run_sync for synchronous contexts
    result = agent.run_sync("What is 2 + 2?")
    print(result)
    ```

**Expected output:**

```
4
```

## Adding Streaming Handlers

Here's where Bond shines. Add `StreamHandlers` to see exactly what your agent is thinking:

```python
import asyncio
from bond import BondAgent, StreamHandlers

# Create handlers to observe the agent
handlers = StreamHandlers(
    on_block_start=lambda kind, idx: print(f"\n[Start {kind} #{idx}]"),
    on_text_delta=lambda txt: print(txt, end="", flush=True),
    on_thinking_delta=lambda txt: print(f"[Thinking: {txt}]", end=""),
    on_tool_execute=lambda id, name, args: print(f"\n[Running {name}...]"),
    on_tool_result=lambda id, name, res: print(f"[{name} returned: {res}]"),
    on_complete=lambda data: print("\n[Complete]"),
)

agent = BondAgent(
    name="assistant",
    instructions="You are a helpful assistant. Think step by step.",
    model="anthropic:claude-sonnet-4-20250514",
)

async def main():
    result = await agent.ask(
        "What is the square root of 144?",
        handlers=handlers,
    )
    print(f"\nFinal answer: {result}")

asyncio.run(main())
```

### Using Pre-built Handlers

For quick debugging, use `create_print_handlers()`:

```python
from bond import BondAgent, create_print_handlers

handlers = create_print_handlers(
    show_thinking=True,   # Show chain-of-thought reasoning
    show_tool_args=True,  # Show tool arguments as they form
)

agent = BondAgent(
    name="debug-assistant",
    instructions="You are helpful.",
    model="anthropic:claude-sonnet-4-20250514",
)

# Now all streaming events print to console
result = await agent.ask("Explain quantum computing", handlers=handlers)
```

### Handler Reference

| Callback | When it fires | Arguments |
|----------|--------------|-----------|
| `on_block_start` | New block (text/thinking/tool) begins | `(kind: str, index: int)` |
| `on_block_end` | Block finishes | `(kind: str, index: int)` |
| `on_text_delta` | Text content streams | `(text: str)` |
| `on_thinking_delta` | Reasoning content streams | `(text: str)` |
| `on_tool_call_delta` | Tool name/args stream | `(name: str, args: str)` |
| `on_tool_execute` | Tool execution starts | `(id: str, name: str, args: dict)` |
| `on_tool_result` | Tool returns result | `(id: str, name: str, result: str)` |
| `on_complete` | Response finished | `(data: Any)` |

## Dynamic Instructions

Switch personas mid-conversation without creating a new agent:

```python
import asyncio
from bond import BondAgent

agent = BondAgent(
    name="multi-persona",
    instructions="You are a general assistant.",
    model="anthropic:claude-sonnet-4-20250514",
)

async def main():
    # Default persona
    result1 = await agent.ask("Explain this SQL query: SELECT * FROM users")
    print("General:", result1)

    # Switch to DBA persona for this call only
    result2 = await agent.ask(
        "Explain this SQL query: SELECT * FROM users",
        dynamic_instructions="You are a senior DBA. Focus on performance implications.",
    )
    print("DBA:", result2)

    # Analyst persona
    result3 = await agent.ask(
        "Explain this SQL query: SELECT * FROM users",
        dynamic_instructions="You are a data analyst. Focus on what insights this query provides.",
    )
    print("Analyst:", result3)

asyncio.run(main())
```

The agent maintains conversation history across persona switches—only the system prompt changes.

## Adding Tools

Define tools with Pydantic validation:

```python
import asyncio
from pydantic_ai import Tool
from pydantic_ai.tools import RunContext
from bond import BondAgent, StreamHandlers

# Define a typed tool
def calculate(ctx: RunContext[None], expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A mathematical expression like "2 + 2" or "sqrt(16)"
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {"sqrt": lambda x: x**0.5})
        return str(result)
    except Exception as e:
        return f"Error: {e}"

calc_tool = Tool(calculate)

agent = BondAgent(
    name="calculator",
    instructions="You are a calculator. Use the calculate tool for math.",
    model="anthropic:claude-sonnet-4-20250514",
    toolsets=[[calc_tool]],
)

handlers = StreamHandlers(
    on_tool_execute=lambda id, name, args: print(f"[Calculating: {args}]"),
    on_tool_result=lambda id, name, res: print(f"[Result: {res}]"),
)

async def main():
    result = await agent.ask(
        "What is 15 * 7 + sqrt(49)?",
        handlers=handlers,
    )
    print(f"Answer: {result}")

asyncio.run(main())
```

## Using Bundled Toolsets

Bond includes pre-built toolsets for common use cases:

```python
from bond.tools.memory import create_memory_toolset, QdrantMemoryStore

# Create a memory backend
store = QdrantMemoryStore(collection="agent-memory")

# Get the memory toolset
memory_tools = create_memory_toolset(store)

agent = BondAgent(
    name="memory-agent",
    instructions="You remember user preferences.",
    model="anthropic:claude-sonnet-4-20250514",
    toolsets=[memory_tools],
    deps=store,  # Pass backend as dependency
)
```

See [Architecture](architecture.md) for details on available toolsets.

## Next Steps

- [Architecture](architecture.md) - Deep dive into StreamHandlers and BondAgent
- [API Reference](api/index.md) - Full API documentation
