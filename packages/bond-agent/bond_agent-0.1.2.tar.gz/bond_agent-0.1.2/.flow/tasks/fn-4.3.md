# fn-4.3 Streaming transport (SSE)

## Description

Build the SSE streaming transport layer with `useBondStream` hook. Handle connection, disconnection, reconnection, and event dispatch.

## Implementation

1. Create `useBondStream(url)` hook:
   - EventSource connection management
   - Status tracking: idle, connecting, live, error
   - Pause control (buffer events when paused)
   - Event history storage for replay

2. Parse SSE format:
   - Handle `event:` and `data:` lines
   - Parse JSON payloads
   - Normalize to BondEvent type

3. Reconnection logic:
   - Detect disconnect vs error states
   - Exponential backoff for manual reconnect
   - Don't fight browser auto-reconnect

4. Cleanup:
   - Close EventSource on unmount
   - Clear buffers on disconnect

## Files to Create

- `ui/src/bond/useBondStream.ts` - Main streaming hook
- `ui/src/bond/useEventHistory.ts` - Event buffer for replay

## References

- Hook skeleton from plan.md lines 251-295
- [MDN EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- SSE format: `src/bond/utils.py:158-167`
## Acceptance
- [ ] `useBondStream` returns state, status, controls
- [ ] Calling `connect()` opens EventSource connection
- [ ] Status transitions: idle → connecting → live
- [ ] Incoming events dispatch to reducer
- [ ] Events are stored in history buffer
- [ ] `disconnect()` closes connection cleanly
- [ ] `setPaused(true)` stops applying events to state
- [ ] Paused events are buffered, not lost
- [ ] Connection errors set status to "error"
- [ ] EventSource cleanup on component unmount
## Done summary
- Created useBondStream hook with EventSource connection management
- Created useEventHistory hook for replay buffer
- Implemented pause control with event buffering

- Enables live streaming from SSE endpoints
- History buffer supports replay/scrub functionality

- `pnpm tsc --noEmit` passes without errors
## Evidence
- Commits: 49ac926b47703a6cec96b165db0dde6d035e8ff8
- Tests: pnpm tsc --noEmit
- PRs: