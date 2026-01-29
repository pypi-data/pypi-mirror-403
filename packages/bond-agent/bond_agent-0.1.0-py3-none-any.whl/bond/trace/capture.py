"""Capture handler factory for trace recording.

Creates StreamHandlers that record all events to a trace storage backend
for later replay and analysis.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from bond.agent import StreamHandlers
from bond.trace._models import (
    EVENT_BLOCK_END,
    EVENT_BLOCK_START,
    EVENT_COMPLETE,
    EVENT_TEXT_DELTA,
    EVENT_THINKING_DELTA,
    EVENT_TOOL_CALL_DELTA,
    EVENT_TOOL_EXECUTE,
    EVENT_TOOL_RESULT,
    STATUS_COMPLETE,
    TraceEvent,
)
from bond.trace._protocols import TraceStorageProtocol


def create_capture_handlers(
    storage: TraceStorageProtocol,
    trace_id: str | None = None,
) -> tuple[StreamHandlers, str]:
    """Create handlers that capture all events to storage.

    Returns handlers that can be passed to agent.ask() along with the
    trace ID for later replay. All 8 StreamHandlers callbacks are wired
    to record events with sequence numbers for ordering.

    Args:
        storage: Backend to store events (e.g., JSONFileTraceStore).
        trace_id: Optional trace ID (auto-generated UUID if None).

    Returns:
        Tuple of (handlers, trace_id) - use handlers with agent.ask(),
        keep trace_id for later replay.

    Example:
        ```python
        store = JSONFileTraceStore()
        handlers, trace_id = create_capture_handlers(store)
        result = await agent.ask("query", handlers=handlers)
        await finalize_capture(store, trace_id)

        # Later: replay with trace_id
        async for event in store.load_trace(trace_id):
            print(event)
        ```
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())

    # Mutable state for closure
    sequence = [0]  # List to allow mutation in nested function
    start_time = time.monotonic()

    def _record(event_type: str, payload: dict[str, Any]) -> None:
        """Record an event to storage.

        Called from sync callbacks, schedules async save.
        """
        event = TraceEvent(
            trace_id=trace_id,
            sequence=sequence[0],
            timestamp=time.monotonic() - start_time,
            wall_time=datetime.now(UTC),
            event_type=event_type,
            payload=payload,
        )
        sequence[0] += 1

        # Schedule async save from sync callback
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(storage.save_event(event))
        except RuntimeError:
            # No running loop - shouldn't happen in normal usage
            pass

    return (
        StreamHandlers(
            on_block_start=lambda kind, idx: _record(
                EVENT_BLOCK_START,
                {"kind": kind, "index": idx},
            ),
            on_block_end=lambda kind, idx: _record(
                EVENT_BLOCK_END,
                {"kind": kind, "index": idx},
            ),
            on_text_delta=lambda text: _record(
                EVENT_TEXT_DELTA,
                {"text": text},
            ),
            on_thinking_delta=lambda text: _record(
                EVENT_THINKING_DELTA,
                {"text": text},
            ),
            on_tool_call_delta=lambda name, args: _record(
                EVENT_TOOL_CALL_DELTA,
                {"name": name, "args": args},
            ),
            on_tool_execute=lambda tool_id, name, args: _record(
                EVENT_TOOL_EXECUTE,
                {"id": tool_id, "name": name, "args": args},
            ),
            on_tool_result=lambda tool_id, name, result: _record(
                EVENT_TOOL_RESULT,
                {"id": tool_id, "name": name, "result": result},
            ),
            on_complete=lambda data: _record(
                EVENT_COMPLETE,
                {"data": data},
            ),
        ),
        trace_id,
    )


async def finalize_capture(
    storage: TraceStorageProtocol,
    trace_id: str,
    status: str = STATUS_COMPLETE,
) -> None:
    """Mark a trace as complete after agent.ask() returns.

    Should be called after the agent run finishes to update the trace
    metadata with the final status.

    Args:
        storage: The storage backend used for capture.
        trace_id: The trace ID from create_capture_handlers().
        status: Final status ("complete" or "failed").

    Example:
        ```python
        handlers, trace_id = create_capture_handlers(store)
        try:
            result = await agent.ask("query", handlers=handlers)
            await finalize_capture(store, trace_id, "complete")
        except Exception:
            await finalize_capture(store, trace_id, "failed")
            raise
        ```
    """
    await storage.finalize_trace(trace_id, status)
