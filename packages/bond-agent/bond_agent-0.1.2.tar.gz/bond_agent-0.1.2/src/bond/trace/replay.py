"""Trace replayer for stepping through stored events.

Provides TraceReplayer class for iterating through stored traces
event by event, with support for manual stepping and seeking.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from bond.trace._models import TraceEvent
from bond.trace._protocols import TraceStorageProtocol


class TraceReplayer:
    """Replay a stored trace event by event.

    Supports both async iteration and manual stepping through events.
    Events are loaded on-demand and cached for stepping operations.

    Example (async iteration):
        replayer = TraceReplayer(storage, trace_id)
        async for event in replayer:
            print(f"{event.event_type}: {event.payload}")

    Example (manual stepping):
        replayer = TraceReplayer(storage, trace_id)
        while event := await replayer.step():
            print(event)
            await asyncio.sleep(event.timestamp)  # Replay at original timing

    Example (seeking):
        replayer = TraceReplayer(storage, trace_id)
        await replayer.seek(10)  # Jump to event 10
        event = await replayer.step()
    """

    def __init__(self, storage: TraceStorageProtocol, trace_id: str) -> None:
        """Initialize replayer for a trace.

        Args:
            storage: Backend containing the trace.
            trace_id: ID of the trace to replay.
        """
        self.storage = storage
        self.trace_id = trace_id
        self._events: list[TraceEvent] | None = None
        self._position: int = 0

    async def _load(self) -> None:
        """Load all events into memory for stepping.

        Called automatically by step/seek operations.
        """
        if self._events is None:
            self._events = [e async for e in self.storage.load_trace(self.trace_id)]

    async def __aiter__(self) -> AsyncIterator[TraceEvent]:
        """Iterate through all events.

        Streams directly from storage without loading all events
        into memory first.

        Yields:
            TraceEvent objects in sequence order.
        """
        async for event in self.storage.load_trace(self.trace_id):
            yield event

    async def step(self) -> TraceEvent | None:
        """Get the next event in the trace.

        Returns:
            The next TraceEvent, or None if at end of trace.
        """
        await self._load()
        assert self._events is not None
        if self._position >= len(self._events):
            return None
        event = self._events[self._position]
        self._position += 1
        return event

    async def step_back(self) -> TraceEvent | None:
        """Go back one event.

        Returns:
            The previous TraceEvent, or None if at start of trace.
        """
        await self._load()
        assert self._events is not None
        if self._position <= 0:
            return None
        self._position -= 1
        return self._events[self._position]

    @property
    def position(self) -> int:
        """Current position in trace (0-indexed).

        Returns:
            The current event index.
        """
        return self._position

    @property
    def total_events(self) -> int | None:
        """Total number of events in trace.

        Returns:
            Event count if loaded, None if not yet loaded.
        """
        return len(self._events) if self._events is not None else None

    async def seek(self, position: int) -> TraceEvent | None:
        """Jump to a specific position in the trace.

        Args:
            position: The event index to seek to (0-indexed).

        Returns:
            The event at that position, or None if position is at/past end.
        """
        await self._load()
        assert self._events is not None
        self._position = max(0, min(position, len(self._events)))
        if self._position < len(self._events):
            return self._events[self._position]
        return None

    async def reset(self) -> None:
        """Reset to the beginning of the trace."""
        self._position = 0

    async def current(self) -> TraceEvent | None:
        """Get the current event without advancing position.

        Returns:
            The current TraceEvent, or None if at end.
        """
        await self._load()
        assert self._events is not None
        if self._position < len(self._events):
            return self._events[self._position]
        return None
