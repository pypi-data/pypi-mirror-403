"""JSON file storage backend for traces.

Stores traces as newline-delimited JSON files with separate metadata files.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles
import aiofiles.os

from bond.trace._models import (
    STATUS_COMPLETE,
    STATUS_IN_PROGRESS,
    TraceEvent,
    TraceMeta,
)


class JSONFileTraceStore:
    """Store traces as JSON files in a directory.

    Each trace consists of two files:
        - {trace_id}.json: Newline-delimited JSON events
        - {trace_id}.meta.json: TraceMeta as JSON

    File Structure:
        {base_path}/
        ├── {trace_id}.json       # Events (one JSON object per line)
        └── {trace_id}.meta.json  # TraceMeta

    Example:
        ```python
        store = JSONFileTraceStore(".bond/traces")
        await store.save_event(event)
        await store.finalize_trace(trace_id)

        async for event in store.load_trace(trace_id):
            print(event)
        ```
    """

    def __init__(self, base_path: Path | str = ".bond/traces") -> None:
        """Initialize JSON file store.

        Args:
            base_path: Directory for trace files. Created if doesn't exist.
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _events_path(self, trace_id: str) -> Path:
        """Get path to events file for a trace."""
        return self.base_path / f"{trace_id}.json"

    def _meta_path(self, trace_id: str) -> Path:
        """Get path to metadata file for a trace."""
        return self.base_path / f"{trace_id}.meta.json"

    async def save_event(self, event: TraceEvent) -> None:
        """Append event to trace file.

        Creates or updates the metadata file to track event count.
        Uses newline-delimited JSON for efficient streaming reads.

        Args:
            event: The trace event to save.

        Raises:
            IOError: If writing fails.
        """
        events_path = self._events_path(event.trace_id)
        meta_path = self._meta_path(event.trace_id)

        # Append event to events file
        async with aiofiles.open(events_path, "a") as f:
            await f.write(event.model_dump_json() + "\n")

        # Update or create metadata
        if meta_path.exists():
            async with aiofiles.open(meta_path) as f:
                content = await f.read()
                meta_data = json.loads(content)
                meta_data["event_count"] = event.sequence + 1
        else:
            meta_data = {
                "trace_id": event.trace_id,
                "created_at": event.wall_time.isoformat(),
                "event_count": event.sequence + 1,
                "status": STATUS_IN_PROGRESS,
            }

        async with aiofiles.open(meta_path, "w") as f:
            await f.write(json.dumps(meta_data, indent=2))

    async def finalize_trace(
        self,
        trace_id: str,
        status: str = STATUS_COMPLETE,
    ) -> None:
        """Mark a trace as complete or failed.

        Updates the metadata file with the final status.

        Args:
            trace_id: The trace to finalize.
            status: Final status ("complete" or "failed").

        Raises:
            KeyError: If trace_id doesn't exist.
            IOError: If writing fails.
        """
        meta_path = self._meta_path(trace_id)

        if not meta_path.exists():
            msg = f"Trace not found: {trace_id}"
            raise KeyError(msg)

        async with aiofiles.open(meta_path) as f:
            content = await f.read()
            meta_data = json.loads(content)

        meta_data["status"] = status

        async with aiofiles.open(meta_path, "w") as f:
            await f.write(json.dumps(meta_data, indent=2))

    async def load_trace(self, trace_id: str) -> AsyncIterator[TraceEvent]:
        """Load all events from a trace for replay.

        Yields events in sequence order. Memory-efficient for large traces
        since it streams line by line.

        Args:
            trace_id: The trace to load.

        Yields:
            TraceEvent objects in sequence order.

        Raises:
            KeyError: If trace_id doesn't exist.
            IOError: If reading fails.
        """
        events_path = self._events_path(trace_id)

        if not events_path.exists():
            msg = f"Trace not found: {trace_id}"
            raise KeyError(msg)

        async with aiofiles.open(events_path) as f:
            async for line in f:
                line = line.strip()
                if line:
                    yield TraceEvent.model_validate_json(line)

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
        traces: list[TraceMeta] = []

        # Find all meta files
        for meta_path in self.base_path.glob("*.meta.json"):
            try:
                async with aiofiles.open(meta_path) as f:
                    content = await f.read()
                    meta_data = json.loads(content)
                    traces.append(TraceMeta.model_validate(meta_data))
            except (json.JSONDecodeError, KeyError):
                # Skip malformed meta files
                continue

        # Sort by creation time (newest first)
        traces.sort(key=lambda m: m.created_at, reverse=True)

        return traces[:limit]

    async def delete_trace(self, trace_id: str) -> None:
        """Delete a trace and all its files.

        Removes both the events file and metadata file.

        Args:
            trace_id: The trace to delete.

        Raises:
            KeyError: If trace_id doesn't exist.
            IOError: If deletion fails.
        """
        events_path = self._events_path(trace_id)
        meta_path = self._meta_path(trace_id)

        if not events_path.exists() and not meta_path.exists():
            msg = f"Trace not found: {trace_id}"
            raise KeyError(msg)

        if events_path.exists():
            await aiofiles.os.remove(events_path)

        if meta_path.exists():
            await aiofiles.os.remove(meta_path)

    async def get_trace_meta(self, trace_id: str) -> TraceMeta | None:
        """Get metadata for a specific trace.

        Args:
            trace_id: The trace to get metadata for.

        Returns:
            TraceMeta if found, None otherwise.
        """
        meta_path = self._meta_path(trace_id)

        if not meta_path.exists():
            return None

        async with aiofiles.open(meta_path) as f:
            content = await f.read()
            meta_data = json.loads(content)
            return TraceMeta.model_validate(meta_data)
