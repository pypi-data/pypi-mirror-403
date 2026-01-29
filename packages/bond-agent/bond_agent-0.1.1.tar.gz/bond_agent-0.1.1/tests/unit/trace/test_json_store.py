"""Tests for JSONFileTraceStore backend."""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from bond.trace._models import (
    EVENT_TEXT_DELTA,
    STATUS_COMPLETE,
    STATUS_FAILED,
    TraceEvent,
)
from bond.trace.backends.json_file import JSONFileTraceStore


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for trace files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def store(temp_dir: Path) -> JSONFileTraceStore:
    """Create a JSONFileTraceStore with temp directory."""
    return JSONFileTraceStore(temp_dir)


def make_event(
    trace_id: str,
    sequence: int,
    event_type: str = EVENT_TEXT_DELTA,
    payload: dict | None = None,
) -> TraceEvent:
    """Helper to create TraceEvent."""
    return TraceEvent(
        trace_id=trace_id,
        sequence=sequence,
        timestamp=float(sequence),
        wall_time=datetime.now(UTC),
        event_type=event_type,
        payload=payload or {},
    )


class TestSaveEvent:
    """Tests for save_event."""

    async def test_save_event_creates_file(self, store: JSONFileTraceStore) -> None:
        """Test save_event creates events file."""
        event = make_event("test-trace", 0)
        await store.save_event(event)

        events_path = store.base_path / "test-trace.json"
        assert events_path.exists()

    async def test_save_event_appends_to_file(self, store: JSONFileTraceStore) -> None:
        """Test save_event appends events to file."""
        await store.save_event(make_event("test-trace", 0, payload={"text": "a"}))
        await store.save_event(make_event("test-trace", 1, payload={"text": "b"}))
        await store.save_event(make_event("test-trace", 2, payload={"text": "c"}))

        events_path = store.base_path / "test-trace.json"
        lines = events_path.read_text().strip().split("\n")
        assert len(lines) == 3

        # Verify each line is valid JSON
        for line in lines:
            data = json.loads(line)
            assert "trace_id" in data

    async def test_save_event_creates_meta_file(self, store: JSONFileTraceStore) -> None:
        """Test save_event creates meta file."""
        await store.save_event(make_event("test-trace", 0))

        meta_path = store.base_path / "test-trace.meta.json"
        assert meta_path.exists()

        meta = json.loads(meta_path.read_text())
        assert meta["trace_id"] == "test-trace"
        assert meta["event_count"] == 1

    async def test_save_event_updates_event_count(self, store: JSONFileTraceStore) -> None:
        """Test save_event updates event count in meta."""
        await store.save_event(make_event("test-trace", 0))
        await store.save_event(make_event("test-trace", 1))
        await store.save_event(make_event("test-trace", 2))

        meta_path = store.base_path / "test-trace.meta.json"
        meta = json.loads(meta_path.read_text())
        assert meta["event_count"] == 3


class TestLoadTrace:
    """Tests for load_trace."""

    async def test_load_trace_returns_events_in_order(self, store: JSONFileTraceStore) -> None:
        """Test load_trace returns events in sequence order."""
        await store.save_event(make_event("test-trace", 0, payload={"i": 0}))
        await store.save_event(make_event("test-trace", 1, payload={"i": 1}))
        await store.save_event(make_event("test-trace", 2, payload={"i": 2}))

        events = [e async for e in store.load_trace("test-trace")]

        assert len(events) == 3
        for i, event in enumerate(events):
            assert event.sequence == i
            assert event.payload == {"i": i}

    async def test_load_trace_raises_for_unknown(self, store: JSONFileTraceStore) -> None:
        """Test load_trace raises KeyError for unknown trace."""
        with pytest.raises(KeyError, match="Trace not found"):
            _ = [e async for e in store.load_trace("nonexistent")]


class TestFinalizeTrace:
    """Tests for finalize_trace."""

    async def test_finalize_trace_sets_status(self, store: JSONFileTraceStore) -> None:
        """Test finalize_trace sets status in meta file."""
        await store.save_event(make_event("test-trace", 0))
        await store.finalize_trace("test-trace", STATUS_COMPLETE)

        meta_path = store.base_path / "test-trace.meta.json"
        meta = json.loads(meta_path.read_text())
        assert meta["status"] == STATUS_COMPLETE

    async def test_finalize_trace_failed_status(self, store: JSONFileTraceStore) -> None:
        """Test finalize_trace with failed status."""
        await store.save_event(make_event("test-trace", 0))
        await store.finalize_trace("test-trace", STATUS_FAILED)

        meta_path = store.base_path / "test-trace.meta.json"
        meta = json.loads(meta_path.read_text())
        assert meta["status"] == STATUS_FAILED

    async def test_finalize_trace_raises_for_unknown(self, store: JSONFileTraceStore) -> None:
        """Test finalize_trace raises KeyError for unknown trace."""
        with pytest.raises(KeyError, match="Trace not found"):
            await store.finalize_trace("nonexistent")


class TestListTraces:
    """Tests for list_traces."""

    async def test_list_traces_returns_empty(self, store: JSONFileTraceStore) -> None:
        """Test list_traces returns empty list when no traces."""
        traces = await store.list_traces()
        assert traces == []

    async def test_list_traces_returns_traces(self, store: JSONFileTraceStore) -> None:
        """Test list_traces returns all traces."""
        await store.save_event(make_event("trace-1", 0))
        await store.save_event(make_event("trace-2", 0))

        traces = await store.list_traces()

        assert len(traces) == 2
        trace_ids = {t.trace_id for t in traces}
        assert trace_ids == {"trace-1", "trace-2"}

    async def test_list_traces_respects_limit(self, store: JSONFileTraceStore) -> None:
        """Test list_traces respects limit parameter."""
        for i in range(5):
            await store.save_event(make_event(f"trace-{i}", 0))

        traces = await store.list_traces(limit=3)
        assert len(traces) == 3

    async def test_list_traces_sorted_newest_first(self, store: JSONFileTraceStore) -> None:
        """Test list_traces returns traces sorted by creation time."""
        # Create traces with different timestamps
        await store.save_event(make_event("old-trace", 0))
        await store.save_event(make_event("new-trace", 0))

        traces = await store.list_traces()

        # Newest should be first
        assert traces[0].trace_id == "new-trace"


class TestDeleteTrace:
    """Tests for delete_trace."""

    async def test_delete_trace_removes_files(self, store: JSONFileTraceStore) -> None:
        """Test delete_trace removes both event and meta files."""
        await store.save_event(make_event("test-trace", 0))

        events_path = store.base_path / "test-trace.json"
        meta_path = store.base_path / "test-trace.meta.json"
        assert events_path.exists()
        assert meta_path.exists()

        await store.delete_trace("test-trace")

        assert not events_path.exists()
        assert not meta_path.exists()

    async def test_delete_trace_raises_for_unknown(self, store: JSONFileTraceStore) -> None:
        """Test delete_trace raises KeyError for unknown trace."""
        with pytest.raises(KeyError, match="Trace not found"):
            await store.delete_trace("nonexistent")


class TestGetTraceMeta:
    """Tests for get_trace_meta."""

    async def test_get_trace_meta_returns_meta(self, store: JSONFileTraceStore) -> None:
        """Test get_trace_meta returns TraceMeta."""
        await store.save_event(make_event("test-trace", 0))
        await store.save_event(make_event("test-trace", 1))
        await store.finalize_trace("test-trace", STATUS_COMPLETE)

        meta = await store.get_trace_meta("test-trace")

        assert meta is not None
        assert meta.trace_id == "test-trace"
        assert meta.event_count == 2
        assert meta.status == STATUS_COMPLETE

    async def test_get_trace_meta_returns_none_for_unknown(self, store: JSONFileTraceStore) -> None:
        """Test get_trace_meta returns None for unknown trace."""
        meta = await store.get_trace_meta("nonexistent")
        assert meta is None
