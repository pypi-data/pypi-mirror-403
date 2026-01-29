# Forensic Features: Trace Persistence and Replay

## Overview

Extend Bond's "Forensic Runtime" capabilities beyond real-time streaming to include trace persistence and replay. This enables:
- **Audit**: Review what an agent did hours/days ago
- **Debug**: Replay failed runs step-by-step
- **Compare**: Analyze different executions side-by-side

## Scope

### In Scope
- **Trace Capture**: Record all 8 StreamHandlers callback events with metadata
- **Storage Backend**: Pluggable backend interface with JSON file implementation
- **Replay API**: SDK method to iterate through stored events
- **Handler Factory**: `create_capture_handlers()` for easy capture setup

### Out of Scope (Future)
- Protobuf serialization (start with JSON for debugging)
- Remote storage backends (S3, database)
- Cross-trace querying and analytics
- Real-time trace streaming to external systems
- Automatic cleanup/retention policies
- UI replay interface (API only in this phase)

## Approach

### Phase 1: Event Model

Define a unified event structure that normalizes all 8 callback types:

```python
@dataclass(frozen=True)
class TraceEvent:
    trace_id: str           # UUID for this trace
    sequence: int           # Ordering within trace
    timestamp: float        # time.monotonic() for ordering
    wall_time: datetime     # Human-readable timestamp
    event_type: str         # "block_start", "text_delta", etc.
    payload: dict[str, Any] # Event-specific data
```

Event types map to StreamHandlers:
| Callback | event_type | payload keys |
|----------|------------|--------------|
| on_block_start | "block_start" | kind, index |
| on_block_end | "block_end" | kind, index |
| on_text_delta | "text_delta" | text |
| on_thinking_delta | "thinking_delta" | text |
| on_tool_call_delta | "tool_call_delta" | name, args |
| on_tool_execute | "tool_execute" | id, name, args |
| on_tool_result | "tool_result" | id, name, result |
| on_complete | "complete" | data |

### Phase 2: Storage Backend Protocol

```python
@runtime_checkable
class TraceStorageProtocol(Protocol):
    async def save_event(self, event: TraceEvent) -> None:
        """Append event to trace."""
        ...

    async def finalize_trace(self, trace_id: str) -> None:
        """Mark trace as complete."""
        ...

    async def load_trace(self, trace_id: str) -> AsyncIterator[TraceEvent]:
        """Load events for replay."""
        ...

    async def list_traces(self, limit: int = 100) -> list[TraceMeta]:
        """List available traces."""
        ...
```

Initial implementation: `JSONFileTraceStore` writing to `.bond/traces/{trace_id}.json`

### Phase 3: Capture Handler Factory

```python
def create_capture_handlers(
    storage: TraceStorageProtocol,
    trace_id: str | None = None,  # Auto-generate if None
) -> tuple[StreamHandlers, str]:
    """Create handlers that capture events to storage.

    Returns:
        (handlers, trace_id) - handlers for agent.ask(), and trace ID for later replay
    """
```

### Phase 4: Replay API

```python
class TraceReplayer:
    def __init__(self, storage: TraceStorageProtocol, trace_id: str):
        ...

    async def __aiter__(self) -> AsyncIterator[TraceEvent]:
        """Iterate through all events."""
        ...

    async def step(self) -> TraceEvent | None:
        """Get next event (for manual stepping)."""
        ...

    @property
    def current_position(self) -> int:
        """Current event index."""
        ...
```

## Key Files

| File | Purpose |
|------|---------|
| `src/bond/trace/__init__.py` | NEW - Module exports |
| `src/bond/trace/_models.py` | NEW - TraceEvent, TraceMeta models |
| `src/bond/trace/_protocols.py` | NEW - TraceStorageProtocol |
| `src/bond/trace/backends/json_file.py` | NEW - JSON file storage |
| `src/bond/trace/capture.py` | NEW - create_capture_handlers |
| `src/bond/trace/replay.py` | NEW - TraceReplayer class |
| `src/bond/utils.py` | UPDATE - Add capture handler factory |
| `tests/unit/trace/` | NEW - Test directory |

## Reuse Points

- **Event structure**: Inspired by `create_websocket_handlers()` JSON format (`src/bond/utils.py:34-86`)
- **Protocol pattern**: Follow `src/bond/tools/memory/_protocols.py` style
- **Storage pattern**: Similar to `AgentMemoryProtocol` but for events

## Quick Commands

```bash
# Run trace tests
uv run pytest tests/unit/trace/ -v

# Type check
uv run mypy src/bond/trace/

# Example usage (after implementation)
python -c "
from bond.trace import JSONFileTraceStore, create_capture_handlers, TraceReplayer
store = JSONFileTraceStore()
handlers, trace_id = create_capture_handlers(store)
print(f'Trace ID: {trace_id}')
"
```

## Acceptance

- [ ] `TraceEvent` model captures all 8 callback types
- [ ] `TraceStorageProtocol` defines storage interface
- [ ] `JSONFileTraceStore` implements protocol with file-based storage
- [ ] `create_capture_handlers()` returns working StreamHandlers
- [ ] `TraceReplayer` can iterate through stored traces
- [ ] All tests pass with >80% coverage on trace module
- [ ] `mypy` and `ruff` pass
- [ ] Documentation added to architecture page

## Open Questions

1. **Trace directory**: Use `.bond/traces/` or configurable path?
2. **Large tool results**: Truncate at what size? 1MB? 10MB?
3. **Crash handling**: How to mark incomplete traces? Separate "status" field?
4. **Event ordering**: Use monotonic clock + sequence number for guaranteed order?

## References

- WebSocket handler pattern: `src/bond/utils.py:20-118`
- StreamHandlers dataclass: `src/bond/agent.py:28-73`
- Event sourcing StoredEvent: https://eventsourcing.readthedocs.io/
- OTel trace format: https://opentelemetry.io/docs/specs/semconv/gen-ai/
