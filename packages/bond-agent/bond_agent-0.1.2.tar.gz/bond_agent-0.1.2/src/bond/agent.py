"""Core agent runtime with high-fidelity streaming."""

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models import Model
from pydantic_ai.tools import Tool

T = TypeVar("T")
DepsT = TypeVar("DepsT")


@dataclass
class StreamHandlers:
    """Callbacks mapping to every stage of the LLM lifecycle.

    This allows the UI to perfectly reconstruct the Agent's thought process.

    Lifecycle Events:
        on_block_start: A new block (Text, Thinking, or Tool Call) has started.
        on_block_end: A block has finished generating.
        on_complete: The entire response is finished.

    Content Events (Typing Effect):
        on_text_delta: Incremental text content.
        on_thinking_delta: Incremental thinking/reasoning content.
        on_tool_call_delta: Incremental tool name and arguments as they form.

    Execution Events:
        on_tool_execute: Tool call is fully formed and NOW executing.
        on_tool_result: Tool has finished and returned data.

    Example:
        ```python
        handlers = StreamHandlers(
            on_block_start=lambda kind, idx: print(f"[Start {kind} #{idx}]"),
            on_text_delta=lambda txt: print(txt, end=""),
            on_tool_execute=lambda id, name, args: print(f"[Running {name}...]"),
            on_tool_result=lambda id, name, res: print(f"[Result: {res}]"),
            on_complete=lambda data: print(f"[Done: {data}]"),
        )
        ```
    """

    # Lifecycle: Block open/close
    on_block_start: Callable[[str, int], None] | None = None  # (type, index)
    on_block_end: Callable[[str, int], None] | None = None  # (type, index)

    # Content: Incremental deltas
    on_text_delta: Callable[[str], None] | None = None
    on_thinking_delta: Callable[[str], None] | None = None
    on_tool_call_delta: Callable[[str, str], None] | None = None  # (name_delta, args_delta)

    # Execution: Tool running/results
    on_tool_execute: Callable[[str, str, dict[str, Any]], None] | None = None  # (id, name, args)
    on_tool_result: Callable[[str, str, str], None] | None = None  # (id, name, result_str)

    # Lifecycle: Response complete
    on_complete: Callable[[Any], None] | None = None


@dataclass
class BondAgent(Generic[T, DepsT]):
    """Generic agent runtime wrapping PydanticAI with full-spectrum streaming.

    A BondAgent provides:
    - High-fidelity streaming with callbacks for every lifecycle event
    - Block start/end notifications for UI rendering
    - Real-time streaming of text, thinking, and tool arguments
    - Tool execution and result callbacks
    - Message history management
    - Dynamic instruction override
    - Toolset composition
    - Retry handling

    Example:
        ```python
        agent = BondAgent(
            name="assistant",
            instructions="You are helpful.",
            model="anthropic:claude-sonnet-4-20250514",
            toolsets=[memory_toolset],
            deps=QdrantMemoryStore(),
        )

        handlers = StreamHandlers(
            on_text_delta=lambda t: print(t, end=""),
            on_tool_execute=lambda id, name, args: print(f"[Running {name}]"),
        )

        response = await agent.ask("Remember my preference", handlers=handlers)
        ```
    """

    name: str
    instructions: str
    model: str | Model
    toolsets: Sequence[Sequence[Tool[DepsT]]] = field(default_factory=list)
    deps: DepsT | None = None
    # output_type can be a type, PromptedOutput, or other pydantic_ai output specs
    output_type: type[T] | Any = str
    max_retries: int = 3

    _agent: Agent[DepsT, T] | None = field(default=None, init=False, repr=False)
    _history: list[ModelMessage] = field(default_factory=list, init=False, repr=False)
    _tool_names: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _tools: list[Tool[DepsT]] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the underlying PydanticAI agent."""
        all_tools: list[Tool[DepsT]] = []
        for toolset in self.toolsets:
            all_tools.extend(toolset)

        # Store tools for reuse when creating dynamic agents
        self._tools = all_tools

        # Only pass system_prompt if instructions are non-empty
        # This matches behavior when using raw Agent without system_prompt
        agent_kwargs: dict[str, Any] = {
            "model": self.model,
            "tools": all_tools,
            "output_type": self.output_type,
            "retries": self.max_retries,
        }
        # Only set deps_type when deps is provided
        if self.deps is not None:
            agent_kwargs["deps_type"] = type(self.deps)
        if self.instructions:
            agent_kwargs["system_prompt"] = self.instructions

        self._agent = Agent(**agent_kwargs)

    async def ask(
        self,
        prompt: str,
        *,
        handlers: StreamHandlers | None = None,
        dynamic_instructions: str | None = None,
    ) -> T:
        """Send prompt and get response with high-fidelity streaming.

        Args:
            prompt: The user's message/question.
            handlers: Optional callbacks for streaming events.
            dynamic_instructions: Override system prompt for this call only.

        Returns:
            The agent's response of type T.
        """
        if self._agent is None:
            raise RuntimeError("Agent not initialized")

        active_agent = self._agent
        if dynamic_instructions and dynamic_instructions != self.instructions:
            dynamic_kwargs: dict[str, Any] = {
                "model": self.model,
                "system_prompt": dynamic_instructions,
                "tools": self._tools,
                "output_type": self.output_type,
                "retries": self.max_retries,
            }
            if self.deps is not None:
                dynamic_kwargs["deps_type"] = type(self.deps)
            active_agent = Agent(**dynamic_kwargs)

        if handlers:
            # Build run_stream kwargs - only include deps if provided
            stream_kwargs: dict[str, Any] = {"message_history": self._history}
            if self.deps is not None:
                stream_kwargs["deps"] = self.deps

            async with active_agent.run_stream(prompt, **stream_kwargs) as result:
                # PydanticAI runs tools internally before streaming the final response.
                # We need to emit tool events from the message history first.

                from pydantic_ai.messages import (
                    ModelRequest as MsgModelRequest,
                )
                from pydantic_ai.messages import (
                    ModelResponse as MsgModelResponse,
                )
                from pydantic_ai.messages import (
                    ToolCallPart,
                    ToolReturnPart,
                )

                block_index = 0
                tool_id_to_block: dict[str, int] = {}

                # Wait for streaming to be ready, then check for tool calls in history
                # The new_messages() contains messages from THIS run
                # We need to consume at least one chunk to populate messages
                first_chunk = None
                async for chunk in result.stream_text():
                    first_chunk = chunk
                    break

                # Now check new_messages for tool calls that happened
                for msg in result.new_messages():
                    if isinstance(msg, MsgModelResponse):
                        for part in msg.parts:
                            if isinstance(part, ToolCallPart):
                                # Emit tool call block
                                if handlers.on_block_start:
                                    handlers.on_block_start("tool-call", block_index)
                                tool_id_to_block[part.tool_call_id] = block_index

                                # Emit tool name/args
                                if handlers.on_tool_call_delta:
                                    handlers.on_tool_call_delta(part.tool_name, "")
                                    if isinstance(part.args, str):
                                        args_str = part.args
                                    else:
                                        args_str = json.dumps(part.args)
                                    handlers.on_tool_call_delta("", args_str)

                                # Emit execute event
                                if handlers.on_tool_execute:
                                    if isinstance(part.args, str):
                                        args_dict = json.loads(part.args)
                                    else:
                                        args_dict = dict(part.args) if part.args else {}
                                    handlers.on_tool_execute(
                                        part.tool_call_id, part.tool_name, args_dict
                                    )

                                block_index += 1

                    elif isinstance(msg, MsgModelRequest):
                        for req_part in msg.parts:
                            if isinstance(req_part, ToolReturnPart):
                                # Emit tool result
                                if handlers.on_tool_result:
                                    if isinstance(req_part.content, str):
                                        result_str = req_part.content
                                    else:
                                        result_str = str(req_part.content)
                                    handlers.on_tool_result(
                                        req_part.tool_call_id,
                                        req_part.tool_name,
                                        result_str,
                                    )

                                # Close the tool block
                                tool_block = tool_id_to_block.get(req_part.tool_call_id)
                                if tool_block is not None and handlers.on_block_end:
                                    handlers.on_block_end("tool-call", tool_block)

                # Now stream the text response
                text_block = block_index
                text_started = False

                if first_chunk:
                    if handlers.on_block_start:
                        handlers.on_block_start("text", text_block)
                    text_started = True
                    if handlers.on_text_delta:
                        handlers.on_text_delta(first_chunk)

                async for chunk in result.stream_text():
                    if not text_started:
                        if handlers.on_block_start:
                            handlers.on_block_start("text", text_block)
                        text_started = True
                    if handlers.on_text_delta:
                        handlers.on_text_delta(chunk)

                if text_started and handlers.on_block_end:
                    handlers.on_block_end("text", text_block)

                # Stream finished
                self._history = list(result.all_messages())

                # Get output - use get_output() which is the awaitable method
                output: T = await result.get_output()

                if handlers.on_complete:
                    handlers.on_complete(output)

                return output

        # Non-streaming fallback - build kwargs similarly
        run_kwargs: dict[str, Any] = {"message_history": self._history}
        if self.deps is not None:
            run_kwargs["deps"] = self.deps

        run_result = await active_agent.run(prompt, **run_kwargs)
        self._history = list(run_result.all_messages())
        result_output: T = run_result.output
        return result_output

    def get_message_history(self) -> list[ModelMessage]:
        """Get current conversation history."""
        return list(self._history)

    def set_message_history(self, history: list[ModelMessage]) -> None:
        """Replace conversation history."""
        self._history = list(history)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._history = []

    def clone_with_history(self, history: list[ModelMessage]) -> "BondAgent[T, DepsT]":
        """Create new agent instance with given history (for branching).

        Args:
            history: The message history to use for the clone.

        Returns:
            A new BondAgent with the same configuration but different history.
        """
        clone: BondAgent[T, DepsT] = BondAgent(
            name=self.name,
            instructions=self.instructions,
            model=self.model,
            toolsets=list(self.toolsets),
            deps=self.deps,
            output_type=self.output_type,
            max_retries=self.max_retries,
        )
        clone.set_message_history(history)
        return clone
