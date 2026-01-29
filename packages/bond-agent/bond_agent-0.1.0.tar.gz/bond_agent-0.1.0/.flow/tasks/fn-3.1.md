# fn-3.1 Create trace event models and protocol

## Description
Create trace event models and storage protocol in `src/bond/trace/`.

### Create Module Structure

```
src/bond/trace/
├── __init__.py
├── _models.py      # TraceEvent, TraceMeta
└── _protocols.py   # TraceStorageProtocol
```

### TraceEvent Model

```python
@dataclass(frozen=True)
class TraceEvent:
    trace_id: str           # UUID
    sequence: int           # Order within trace (0-indexed)
    timestamp: float        # time.monotonic() for relative ordering
    wall_time: datetime     # ISO timestamp for display
    event_type: str         # One of the 8 callback types
    payload: dict[str, Any] # Event-specific data

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON storage."""
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TraceEvent:
        """Deserialize from JSON."""
        ...
```

### TraceMeta Model

```python
@dataclass(frozen=True)
class TraceMeta:
    trace_id: str
    created_at: datetime
    event_count: int
    status: str  # "in_progress", "complete", "failed"
```

### TraceStorageProtocol

```python
@runtime_checkable
class TraceStorageProtocol(Protocol):
    async def save_event(self, event: TraceEvent) -> None: ...
    async def finalize_trace(self, trace_id: str, status: str = "complete") -> None: ...
    async def load_trace(self, trace_id: str) -> AsyncIterator[TraceEvent]: ...
    async def list_traces(self, limit: int = 100) -> list[TraceMeta]: ...
    async def delete_trace(self, trace_id: str) -> None: ...
```

### Reference

- StreamHandlers callbacks: `src/bond/agent.py:28-73`
- Memory protocol pattern: `src/bond/tools/memory/_protocols.py`
## Acceptance
- [ ] `src/bond/trace/_models.py` contains TraceEvent and TraceMeta
- [ ] TraceEvent has to_dict/from_dict for JSON serialization
- [ ] event_type covers all 8 StreamHandler callbacks
- [ ] `src/bond/trace/_protocols.py` defines TraceStorageProtocol
- [ ] Protocol is @runtime_checkable
- [ ] `mypy src/bond/trace/` passes
## Done summary
- Created src/bond/trace/ module with TraceEvent, TraceMeta models
- TraceEvent captures all 8 StreamHandlers callback types with to_dict/from_dict
- TraceMeta provides summary info (trace_id, created_at, event_count, status)
- TraceStorageProtocol defines @runtime_checkable interface for backends
- Verification: mypy and ruff pass on src/bond/trace/
## Evidence
- Commits: d01a07b
- Tests:
- PRs: