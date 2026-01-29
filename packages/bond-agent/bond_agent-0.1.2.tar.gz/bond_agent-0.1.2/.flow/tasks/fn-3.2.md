# fn-3.2 Implement JSON file storage backend

## Description
Implement JSON file storage backend in `src/bond/trace/backends/`.

### File Structure

```
src/bond/trace/backends/
├── __init__.py
└── json_file.py
```

### JSONFileTraceStore

```python
class JSONFileTraceStore:
    """Store traces as JSON files in a directory.

    Structure:
        {base_path}/
        ├── {trace_id}.json       # Events (one JSON object per line)
        └── {trace_id}.meta.json  # TraceMeta
    """

    def __init__(self, base_path: Path | str = ".bond/traces"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_event(self, event: TraceEvent) -> None:
        """Append event to trace file (newline-delimited JSON)."""
        path = self.base_path / f"{event.trace_id}.json"
        async with aiofiles.open(path, "a") as f:
            await f.write(json.dumps(event.to_dict()) + "\n")

    async def finalize_trace(self, trace_id: str, status: str = "complete") -> None:
        """Write meta file marking trace complete."""
        ...

    async def load_trace(self, trace_id: str) -> AsyncIterator[TraceEvent]:
        """Read events from trace file."""
        path = self.base_path / f"{trace_id}.json"
        async with aiofiles.open(path, "r") as f:
            async for line in f:
                yield TraceEvent.from_dict(json.loads(line))

    async def list_traces(self, limit: int = 100) -> list[TraceMeta]:
        """List traces sorted by creation time (newest first)."""
        ...

    async def delete_trace(self, trace_id: str) -> None:
        """Delete trace and meta files."""
        ...
```

### Dependencies

Add to pyproject.toml:
```toml
"aiofiles>=24.0.0",
```

### Reference

- Memory backend pattern: `src/bond/tools/memory/backends/`
## Acceptance
- [ ] `JSONFileTraceStore` implements `TraceStorageProtocol`
- [ ] Events stored as newline-delimited JSON
- [ ] Meta files track trace status and event count
- [ ] `list_traces` returns TraceMeta sorted by time
- [ ] `delete_trace` cleans up both files
- [ ] aiofiles added to dependencies
- [ ] `mypy` passes
## Done summary
- Created JSONFileTraceStore implementing TraceStorageProtocol
- Events stored as newline-delimited JSON for efficient streaming
- Meta files track trace status and event count
- Added aiofiles and types-aiofiles dependencies
- Verification: mypy and ruff pass on src/bond/trace/
## Evidence
- Commits: 53582a0
- Tests:
- PRs: