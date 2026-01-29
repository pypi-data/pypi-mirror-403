"""Trace module: Forensic capture and replay for agent executions.

Provides tools for recording all StreamHandlers events during agent runs
and replaying them later for debugging, auditing, and analysis.

Example:
    from bond.trace import JSONFileTraceStore, create_capture_handlers, TraceReplayer

    # Capture during execution
    store = JSONFileTraceStore()
    handlers, trace_id = create_capture_handlers(store)
    result = await agent.ask("hello", stream=handlers)

    # Replay later
    replayer = TraceReplayer(store, trace_id)
    async for event in replayer:
        print(f"{event.event_type}: {event.payload}")
"""

from bond.trace._models import (
    ALL_EVENT_TYPES,
    EVENT_BLOCK_END,
    EVENT_BLOCK_START,
    EVENT_COMPLETE,
    EVENT_TEXT_DELTA,
    EVENT_THINKING_DELTA,
    EVENT_TOOL_CALL_DELTA,
    EVENT_TOOL_EXECUTE,
    EVENT_TOOL_RESULT,
    STATUS_COMPLETE,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
    TraceEvent,
    TraceMeta,
)
from bond.trace._protocols import TraceStorageProtocol
from bond.trace.backends import JSONFileTraceStore
from bond.trace.capture import create_capture_handlers, finalize_capture
from bond.trace.replay import TraceReplayer

__all__ = [
    # Models
    "TraceEvent",
    "TraceMeta",
    # Protocol
    "TraceStorageProtocol",
    # Backends
    "JSONFileTraceStore",
    # Capture
    "create_capture_handlers",
    "finalize_capture",
    # Replay
    "TraceReplayer",
    # Event type constants
    "EVENT_BLOCK_START",
    "EVENT_BLOCK_END",
    "EVENT_TEXT_DELTA",
    "EVENT_THINKING_DELTA",
    "EVENT_TOOL_CALL_DELTA",
    "EVENT_TOOL_EXECUTE",
    "EVENT_TOOL_RESULT",
    "EVENT_COMPLETE",
    "ALL_EVENT_TYPES",
    # Status constants
    "STATUS_IN_PROGRESS",
    "STATUS_COMPLETE",
    "STATUS_FAILED",
]
