"""Trace storage protocol - interface for trace backends.

Defines the interface that trace storage implementations must follow.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from bond.trace._models import TraceEvent, TraceMeta


@runtime_checkable
class TraceStorageProtocol(Protocol):
    """Protocol for trace storage backends.

    Provides async methods for saving, loading, and managing execution traces.
    All operations are async to support various backend implementations
    (file, database, remote storage).

    Implementations:
        - JSONFileTraceStore: Local JSON file storage (default)
    """

    async def save_event(self, event: TraceEvent) -> None:
        """Append an event to a trace.

        The trace is created if it doesn't exist. Events should be
        saved in order (by sequence number).

        Args:
            event: The trace event to save.

        Raises:
            IOError: If storage fails.
        """
        ...

    async def finalize_trace(
        self,
        trace_id: str,
        status: str = "complete",
    ) -> None:
        """Mark a trace as complete or failed.

        Should be called when the agent run finishes. This updates
        the trace metadata and may trigger cleanup or indexing.

        Args:
            trace_id: The trace to finalize.
            status: Final status ("complete" or "failed").

        Raises:
            KeyError: If trace_id doesn't exist.
            IOError: If storage fails.
        """
        ...

    def load_trace(self, trace_id: str) -> AsyncIterator[TraceEvent]:
        """Load all events from a trace for replay.

        Yields events in sequence order. Memory-efficient for large traces.
        This is an async generator method.

        Args:
            trace_id: The trace to load.

        Yields:
            TraceEvent objects in sequence order.

        Raises:
            KeyError: If trace_id doesn't exist.
            IOError: If loading fails.
        """
        ...

    async def list_traces(self, limit: int = 100) -> list[TraceMeta]:
        """List available traces with metadata.

        Returns traces ordered by creation time (newest first).

        Args:
            limit: Maximum number of traces to return.

        Returns:
            List of TraceMeta for available traces.

        Raises:
            IOError: If listing fails.
        """
        ...

    async def delete_trace(self, trace_id: str) -> None:
        """Delete a trace and all its events.

        Args:
            trace_id: The trace to delete.

        Raises:
            KeyError: If trace_id doesn't exist.
            IOError: If deletion fails.
        """
        ...
