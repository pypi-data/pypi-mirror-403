"""Tests for TraceReplayer."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from bond.trace._models import EVENT_TEXT_DELTA, TraceEvent
from bond.trace.backends.json_file import JSONFileTraceStore
from bond.trace.replay import TraceReplayer


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for trace files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def store(temp_dir: Path) -> JSONFileTraceStore:
    """Create a JSONFileTraceStore with temp directory."""
    return JSONFileTraceStore(temp_dir)


def make_event(trace_id: str, sequence: int, text: str = "") -> TraceEvent:
    """Helper to create TraceEvent."""
    return TraceEvent(
        trace_id=trace_id,
        sequence=sequence,
        timestamp=float(sequence),
        wall_time=datetime.now(UTC),
        event_type=EVENT_TEXT_DELTA,
        payload={"text": text or f"event-{sequence}"},
    )


async def create_trace_with_events(store: JSONFileTraceStore, trace_id: str, count: int) -> None:
    """Helper to create a trace with specified number of events."""
    for i in range(count):
        await store.save_event(make_event(trace_id, i))


class TestTraceReplayerIteration:
    """Tests for async iteration."""

    async def test_iteration_yields_all_events(self, store: JSONFileTraceStore) -> None:
        """Test async for yields all events."""
        await create_trace_with_events(store, "test-trace", 5)

        replayer = TraceReplayer(store, "test-trace")
        events = [e async for e in replayer]

        assert len(events) == 5

    async def test_iteration_yields_events_in_order(self, store: JSONFileTraceStore) -> None:
        """Test events yielded in sequence order."""
        await create_trace_with_events(store, "test-trace", 5)

        replayer = TraceReplayer(store, "test-trace")
        events = [e async for e in replayer]

        sequences = [e.sequence for e in events]
        assert sequences == [0, 1, 2, 3, 4]

    async def test_iteration_with_empty_trace(self, store: JSONFileTraceStore) -> None:
        """Test iteration with trace that has no events raises KeyError."""
        replayer = TraceReplayer(store, "nonexistent")

        with pytest.raises(KeyError):
            _ = [e async for e in replayer]


class TestTraceReplayerStep:
    """Tests for step() method."""

    async def test_step_returns_next_event(self, store: JSONFileTraceStore) -> None:
        """Test step() returns next event."""
        await create_trace_with_events(store, "test-trace", 3)

        replayer = TraceReplayer(store, "test-trace")
        event = await replayer.step()

        assert event is not None
        assert event.sequence == 0

    async def test_step_advances_position(self, store: JSONFileTraceStore) -> None:
        """Test step() advances position."""
        await create_trace_with_events(store, "test-trace", 3)

        replayer = TraceReplayer(store, "test-trace")
        assert replayer.position == 0

        await replayer.step()
        assert replayer.position == 1

        await replayer.step()
        assert replayer.position == 2

    async def test_step_returns_none_at_end(self, store: JSONFileTraceStore) -> None:
        """Test step() returns None when at end of trace."""
        await create_trace_with_events(store, "test-trace", 2)

        replayer = TraceReplayer(store, "test-trace")
        await replayer.step()  # 0
        await replayer.step()  # 1
        result = await replayer.step()  # past end

        assert result is None


class TestTraceReplayerStepBack:
    """Tests for step_back() method."""

    async def test_step_back_returns_previous_event(self, store: JSONFileTraceStore) -> None:
        """Test step_back() returns previous event."""
        await create_trace_with_events(store, "test-trace", 3)

        replayer = TraceReplayer(store, "test-trace")
        await replayer.step()  # position 1
        await replayer.step()  # position 2

        event = await replayer.step_back()

        assert event is not None
        assert event.sequence == 1
        assert replayer.position == 1

    async def test_step_back_returns_none_at_start(self, store: JSONFileTraceStore) -> None:
        """Test step_back() returns None at start."""
        await create_trace_with_events(store, "test-trace", 3)

        replayer = TraceReplayer(store, "test-trace")
        result = await replayer.step_back()

        assert result is None
        assert replayer.position == 0


class TestTraceReplayerSeek:
    """Tests for seek() method."""

    async def test_seek_jumps_to_position(self, store: JSONFileTraceStore) -> None:
        """Test seek() jumps to specific position."""
        await create_trace_with_events(store, "test-trace", 10)

        replayer = TraceReplayer(store, "test-trace")
        event = await replayer.seek(5)

        assert event is not None
        assert event.sequence == 5
        assert replayer.position == 5

    async def test_seek_clamps_to_bounds(self, store: JSONFileTraceStore) -> None:
        """Test seek() clamps to valid range."""
        await create_trace_with_events(store, "test-trace", 5)

        replayer = TraceReplayer(store, "test-trace")

        # Seek past end
        await replayer.seek(100)
        assert replayer.position == 5  # Clamped to len

        # Seek before start
        await replayer.seek(-10)
        assert replayer.position == 0

    async def test_seek_returns_none_at_end(self, store: JSONFileTraceStore) -> None:
        """Test seek() returns None when seeking to end."""
        await create_trace_with_events(store, "test-trace", 5)

        replayer = TraceReplayer(store, "test-trace")
        event = await replayer.seek(5)

        assert event is None


class TestTraceReplayerProperties:
    """Tests for position and total_events properties."""

    async def test_position_starts_at_zero(self, store: JSONFileTraceStore) -> None:
        """Test position starts at 0."""
        await create_trace_with_events(store, "test-trace", 5)

        replayer = TraceReplayer(store, "test-trace")
        assert replayer.position == 0

    async def test_total_events_none_before_load(self, store: JSONFileTraceStore) -> None:
        """Test total_events is None before loading."""
        await create_trace_with_events(store, "test-trace", 5)

        replayer = TraceReplayer(store, "test-trace")
        assert replayer.total_events is None

    async def test_total_events_after_load(self, store: JSONFileTraceStore) -> None:
        """Test total_events returns count after loading."""
        await create_trace_with_events(store, "test-trace", 5)

        replayer = TraceReplayer(store, "test-trace")
        await replayer.step()  # This triggers load

        assert replayer.total_events == 5


class TestTraceReplayerReset:
    """Tests for reset() method."""

    async def test_reset_moves_to_start(self, store: JSONFileTraceStore) -> None:
        """Test reset() moves position to 0."""
        await create_trace_with_events(store, "test-trace", 5)

        replayer = TraceReplayer(store, "test-trace")
        await replayer.seek(3)
        assert replayer.position == 3

        await replayer.reset()
        assert replayer.position == 0


class TestTraceReplayerCurrent:
    """Tests for current() method."""

    async def test_current_returns_event_at_position(self, store: JSONFileTraceStore) -> None:
        """Test current() returns event at current position."""
        await create_trace_with_events(store, "test-trace", 5)

        replayer = TraceReplayer(store, "test-trace")
        await replayer.seek(2)

        event = await replayer.current()

        assert event is not None
        assert event.sequence == 2
        # Position shouldn't change
        assert replayer.position == 2

    async def test_current_returns_none_at_end(self, store: JSONFileTraceStore) -> None:
        """Test current() returns None at end."""
        await create_trace_with_events(store, "test-trace", 3)

        replayer = TraceReplayer(store, "test-trace")
        await replayer.seek(3)  # Past last event

        event = await replayer.current()
        assert event is None
