# fn-4.6 Inspector panel

## Description

Build the inspector panel that shows details when a block is selected. Enable copying block data as JSON.

## Implementation

1. Selection state:
   - Click block to select
   - Track selected block ID
   - Highlight selected block

2. Inspector panel content:
   - Block type and ID
   - Full content (not truncated)
   - For tool blocks: tool_id, full args, result length
   - Timestamps (if available)
   - Raw event fragments (optional toggle)

3. Copy functionality:
   - "Copy as JSON" button
   - Format block data nicely
   - Show copy feedback (toast or checkmark)

4. Panel behavior:
   - Slides in from right when block selected
   - Click outside to deselect
   - Keyboard: Escape to close

## Files to Create

- `ui/src/ui/Inspector.tsx` - Inspector panel component
- `ui/src/ui/useSelection.ts` - Selection state hook

## References

- Inspector description from plan.md lines 409-425
## Acceptance
- [ ] Clicking a block selects it
- [ ] Selected block has visual highlight
- [ ] Inspector panel shows selected block details
- [ ] Inspector shows block type, ID, content
- [ ] Inspector shows tool_id and full args for tool blocks
- [ ] "Copy as JSON" button copies block data
- [ ] Copy shows feedback (checkmark or toast)
- [ ] Escape key closes inspector
- [ ] Clicking outside deselects block
## Done summary
## Summary
Implemented inspector panel with full block details:
- useSelection.ts: Hook with selection state, Escape key, click-outside deselection
- Inspector.tsx: Slide-in panel showing block type, ID, status, content
- Tool blocks show tool_id, tool name, full args, result
- Copy as JSON button with checkmark feedback
- AnimatePresence for smooth slide animations

All acceptance criteria met.
## Evidence
- Commits:
- Tests:
- PRs: