# fn-4.4 Timeline rendering

## Description

Build the timeline UI that renders blocks with appropriate styling and animations. This is the core visual component.

## Implementation

1. Create `Timeline` component:
   - Receives blocks array
   - Renders list with Framer Motion animations
   - Auto-scroll to bottom when new blocks arrive

2. Create `BlockCard` variants:
   - Text block: clean prose, `text-zinc-50`
   - Thinking block: subtle, collapsible, `text-zinc-300`, "Thinking" label
   - Tool block: name, args (monospace), status badge, result panel
   - Unknown kind: generic fallback block

3. **Active cursor affordance** (the "it's alive" visual):
   - Active block (isActive=true) has soft glow border
   - Subtle caret/shimmer animation on streaming content
   - Makes the UI feel responsive and alive

4. Animations:
   - Slide/fade-in as blocks appear (`initial`, `animate`)
   - Use `AnimatePresence` for list
   - Stable keys from block.id

5. Auto-scroll:
   - Intersection Observer on bottom sentinel
   - Only auto-scroll when user is at bottom
   - Show "scroll to bottom" when scrolled up

## Files to Create

- `ui/src/ui/Timeline.tsx` - Main timeline component
- `ui/src/ui/BlockCard.tsx` - Block rendering variants
- `ui/src/ui/TextBlock.tsx` - Text block component
- `ui/src/ui/ThinkingBlock.tsx` - Thinking block component
- `ui/src/ui/ToolBlock.tsx` - Tool block component

## References

- Block renderer from plan.md lines 318-385
- Status badge styling from plan.md lines 324-326
## Acceptance
- [ ] Timeline renders list of blocks
- [ ] Text blocks show content with prose styling
- [ ] Thinking blocks show "Thinking" label, dimmer text
- [ ] Tool blocks show tool name and status badge
- [ ] Tool blocks show streaming args in monospace
- [ ] Tool blocks show result panel when done
- [ ] New blocks animate in (fade + slide)
- [ ] **Active block has soft glow border**
- [ ] **Streaming content shows subtle shimmer/caret**
- [ ] Unknown `kind` values render as generic block
- [ ] Auto-scroll follows new blocks when at bottom
- [ ] User can scroll up without fighting auto-scroll
- [ ] "Scroll to bottom" button appears when scrolled up
## Done summary
## Summary
Implemented timeline rendering components with Framer Motion animations:
- Timeline.tsx: Main component with auto-scroll using Intersection Observer
- BlockCard.tsx: Wrapper with active cursor affordance (glow + shimmer)
- TextBlock.tsx: Renders text content with prose styling
- ThinkingBlock.tsx: Collapsible thinking/reasoning display
- ToolBlock.tsx: Tool calls with status badges (forming/executing/done)
- Added shimmer animation keyframes to index.css

All components follow the design spec with dark theme styling.
## Evidence
- Commits:
- Tests:
- PRs: