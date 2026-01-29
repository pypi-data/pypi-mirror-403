# fn-4.7 Demo mode (canned events)

## Description

Implement demo mode that plays pre-recorded events from a file, enabling perfect demos without a live backend.

## Implementation

### Demo Mode Uses TraceEvent Format (not wire format)

Demo/replay uses the richer `TraceEvent` schema which includes timing:
```typescript
interface TraceEvent {
  trace_id: string
  sequence: number
  timestamp: number    // Monotonic clock - use for replay timing
  wall_time: string    // ISO datetime
  event_type: string   // "text_delta", "tool_execute", etc.
  payload: object
}
```

This allows timing-accurate playback without hardcoding delays.

### Steps

1. Create demo events file:
   - `ui/public/demo-events.ndjson` — **TraceEvent format**
   - Pre-recorded realistic agent session
   - Include all event types: thinking, text, tool calls
   - Timestamps enable realistic replay timing

2. Replay from file hook:
   - `useBondReplayFromFile()`
   - Load NDJSON file
   - Use `timestamp` differences to drive playback timing
   - Normalize TraceEvents via `normalizeTraceEvent()`

3. Playback controls:
   - Play/Pause
   - Speed control: 1x, 2x, 0.5x
   - Jump to moment

4. Integration:
   - "Run Demo" button loads demo file
   - Clear indicator of demo vs live mode
   - Demo uses same timeline/inspector as live

## Files to Create

- `ui/public/demo-events.ndjson` - Pre-recorded events
- `ui/src/bond/useBondReplayFromFile.ts` - File replay hook
- `ui/src/ui/DemoControls.tsx` - Demo playback controls

## References

- Demo mode from plan.md lines 427-440
- Event format: `src/bond/trace/_models.py:38-60`
## Acceptance
- [ ] "Run Demo" button starts demo playback
- [ ] Demo events play with timing from `TraceEvent.timestamp`
- [ ] All block types appear: text, thinking, tool calls
- [ ] Play/Pause control works
- [ ] Speed control: 1x, 2x, 0.5x options
- [ ] Clear "Demo Mode" indicator visible
- [ ] Demo works without any backend connection
- [ ] Can produce flawless screen recording
## Done summary
## Summary
Implemented demo mode with pre-recorded event playback:
- useBondReplayFromFile.ts: Hook loading NDJSON TraceEvents with timestamp-based timing
- DemoControls.tsx: Playback UI with play/pause, speed control (0.5x/1x/2x), progress bar
- demo-events.ndjson: Realistic session with thinking, text, and tool call blocks
- Demo mode badge indicator

All acceptance criteria met.
## Evidence
- Commits:
- Tests:
- PRs: