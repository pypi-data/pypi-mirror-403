# fn-3.4 Implement trace replayer

## Description
Implement trace replayer in `src/bond/trace/replay.py`.

### Implementation

```python
class TraceReplayer:
    """Replay a stored trace event by event.

    Usage:
        replayer = TraceReplayer(storage, trace_id)

        # Iterate all events
        async for event in replayer:
            print(f"{event.event_type}: {event.payload}")

        # Or step manually
        replayer = TraceReplayer(storage, trace_id)
        while event := await replayer.step():
            print(event)
            await asyncio.sleep(0.1)  # Simulate timing
    """

    def __init__(self, storage: TraceStorageProtocol, trace_id: str):
        self.storage = storage
        self.trace_id = trace_id
        self._events: list[TraceEvent] | None = None
        self._position: int = 0

    async def _load(self) -> None:
        """Load all events into memory for stepping."""
        if self._events is None:
            self._events = [e async for e in self.storage.load_trace(self.trace_id)]

    async def __aiter__(self) -> AsyncIterator[TraceEvent]:
        """Iterate through all events."""
        async for event in self.storage.load_trace(self.trace_id):
            yield event

    async def step(self) -> TraceEvent | None:
        """Get next event, or None if complete."""
        await self._load()
        if self._position >= len(self._events):
            return None
        event = self._events[self._position]
        self._position += 1
        return event

    async def step_back(self) -> TraceEvent | None:
        """Go back one event."""
        await self._load()
        if self._position <= 0:
            return None
        self._position -= 1
        return self._events[self._position]

    @property
    def position(self) -> int:
        """Current position in trace."""
        return self._position

    @property
    def total_events(self) -> int | None:
        """Total events (None if not loaded)."""
        return len(self._events) if self._events else None

    async def seek(self, position: int) -> TraceEvent | None:
        """Jump to specific position."""
        await self._load()
        self._position = max(0, min(position, len(self._events)))
        return self._events[self._position] if self._position < len(self._events) else None
```

### Reference

- AsyncIterator pattern: standard library typing
## Acceptance
- [ ] `TraceReplayer` supports async iteration
- [ ] `step()` returns next event or None
- [ ] `step_back()` returns previous event
- [ ] `seek(position)` jumps to specific event
- [ ] `position` and `total_events` properties work
- [ ] Integration test: capture → replay → verify events match
## Done summary
- Created TraceReplayer class for stepping through stored traces
- Supports async iteration (async for event in replayer)
- Manual stepping: step(), step_back()
- Position control: seek(position), reset(), current()
- Properties: position, total_events
- Fixed protocol: load_trace is async generator (not async function)
- Verification: mypy and ruff pass
## Evidence
- Commits: e249744
- Tests:
- PRs: