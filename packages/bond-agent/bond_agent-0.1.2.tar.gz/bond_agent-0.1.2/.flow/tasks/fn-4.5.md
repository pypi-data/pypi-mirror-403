# fn-4.5 Replay mode (pause + scrub)

## Description

Implement replay mode allowing users to pause the stream, scrub through event history, and jump back to live.

## Implementation

1. Store full event history (separate from visible state)

2. Replay controls:
   - Pause button to stop applying new events
   - Slider from 0..N events
   - "Live" vs "Replay" indicator

3. Scrubber logic:
   - On scrub, re-reduce events from 0..K
   - Debounce scrubber input for performance
   - Cache intermediate states if needed

4. Live jump:
   - Button to jump back to live position
   - Resume auto-scroll

5. State management:
   - Track replay position separately from event count
   - Derive visible blocks from position

## Files to Create/Modify

- `ui/src/bond/useReplayState.ts` - Replay state management
- `ui/src/ui/ReplayControls.tsx` - Scrubber and controls
- `ui/src/ui/Timeline.tsx` - Integrate replay state

## References

- Replay description from plan.md lines 390-406
- Backend TraceReplayer pattern: `src/bond/trace/replay.py:15-145`
## Acceptance
- [ ] Pause button stops applying new events to timeline
- [ ] Events continue buffering while paused
- [ ] Scrubber slider shows 0..N range
- [ ] Dragging scrubber updates visible blocks
- [ ] "Live" indicator shows when at latest position
- [ ] "Replay" indicator shows when scrubbed back
- [ ] "Jump to Live" button returns to current position
- [ ] Scrubber is debounced (no lag on fast drag)
- [ ] Can pause, scrub back, then resume at paused position
## Done summary
## Summary
Implemented replay mode with pause and scrub functionality:
- useReplayState.ts: Hook managing replay position, mode (live/replay), and derived visible state
- ReplayControls.tsx: UI component with play/pause, slider, live/replay indicator, jump-to-live
- Includes state caching at intervals for smooth scrubbing
- Debounced scrubber input for performance

All acceptance criteria met: pause, buffer, scrub, indicators, jump-to-live.
## Evidence
- Commits:
- Tests:
- PRs: