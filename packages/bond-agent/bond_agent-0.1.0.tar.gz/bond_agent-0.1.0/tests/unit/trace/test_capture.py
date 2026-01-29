"""Tests for capture handler factory."""

import tempfile
from pathlib import Path

import pytest

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
    STATUS_FAILED,
)
from bond.trace.backends.json_file import JSONFileTraceStore
from bond.trace.capture import create_capture_handlers, finalize_capture


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for trace files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def store(temp_dir: Path) -> JSONFileTraceStore:
    """Create a JSONFileTraceStore with temp directory."""
    return JSONFileTraceStore(temp_dir)


class TestCreateCaptureHandlers:
    """Tests for create_capture_handlers."""

    def test_returns_handlers_and_trace_id(self, store: JSONFileTraceStore) -> None:
        """Test create_capture_handlers returns tuple of handlers and trace_id."""
        handlers, trace_id = create_capture_handlers(store)

        assert handlers is not None
        assert trace_id is not None
        assert len(trace_id) > 0

    def test_auto_generates_trace_id(self, store: JSONFileTraceStore) -> None:
        """Test trace_id is auto-generated when not provided."""
        _, trace_id1 = create_capture_handlers(store)
        _, trace_id2 = create_capture_handlers(store)

        assert trace_id1 != trace_id2

    def test_uses_provided_trace_id(self, store: JSONFileTraceStore) -> None:
        """Test uses provided trace_id."""
        _, trace_id = create_capture_handlers(store, trace_id="custom-id")
        assert trace_id == "custom-id"

    def test_handlers_have_all_callbacks(self, store: JSONFileTraceStore) -> None:
        """Test handlers have all 8 callback functions."""
        handlers, _ = create_capture_handlers(store)

        assert handlers.on_block_start is not None
        assert handlers.on_block_end is not None
        assert handlers.on_text_delta is not None
        assert handlers.on_thinking_delta is not None
        assert handlers.on_tool_call_delta is not None
        assert handlers.on_tool_execute is not None
        assert handlers.on_tool_result is not None
        assert handlers.on_complete is not None


class TestHandlerCallbacks:
    """Tests for individual handler callbacks recording events."""

    async def test_on_block_start_records_event(self, store: JSONFileTraceStore) -> None:
        """Test on_block_start records block_start event."""
        handlers, trace_id = create_capture_handlers(store)

        # Call the handler (sync)
        handlers.on_block_start("text", 0)  # type: ignore[misc]

        # Wait for async task to complete
        import asyncio

        await asyncio.sleep(0.1)

        events = [e async for e in store.load_trace(trace_id)]
        assert len(events) >= 1
        assert events[0].event_type == EVENT_BLOCK_START
        assert events[0].payload == {"kind": "text", "index": 0}

    async def test_on_text_delta_records_event(self, store: JSONFileTraceStore) -> None:
        """Test on_text_delta records text_delta event."""
        handlers, trace_id = create_capture_handlers(store)

        handlers.on_text_delta("Hello")  # type: ignore[misc]

        import asyncio

        await asyncio.sleep(0.1)

        events = [e async for e in store.load_trace(trace_id)]
        assert any(
            e.event_type == EVENT_TEXT_DELTA and e.payload == {"text": "Hello"} for e in events
        )

    async def test_sequence_numbers_unique(self, store: JSONFileTraceStore) -> None:
        """Test events have unique sequence numbers (0-indexed)."""
        handlers, trace_id = create_capture_handlers(store)

        handlers.on_block_start("text", 0)  # type: ignore[misc]
        handlers.on_text_delta("a")  # type: ignore[misc]
        handlers.on_text_delta("b")  # type: ignore[misc]
        handlers.on_block_end("text", 0)  # type: ignore[misc]

        import asyncio

        await asyncio.sleep(0.2)

        events = [e async for e in store.load_trace(trace_id)]
        sequences = sorted([e.sequence for e in events])
        # All sequences present (async saves may complete out of order)
        assert sequences == list(range(len(sequences)))

    async def test_all_callbacks_record_correct_types(self, store: JSONFileTraceStore) -> None:
        """Test all 8 callbacks record correct event types."""
        handlers, trace_id = create_capture_handlers(store)

        handlers.on_block_start("text", 0)  # type: ignore[misc]
        handlers.on_text_delta("Hello")  # type: ignore[misc]
        handlers.on_thinking_delta("thinking...")  # type: ignore[misc]
        handlers.on_tool_call_delta("search", '{"q":')  # type: ignore[misc]
        handlers.on_tool_execute("tool-1", "search", {"q": "test"})  # type: ignore[misc]
        handlers.on_tool_result("tool-1", "search", "result")  # type: ignore[misc]
        handlers.on_block_end("text", 0)  # type: ignore[misc]
        handlers.on_complete({"answer": "42"})  # type: ignore[misc]

        import asyncio

        await asyncio.sleep(0.3)

        events = [e async for e in store.load_trace(trace_id)]
        event_types = [e.event_type for e in events]

        assert EVENT_BLOCK_START in event_types
        assert EVENT_TEXT_DELTA in event_types
        assert EVENT_THINKING_DELTA in event_types
        assert EVENT_TOOL_CALL_DELTA in event_types
        assert EVENT_TOOL_EXECUTE in event_types
        assert EVENT_TOOL_RESULT in event_types
        assert EVENT_BLOCK_END in event_types
        assert EVENT_COMPLETE in event_types


class TestFinalizeCapture:
    """Tests for finalize_capture."""

    async def test_finalize_capture_marks_complete(self, store: JSONFileTraceStore) -> None:
        """Test finalize_capture marks trace as complete."""
        handlers, trace_id = create_capture_handlers(store)
        handlers.on_text_delta("test")  # type: ignore[misc]

        import asyncio

        await asyncio.sleep(0.1)
        await finalize_capture(store, trace_id)

        meta = await store.get_trace_meta(trace_id)
        assert meta is not None
        assert meta.status == STATUS_COMPLETE

    async def test_finalize_capture_with_failed_status(self, store: JSONFileTraceStore) -> None:
        """Test finalize_capture with failed status."""
        handlers, trace_id = create_capture_handlers(store)
        handlers.on_text_delta("test")  # type: ignore[misc]

        import asyncio

        await asyncio.sleep(0.1)
        await finalize_capture(store, trace_id, STATUS_FAILED)

        meta = await store.get_trace_meta(trace_id)
        assert meta is not None
        assert meta.status == STATUS_FAILED
