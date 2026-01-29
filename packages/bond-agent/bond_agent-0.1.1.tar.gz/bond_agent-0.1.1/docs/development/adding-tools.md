# Adding Tools

This guide explains how to add new toolsets to Bond using the protocol-driven architecture.

## Overview

Bond toolsets follow a consistent pattern:

1. **Protocol** - Defines the interface (what the backend must implement)
2. **Models** - Pydantic models for request/response validation
3. **Adapter** - Concrete implementation of the protocol
4. **Tools** - Agent-facing functions that use dependency injection

This separation enables:

- Backend flexibility (swap implementations without changing tools)
- Type safety (all inputs/outputs validated)
- Testability (mock the protocol in tests)

## File Structure

Create a new directory under `src/bond/tools/`:

```
src/bond/tools/my_tool/
├── __init__.py          # Public API exports
├── _protocols.py        # Protocol definition
├── _models.py           # Request/response models
├── _adapter.py          # Protocol implementation
├── _types.py            # (optional) Domain types
├── _exceptions.py       # (optional) Custom exceptions
└── tools.py             # Tool functions
```

## Step-by-Step Guide

### 1. Define the Protocol

The protocol defines what operations your backend must support:

```python
# _protocols.py
"""Protocol definition for MyTool."""

from typing import Protocol, runtime_checkable

from ._types import MyResult


@runtime_checkable
class MyToolProtocol(Protocol):
    """Protocol for MyTool operations.

    Provides methods to:
    - Do something useful
    - Do something else useful
    """

    async def do_something(
        self,
        input_value: str,
        options: dict[str, str] | None = None,
    ) -> MyResult:
        """Perform the main operation.

        Args:
            input_value: The input to process.
            options: Optional configuration.

        Returns:
            MyResult with the operation outcome.

        Raises:
            MyToolError: If operation fails.
        """
        ...
```

Key points:

- Use `@runtime_checkable` for isinstance checks
- Document all methods with Google-style docstrings
- Use `...` (ellipsis) for method bodies in protocols

### 2. Create Request/Response Models

Define Pydantic models for tool inputs:

```python
# _models.py
"""Request and error models for MyTool."""

from typing import Annotated

from pydantic import BaseModel, Field


class DoSomethingRequest(BaseModel):
    """Request to perform the main operation.

    Agent Usage: Use this when you need to process an input
    and get a structured result.
    """

    input_value: Annotated[
        str,
        Field(description="The input value to process"),
    ]

    options: Annotated[
        dict[str, str] | None,
        Field(default=None, description="Optional configuration"),
    ]


class Error(BaseModel):
    """Error response from MyTool operations.

    Used as union return type: `MyResult | Error`.
    """

    description: Annotated[
        str,
        Field(description="Error message explaining what went wrong"),
    ]
```

Best practices:

- Include "Agent Usage" in model docstrings to help the LLM understand when to use the tool
- Use `Annotated` with `Field(description=...)` for all fields
- Add validation constraints where appropriate (`ge=`, `le=`, `min_length=`, etc.)

### 3. Implement the Adapter

Create a concrete implementation of your protocol:

```python
# _adapter.py
"""Adapter implementation for MyTool."""

from ._exceptions import MyToolError
from ._protocols import MyToolProtocol
from ._types import MyResult


class MyToolAdapter:
    """Default implementation of MyToolProtocol.

    Uses external service/library to perform operations.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the adapter.

        Args:
            api_key: Optional API key for authentication.
        """
        self._api_key = api_key

    async def do_something(
        self,
        input_value: str,
        options: dict[str, str] | None = None,
    ) -> MyResult:
        """Perform the main operation.

        Args:
            input_value: The input to process.
            options: Optional configuration.

        Returns:
            MyResult with the operation outcome.

        Raises:
            MyToolError: If operation fails.
        """
        try:
            # Implementation here
            result = await self._call_external_service(input_value, options)
            return MyResult(value=result)
        except Exception as e:
            raise MyToolError(str(e)) from e
```

### 4. Create Tool Functions

Tool functions use `RunContext` for dependency injection:

```python
# tools.py
"""MyTool tools for PydanticAI agents."""

from pydantic_ai import RunContext
from pydantic_ai.tools import Tool

from ._exceptions import MyToolError
from ._models import DoSomethingRequest, Error
from ._protocols import MyToolProtocol
from ._types import MyResult


async def do_something(
    ctx: RunContext[MyToolProtocol],
    request: DoSomethingRequest,
) -> MyResult | Error:
    """Perform the main operation.

    Agent Usage:
        Call this tool when you need to process an input value
        and get a structured result:
        - "Process this data" → do_something with the input
        - "Transform this value" → check the result

    Example:
        ```python
        do_something({
            "input_value": "hello world",
            "options": {"format": "uppercase"}
        })
        ```

    Returns:
        MyResult with the processed value,
        or Error if the operation failed.
    """
    try:
        return await ctx.deps.do_something(
            input_value=request.input_value,
            options=request.options,
        )
    except MyToolError as e:
        return Error(description=str(e))


# Export as toolset for BondAgent
my_tool_toolset: list[Tool[MyToolProtocol]] = [
    Tool(do_something),
]
```

Key patterns:

- **Return `Error`, don't raise**: Tools return union types like `MyResult | Error`
- **Agent Usage docstrings**: Describe when and how the agent should use the tool
- **Example blocks**: Show the exact JSON the agent should pass
- **Type the toolset**: Use `list[Tool[MyToolProtocol]]` for type safety

### 5. Export Public API

Define what's public in `__init__.py`:

```python
# __init__.py
"""MyTool: Description of what this toolset does.

Provides tools for:
- Operation one
- Operation two
"""

from ._adapter import MyToolAdapter
from ._exceptions import MyToolError
from ._models import DoSomethingRequest, Error
from ._protocols import MyToolProtocol
from ._types import MyResult
from .tools import my_tool_toolset

__all__ = [
    # Adapter
    "MyToolAdapter",
    # Types
    "MyResult",
    # Protocol
    "MyToolProtocol",
    # Toolset
    "my_tool_toolset",
    # Request Models
    "DoSomethingRequest",
    "Error",
    # Exceptions
    "MyToolError",
]
```

### 6. Register with BondAgent

Users can now use your toolset:

```python
from bond import BondAgent
from bond.tools.my_tool import my_tool_toolset, MyToolAdapter

# Create the adapter
adapter = MyToolAdapter(api_key="...")

# Create agent with tools
agent = BondAgent(
    name="my-agent",
    instructions="Use MyTool to process inputs.",
    model="anthropic:claude-sonnet-4-20250514",
    toolsets=[my_tool_toolset],
    deps=adapter,
)

# Run the agent
result = await agent.ask("Process this: hello world")
```

## Best Practices

### Error Handling

Always return `Error` models instead of raising exceptions in tool functions:

```python
# Good - returns Error
async def my_tool(ctx: RunContext[Protocol], request: Request) -> Result | Error:
    try:
        return await ctx.deps.operation(request.value)
    except MyError as e:
        return Error(description=str(e))

# Bad - raises exception
async def my_tool(ctx: RunContext[Protocol], request: Request) -> Result:
    return await ctx.deps.operation(request.value)  # May raise!
```

### Docstrings

Include "Agent Usage" sections that explain:

- **When** to use the tool
- **What** inputs it expects
- **What** outputs to expect

```python
async def analyze_data(
    ctx: RunContext[AnalysisProtocol],
    request: AnalyzeRequest,
) -> AnalysisResult | Error:
    """Analyze data and return insights.

    Agent Usage:
        Call this tool when you need to analyze structured data:
        - "What patterns are in this data?" → analyze_data
        - "Summarize these metrics" → analyze_data with summary=True

    Example:
        ```python
        analyze_data({
            "data": [1, 2, 3, 4, 5],
            "summary": true
        })
        ```

    Returns:
        AnalysisResult with insights and statistics,
        or Error if analysis failed.
    """
```

### Type Safety

Use `Annotated` fields with descriptive metadata:

```python
class MyRequest(BaseModel):
    # Good - descriptive, validated
    count: Annotated[
        int,
        Field(ge=1, le=100, description="Number of items to process (1-100)"),
    ]

    # Bad - no description, no validation
    count: int
```

## See Also

- [Testing](testing.md) - How to test your new toolset
- [GitHunter Guide](../guides/githunter.md) - Example toolset documentation
- [API Reference: Tools](../api/tools.md) - Full API documentation
