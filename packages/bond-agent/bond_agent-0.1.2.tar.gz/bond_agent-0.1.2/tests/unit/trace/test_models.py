"""Tests for trace event models."""

from datetime import UTC, datetime

import pytest

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
    STATUS_IN_PROGRESS,
    TraceEvent,
    TraceMeta,
)


class TestTraceEvent:
    """Tests for TraceEvent Pydantic model."""

    def test_trace_event_creation(self) -> None:
        """Test TraceEvent can be created with all fields."""
        event = TraceEvent(
            trace_id="test-trace-id",
            sequence=0,
            timestamp=1.5,
            wall_time=datetime(2024, 6, 15, 10, 30, tzinfo=UTC),
            event_type=EVENT_TEXT_DELTA,
            payload={"text": "Hello"},
        )
        assert event.trace_id == "test-trace-id"
        assert event.sequence == 0
        assert event.timestamp == 1.5
        assert event.event_type == EVENT_TEXT_DELTA
        assert event.payload == {"text": "Hello"}

    def test_trace_event_model_dump(self) -> None:
        """Test TraceEvent serialization to dict."""
        wall_time = datetime(2024, 6, 15, 10, 30, tzinfo=UTC)
        event = TraceEvent(
            trace_id="test-id",
            sequence=5,
            timestamp=2.5,
            wall_time=wall_time,
            event_type=EVENT_TOOL_EXECUTE,
            payload={"id": "tool-1", "name": "search", "args": {"q": "test"}},
        )

        result = event.model_dump()

        assert result["trace_id"] == "test-id"
        assert result["sequence"] == 5
        assert result["timestamp"] == 2.5
        assert result["wall_time"] == wall_time
        assert result["event_type"] == EVENT_TOOL_EXECUTE
        assert result["payload"] == {"id": "tool-1", "name": "search", "args": {"q": "test"}}

    def test_trace_event_model_validate(self) -> None:
        """Test TraceEvent deserialization from dict."""
        data = {
            "trace_id": "test-id",
            "sequence": 3,
            "timestamp": 1.0,
            "wall_time": "2024-06-15T10:30:00+00:00",
            "event_type": EVENT_BLOCK_START,
            "payload": {"kind": "text", "index": 0},
        }

        event = TraceEvent.model_validate(data)

        assert event.trace_id == "test-id"
        assert event.sequence == 3
        assert event.timestamp == 1.0
        assert event.wall_time == datetime(2024, 6, 15, 10, 30, tzinfo=UTC)
        assert event.event_type == EVENT_BLOCK_START
        assert event.payload == {"kind": "text", "index": 0}

    def test_trace_event_roundtrip(self) -> None:
        """Test TraceEvent model_dump/model_validate roundtrip."""
        original = TraceEvent(
            trace_id="roundtrip-test",
            sequence=10,
            timestamp=5.5,
            wall_time=datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
            event_type=EVENT_COMPLETE,
            payload={"data": {"answer": "42"}},
        )

        serialized = original.model_dump()
        restored = TraceEvent.model_validate(serialized)

        assert restored == original

    def test_trace_event_model_validate_with_z_suffix(self) -> None:
        """Test model_validate handles Z timezone suffix."""
        data = {
            "trace_id": "z-test",
            "sequence": 0,
            "timestamp": 0.0,
            "wall_time": "2024-06-15T10:30:00Z",
            "event_type": EVENT_TEXT_DELTA,
            "payload": {},
        }

        event = TraceEvent.model_validate(data)
        assert event.wall_time.tzinfo is not None

    @pytest.mark.parametrize("event_type", list(ALL_EVENT_TYPES))
    def test_all_event_types_serialize(self, event_type: str) -> None:
        """Test all 8 event types serialize correctly."""
        event = TraceEvent(
            trace_id="type-test",
            sequence=0,
            timestamp=0.0,
            wall_time=datetime.now(UTC),
            event_type=event_type,
            payload={},
        )

        serialized = event.model_dump()
        assert serialized["event_type"] == event_type

        restored = TraceEvent.model_validate(serialized)
        assert restored.event_type == event_type


class TestTraceMeta:
    """Tests for TraceMeta Pydantic model."""

    def test_trace_meta_creation(self) -> None:
        """Test TraceMeta can be created."""
        meta = TraceMeta(
            trace_id="test-trace",
            created_at=datetime(2024, 6, 15, tzinfo=UTC),
            event_count=42,
            status=STATUS_COMPLETE,
        )
        assert meta.trace_id == "test-trace"
        assert meta.event_count == 42
        assert meta.status == STATUS_COMPLETE

    def test_trace_meta_model_dump(self) -> None:
        """Test TraceMeta serialization."""
        created = datetime(2024, 6, 15, 12, 0, tzinfo=UTC)
        meta = TraceMeta(
            trace_id="meta-test",
            created_at=created,
            event_count=100,
            status=STATUS_IN_PROGRESS,
        )

        result = meta.model_dump()

        assert result["trace_id"] == "meta-test"
        assert result["created_at"] == created
        assert result["event_count"] == 100
        assert result["status"] == STATUS_IN_PROGRESS

    def test_trace_meta_model_validate(self) -> None:
        """Test TraceMeta deserialization."""
        data = {
            "trace_id": "from-dict-test",
            "created_at": "2024-06-15T12:00:00+00:00",
            "event_count": 50,
            "status": STATUS_COMPLETE,
        }

        meta = TraceMeta.model_validate(data)

        assert meta.trace_id == "from-dict-test"
        assert meta.created_at == datetime(2024, 6, 15, 12, 0, tzinfo=UTC)
        assert meta.event_count == 50
        assert meta.status == STATUS_COMPLETE

    def test_trace_meta_roundtrip(self) -> None:
        """Test TraceMeta model_dump/model_validate roundtrip."""
        original = TraceMeta(
            trace_id="roundtrip",
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            event_count=25,
            status=STATUS_COMPLETE,
        )

        restored = TraceMeta.model_validate(original.model_dump())
        assert restored == original


class TestEventTypeConstants:
    """Tests for event type constants."""

    def test_all_event_types_set(self) -> None:
        """Test ALL_EVENT_TYPES contains all 8 types."""
        assert len(ALL_EVENT_TYPES) == 8
        assert EVENT_BLOCK_START in ALL_EVENT_TYPES
        assert EVENT_BLOCK_END in ALL_EVENT_TYPES
        assert EVENT_TEXT_DELTA in ALL_EVENT_TYPES
        assert EVENT_THINKING_DELTA in ALL_EVENT_TYPES
        assert EVENT_TOOL_CALL_DELTA in ALL_EVENT_TYPES
        assert EVENT_TOOL_EXECUTE in ALL_EVENT_TYPES
        assert EVENT_TOOL_RESULT in ALL_EVENT_TYPES
        assert EVENT_COMPLETE in ALL_EVENT_TYPES
