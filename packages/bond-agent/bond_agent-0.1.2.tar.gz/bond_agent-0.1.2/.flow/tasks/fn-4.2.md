# fn-4.2 Event schema + block model

## Description

Define TypeScript types for Bond events and the Block model. Implement the reducer that transforms streaming events into renderable blocks.

## Implementation

### Two-Mode Event Story

The UI handles two distinct formats:

**Live Mode (canonical wire format from `create_websocket_handlers()`):**
```json
{"t":"block_start","kind":"text","idx":0}
{"t":"text","c":"Hello"}
{"t":"thinking","c":"Let me think..."}
{"t":"tool_delta","n":"read_file","a":"{\"path\":"}
{"t":"tool_exec","id":"call_123","name":"read_file","args":{"path":"/foo"}}
{"t":"tool_result","id":"call_123","name":"read_file","result":"..."}
{"t":"block_end","kind":"text","idx":0}
{"t":"complete","data":null}
```

SSE uses named event types: `event: text\ndata: {"c": "Hello"}`

**Replay/Demo Mode (TraceEvent NDJSON):**
- Uses full `TraceEvent` schema with `timestamp` + `wall_time`
- Richer metadata for timing-accurate replay

### Steps

1. Define `WireEvent` type matching canonical wire format (`t/n/a/c/idx`)

2. Define internal `BondEvent` union type (normalized):
   - `block_start`, `block_end` (kind, index)
   - `text_delta`, `thinking_delta` (content)
   - `tool_call_delta` (name, args deltas)
   - `tool_execute`, `tool_result` (id, name, args/result)
   - `complete`

3. Define `Block` type:
   - Text block: id, kind, content, isClosed, **isActive**
   - Thinking block: id, kind, content, isClosed, **isActive**
   - Tool block: id, kind, draft state, final state, status, result, **isActive**

4. Create normalization layer:
   - `normalizeWireEvent(wire: WireEvent): BondEvent`
   - `normalizeSSEEvent(type: string, data: object): BondEvent`
   - `normalizeTraceEvent(trace: TraceEvent): BondEvent`

5. Implement reducer:
   - Handle block_start: create new block, mark as active
   - Handle deltas: append to active block
   - Handle tool_execute: transition to "executing", correlate by `id`
   - Handle tool_result: attach result by `id`, mark "done"
   - Handle block_end: close block, clear active state

**Key insight:** `tool_delta` has no `id` — attach to currently active tool_call block.

## Files to Create

- `ui/src/bond/types.ts` - WireEvent, BondEvent, Block, TraceEvent types
- `ui/src/bond/reducer.ts` - Event reducer with active block tracking
- `ui/src/bond/normalize.ts` - Normalization for WS/SSE/TraceEvent formats

## References

- Type definitions from plan.md lines 109-143
- Reducer skeleton from plan.md lines 144-230
- Backend event types: `src/bond/trace/_models.py:14-23`
- SSE format: `src/bond/utils.py:158-167`
## Acceptance
- [ ] `WireEvent` type matches canonical wire format (`t/n/a/c/idx`)
- [ ] `BondEvent` type covers all 8 normalized event types
- [ ] `Block` type supports text, thinking, tool_call with `isActive` flag
- [ ] `normalizeWireEvent()` converts wire format to BondEvent
- [ ] `normalizeSSEEvent()` handles named SSE event types
- [ ] `normalizeTraceEvent()` handles TraceEvent for replay/demo
- [ ] Reducer tracks active block and marks it correctly
- [ ] Reducer handles tool_delta attaching to active tool_call block
- [ ] Reducer correlates tool_execute/tool_result by `id` field
- [ ] Unknown `kind` values handled gracefully (generic block)
## Done summary
- Created types.ts with WireEvent, BondEvent, Block, TraceEvent types
- Created normalize.ts with normalizeWireEvent, normalizeSSEEvent, normalizeTraceEvent
- Created reducer.ts with bondReducer and reduceEvents helper

- Establishes foundation for streaming transport and timeline rendering
- Two-mode event story cleanly separates live vs replay formats

- `pnpm tsc --noEmit` passes without errors
- All type definitions match canonical wire format from backend
## Evidence
- Commits: 572993dbf3ce2cad47d093be9f5c904a41d3691c
- Tests: pnpm tsc --noEmit
- PRs: