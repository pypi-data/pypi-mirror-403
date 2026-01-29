"""Trace event models for forensic capture and replay.

Provides Pydantic models for trace events and metadata that capture
all 8 StreamHandlers callback types for persistence and replay.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

# Event type constants matching StreamHandlers callbacks
EVENT_BLOCK_START = "block_start"
EVENT_BLOCK_END = "block_end"
EVENT_TEXT_DELTA = "text_delta"
EVENT_THINKING_DELTA = "thinking_delta"
EVENT_TOOL_CALL_DELTA = "tool_call_delta"
EVENT_TOOL_EXECUTE = "tool_execute"
EVENT_TOOL_RESULT = "tool_result"
EVENT_COMPLETE = "complete"

ALL_EVENT_TYPES = frozenset(
    {
        EVENT_BLOCK_START,
        EVENT_BLOCK_END,
        EVENT_TEXT_DELTA,
        EVENT_THINKING_DELTA,
        EVENT_TOOL_CALL_DELTA,
        EVENT_TOOL_EXECUTE,
        EVENT_TOOL_RESULT,
        EVENT_COMPLETE,
    }
)


class TraceEvent(BaseModel):
    """A single event in an execution trace.

    Captures one callback from StreamHandlers with full context
    for later replay or analysis.

    Attributes:
        trace_id: UUID identifying this trace session.
        sequence: Zero-indexed order within the trace.
        timestamp: Monotonic clock value for relative ordering.
        wall_time: Human-readable UTC timestamp.
        event_type: One of the 8 callback types.
        payload: Event-specific data (varies by event_type).
    """

    model_config = ConfigDict(frozen=True)

    trace_id: str
    sequence: int
    timestamp: float
    wall_time: datetime
    event_type: str
    payload: dict[str, Any]


# Trace status constants
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETE = "complete"
STATUS_FAILED = "failed"


class TraceMeta(BaseModel):
    """Metadata about a stored trace.

    Provides summary information without loading all events.

    Attributes:
        trace_id: UUID identifying this trace.
        created_at: When the trace was started.
        event_count: Number of events in the trace.
        status: One of "in_progress", "complete", "failed".
    """

    model_config = ConfigDict(frozen=True)

    trace_id: str
    created_at: datetime
    event_count: int
    status: str
