# fn-3.3 Create capture handler factory

## Description
Create capture handler factory in `src/bond/trace/capture.py`.

### Implementation

```python
import time
import uuid
from datetime import datetime, UTC

def create_capture_handlers(
    storage: TraceStorageProtocol,
    trace_id: str | None = None,
) -> tuple[StreamHandlers, str]:
    """Create handlers that capture events to storage.

    Args:
        storage: Backend to store events
        trace_id: Optional trace ID (auto-generated if None)

    Returns:
        (handlers, trace_id) - Use handlers with agent.ask(), keep trace_id for replay

    Example:
        store = JSONFileTraceStore()
        handlers, trace_id = create_capture_handlers(store)
        await agent.ask("query", handlers=handlers)
        # Later: replay with trace_id
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())

    sequence = 0
    start_time = time.monotonic()

    def _record(event_type: str, payload: dict) -> None:
        nonlocal sequence
        event = TraceEvent(
            trace_id=trace_id,
            sequence=sequence,
            timestamp=time.monotonic() - start_time,
            wall_time=datetime.now(UTC),
            event_type=event_type,
            payload=payload,
        )
        sequence += 1
        # Schedule async save from sync callback
        asyncio.get_event_loop().create_task(storage.save_event(event))

    return StreamHandlers(
        on_block_start=lambda k, i: _record("block_start", {"kind": k, "index": i}),
        on_block_end=lambda k, i: _record("block_end", {"kind": k, "index": i}),
        on_text_delta=lambda t: _record("text_delta", {"text": t}),
        on_thinking_delta=lambda t: _record("thinking_delta", {"text": t}),
        on_tool_call_delta=lambda n, a: _record("tool_call_delta", {"name": n, "args": a}),
        on_tool_execute=lambda i, n, a: _record("tool_execute", {"id": i, "name": n, "args": a}),
        on_tool_result=lambda i, n, r: _record("tool_result", {"id": i, "name": n, "result": r}),
        on_complete=lambda d: _record("complete", {"data": d}),
    ), trace_id
```

### Also Add

Helper to finalize trace after agent completes:

```python
async def finalize_capture(
    storage: TraceStorageProtocol,
    trace_id: str,
    status: str = "complete",
) -> None:
    """Mark trace as complete after agent.ask() returns."""
    await storage.finalize_trace(trace_id, status)
```

### Reference

- WebSocket handler pattern: `src/bond/utils.py:20-118`
## Acceptance
- [ ] `create_capture_handlers` returns (StreamHandlers, trace_id)
- [ ] All 8 callbacks are wired to record events
- [ ] Events include sequence number for ordering
- [ ] `finalize_capture` helper exists
- [ ] Works with async agent.ask() (sync callbacks schedule async saves)
- [ ] Integration test: capture → verify file exists with events
## Done summary
- Created create_capture_handlers() returning (StreamHandlers, trace_id)
- All 8 callbacks wired to record TraceEvents with sequence numbers
- Uses monotonic clock for relative timestamps, UTC wall_time for display
- Sync callbacks schedule async saves via event loop (follows websocket pattern)
- Added finalize_capture() helper for marking traces complete/failed
- Verification: mypy and ruff pass on src/bond/trace/
## Evidence
- Commits: b7f53f4
- Tests:
- PRs: