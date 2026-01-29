# fn-3.5 Add tests and documentation

## Description
Add comprehensive tests and update documentation.

### Tests to Add

```
tests/unit/trace/
├── __init__.py
├── test_models.py      # TraceEvent serialization
├── test_json_store.py  # JSONFileTraceStore
├── test_capture.py     # create_capture_handlers
└── test_replay.py      # TraceReplayer
```

### Test Cases

**test_models.py**:
- TraceEvent to_dict/from_dict roundtrip
- All 8 event types serialize correctly
- TraceMeta creation

**test_json_store.py**:
- save_event appends to file
- load_trace returns events in order
- finalize_trace creates meta file
- list_traces returns sorted results
- delete_trace removes files

**test_capture.py**:
- create_capture_handlers returns handlers + trace_id
- Captured events have correct sequence numbers
- Events persisted to storage

**test_replay.py**:
- Iteration yields all events
- step() advances position
- step_back() moves backward
- seek() jumps to position

### Documentation Updates

1. Add to `docs/architecture.md`:
   - New "Trace Persistence" section
   - "Replay" section with examples

2. Update `docs/api/index.md`:
   - Add trace module link

3. Create `docs/api/trace.md`:
   - Module overview
   - TraceEvent reference
   - TraceStorageProtocol reference
   - JSONFileTraceStore reference
   - create_capture_handlers reference
   - TraceReplayer reference

### Exports

Update `src/bond/__init__.py`:
```python
from bond.trace import (
    TraceEvent,
    TraceMeta,
    TraceStorageProtocol,
    JSONFileTraceStore,
    create_capture_handlers,
    finalize_capture,
    TraceReplayer,
)
```
## Acceptance
- [ ] All test files created with >80% coverage
- [ ] `uv run pytest tests/unit/trace/ -v` passes
- [ ] `docs/api/trace.md` documents all public APIs
- [ ] `docs/architecture.md` has Trace Persistence section
- [ ] Main `__init__.py` exports trace module classes
- [ ] `from bond import create_capture_handlers, TraceReplayer` works
- [ ] `mkdocs build --strict` passes
## Done summary
# Task fn-3.5: Add tests and documentation

## Completed Work

1. **Unit tests (62 tests, all passing)**:
   - `tests/unit/trace/test_models.py` - TraceEvent/TraceMeta serialization
   - `tests/unit/trace/test_json_store.py` - JSONFileTraceStore operations
   - `tests/unit/trace/test_capture.py` - create_capture_handlers factory
   - `tests/unit/trace/test_replay.py` - TraceReplayer navigation

2. **Package exports**:
   - Updated `src/bond/__init__.py` with all trace types

3. **Documentation**:
   - Created `docs/api/trace.md` with API reference
   - Added Trace Persistence section to `docs/architecture.md`
   - Added trace to mkdocs.yml navigation

## Acceptance Criteria Met
- All 62 unit tests pass
- mkdocs build --strict passes
- ruff and mypy pass on trace module
## Evidence
- Commits:
- Tests: 62 passed
- PRs: