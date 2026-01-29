# Bond UI - Forensic Timeline Frontend

## Overview

A polished single-page web app that connects to Bond's streaming endpoints (SSE or WebSocket), renders the agent lifecycle as a live timeline (text/thinking/tool-call/tool-result), and supports "replay mode" (scrub + pause) for forensic debugging.

## Scope

**In Scope:**
- React + Vite + Tailwind + shadcn/ui + Framer Motion frontend
- SSE streaming transport (WebSocket optional follow-up)
- Event-driven store: BondEvents → Blocks reducer
- Timeline rendering with text/thinking/tool_call blocks
- Replay mode with pause/scrub functionality
- Inspector panel for block details
- Demo mode with pre-recorded events
- Dark mode only (premium devtool aesthetic)
- **Run header + status line** (trace ID, status, event count, connection indicator)
- **Active cursor affordance** (soft glow + shimmer on streaming block)

**Out of Scope:**
- Authentication, accounts, persistence
- Multi-run browsing
- Complex theming system
- Backend modifications (beyond simple stream endpoint if needed)
- Mobile/responsive design

## Approach

### Architecture
- **State**: Event-driven reducer pattern - store full event stream, derive visible blocks
- **Transport**: EventSource API with reconnection and cleanup
- **Rendering**: Framer Motion for block animations, shadcn/ui primitives
- **Replay**: Client-side re-reduction from event history (optimize with caching if needed)

### Two-Mode Event Story (Critical)

The UI handles two distinct event formats:

**Live Mode (WS/SSE frames)** — tiny payloads, maximum responsiveness:
```json
{"t":"block_start","kind":"text","idx":0}
{"t":"text","c":"Hello"}
{"t":"thinking","c":"Let me think..."}
{"t":"tool_delta","n":"read_file","a":"{\"path\":"}
{"t":"tool_exec","id":"call_123","name":"read_file","args":{"path":"/foo"}}
{"t":"tool_result","id":"call_123","name":"read_file","result":"contents..."}
{"t":"block_end","kind":"text","idx":0}
{"t":"complete","data":null}
```

SSE uses named event types: `event: text\ndata: {"c": "Hello"}`

**Replay/Demo Mode (TraceEvent NDJSON)** — richer metadata + timing:
- Uses `TraceEvent` schema with `timestamp` + `wall_time`
- Demo file: `ui/public/demo-events.ndjson`
- Timing driven by `timestamp` field (monotonic clock)

This separation prevents forcing trace semantics onto live streaming.

### Key Technical Decisions
1. **Event normalization**: Map wire format (`t/n/a/c/idx`) to internal BondEvent type
2. **Block correlation**: Use `(kind, index)` for block ID; tool calls correlated by `id` field
3. **Tool delta handling**: Attach to currently active tool_call block (no id in delta)
4. **Auto-scroll**: Intersection Observer, only auto-scroll when at bottom
5. **High-frequency batching**: requestAnimationFrame batching (add virtualization only if needed)

### Backend Integration
The UI connects to Bond's existing streaming infrastructure:
- `create_sse_handlers()` from `src/bond/utils.py:125-167`
- `create_websocket_handlers()` from `src/bond/utils.py:20-122`
- TraceEvent schema from `src/bond/trace/_models.py:38-60`

**Note:** Bond provides handlers, not routes. The UI takes a URL via env var + input field.

## Quick Commands

```bash
# Start development server
cd ui && pnpm dev

# Type check
cd ui && pnpm tsc --noEmit

# Build for production
cd ui && pnpm build

# Run with demo mode (no backend needed)
cd ui && pnpm dev  # Then click "Run Demo"
```

## Acceptance Criteria

- [ ] App loads with clean shell (header + sidebar + timeline)
- [ ] **Run header shows**: trace ID/name, status (live/paused/replay), event count
- [ ] **Connection indicator** shows latency/disconnect state
- [ ] Can connect to SSE endpoint and see blocks appear live
- [ ] Text blocks render with prose styling
- [ ] Thinking blocks are visually distinct (subtle, collapsible)
- [ ] Tool blocks show streaming args, status pill, result panel
- [ ] **Active cursor**: currently streaming block has soft glow + subtle shimmer
- [ ] Can pause stream and scrub timeline backwards
- [ ] Can click any block to see details in inspector panel
- [ ] Demo mode plays canned events without backend (using TraceEvent timing)
- [ ] Keyboard shortcuts work (Space=pause, L=live, J/K=step)
- [ ] UI feels like Linear/Vercel quality, not "React starter"

## Resolved Questions (from review)

### Wire Format — Canonical
The wire format is defined in `create_websocket_handlers()`:
- `{"t":"block_start","kind":str,"idx":int}`
- `{"t":"text","c":str}` / `{"t":"thinking","c":str}`
- `{"t":"tool_delta","n":str,"a":str}`
- `{"t":"tool_exec","id":str,"name":str,"args":dict}`
- `{"t":"tool_result","id":str,"name":str,"result":str}`
- `{"t":"complete","data":Any}`

SSE uses `send(event_type, data)` — named event types work perfectly with EventSource.

### Block Kind Values
Treat `kind` as opaque enum string from PydanticAI (`TextPartDelta`, `ThinkingPartDelta`, `ToolCallPartDelta`). Style-map known values, handle unknowns safely.

### Parallel Tool Correlation
Tool execution and result are correlated by `id` field. `tool_delta` doesn't include id — attach to currently active tool_call block.

### Timestamps for Replay
- Live streams don't include timestamps (not needed)
- Demo/replay uses `TraceEvent.timestamp` (monotonic) for timing
- Alternative: fixed cadence client-side for simpler demos

### Maximum Event Rate
Implement requestAnimationFrame batching early. Add virtualization only if perf issues arise.

## Edge Cases to Handle

- Empty stream (timeout/loading state)
- Very long tool results (truncate/lazy-load)
- Stream disconnect mid-block (show "interrupted" state)
- Browser tab backgrounded (catch-up on focus)
- Invalid JSON in payloads (graceful degradation)
- Unknown `kind` values (render as generic block)

## References

### Backend Code
- Event types: `src/bond/trace/_models.py:14-23`
- TraceEvent model: `src/bond/trace/_models.py:38-60`
- SSE handlers: `src/bond/utils.py:125-167`
- WebSocket handlers: `src/bond/utils.py:20-122`
- StreamHandlers: `src/bond/agent.py:28-74`
- TraceReplayer: `src/bond/trace/replay.py:15-145`

### Documentation
- [Vite + React Setup](https://vite.dev/guide/)
- [shadcn/ui Installation](https://ui.shadcn.com/docs/installation/vite)
- [Framer Motion Lists](https://motion.dev/docs/react-animate-presence)
- [MDN EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
