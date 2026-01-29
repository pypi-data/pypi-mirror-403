# Trace Module

The trace module provides forensic capture and replay capabilities for Bond agent executions. Record all StreamHandlers events during runs and replay them later for debugging, auditing, and analysis.

## Quick Start

```python
from bond import (
    BondAgent,
    JSONFileTraceStore,
    create_capture_handlers,
    finalize_capture,
    TraceReplayer,
)

# Capture during execution
store = JSONFileTraceStore(".bond/traces")
handlers, trace_id = create_capture_handlers(store)
result = await agent.ask("What is the weather?", handlers=handlers)
await finalize_capture(store, trace_id)

# Replay later
replayer = TraceReplayer(store, trace_id)
async for event in replayer:
    print(f"{event.event_type}: {event.payload}")
```

## Event Types

All 8 StreamHandlers callbacks are captured:

| Event Type | Payload Keys | Description |
|------------|--------------|-------------|
| `block_start` | `kind`, `index` | New block started |
| `block_end` | `kind`, `index` | Block finished |
| `text_delta` | `text` | Incremental text |
| `thinking_delta` | `text` | Reasoning content |
| `tool_call_delta` | `name`, `args` | Tool call forming |
| `tool_execute` | `id`, `name`, `args` | Tool executing |
| `tool_result` | `id`, `name`, `result` | Tool returned |
| `complete` | `data` | Response finished |

---

## TraceEvent

::: bond.trace.TraceEvent
    options:
      show_source: true

---

## TraceMeta

::: bond.trace.TraceMeta
    options:
      show_source: true

---

## TraceStorageProtocol

::: bond.trace.TraceStorageProtocol
    options:
      show_source: true

---

## JSONFileTraceStore

::: bond.trace.JSONFileTraceStore
    options:
      show_source: false

---

## create_capture_handlers

::: bond.trace.create_capture_handlers
    options:
      show_source: false

---

## finalize_capture

::: bond.trace.finalize_capture
    options:
      show_source: false

---

## TraceReplayer

::: bond.trace.TraceReplayer
    options:
      show_source: true
