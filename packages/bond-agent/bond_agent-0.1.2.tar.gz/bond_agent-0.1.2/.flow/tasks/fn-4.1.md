# fn-4.1 Project scaffold + styling baseline

## Description

Set up the frontend project with Vite, React, TypeScript, Tailwind CSS, shadcn/ui, and Framer Motion. Create the app shell layout with header, sidebar, and main timeline area.

## Implementation

1. Create `ui/` directory in project root
2. Initialize Vite + React + TypeScript project
3. Install and configure Tailwind CSS v4
4. Initialize shadcn/ui with components: Card, Button, ScrollArea, Badge
5. Install Framer Motion (motion package)
6. Create minimal dark theme: `zinc-950` background, `zinc-800` borders
7. Implement App shell layout:
   - Header with logo, "Run Demo" and "Connect" buttons
   - **Run header/status line**: trace ID, status indicator, event count, connection state
   - Sidebar card showing session info
   - Main timeline area with ScrollArea

## Files to Create

- `ui/package.json` - dependencies
- `ui/vite.config.ts` - Vite config with path aliases
- `ui/tsconfig.json` - TypeScript config
- `ui/src/index.css` - Tailwind imports + CSS variables
- `ui/src/App.tsx` - Shell layout
- `ui/src/main.tsx` - Entry point
- `ui/index.html` - HTML template
- `ui/components.json` - shadcn/ui config

## References

- App shell layout from plan.md lines 44-90
- [Vite React setup](https://vite.dev/guide/)
- [shadcn/ui Vite installation](https://ui.shadcn.com/docs/installation/vite)
## Acceptance
- [ ] `pnpm dev` starts dev server without errors
- [ ] `pnpm tsc --noEmit` passes type check
- [ ] App loads with header showing "Bond" logo and buttons
- [ ] Sidebar shows "Session" card with placeholder text
- [ ] **Run header shows**: trace ID placeholder, status (idle), event count (0)
- [ ] **Connection indicator**: shows "disconnected" state
- [ ] Timeline area shows "Waiting for events..." placeholder
- [ ] Dark theme applied: zinc-950 background, zinc-800 borders
- [ ] Typography feels premium (not default browser styles)
## Done summary
- Created ui/ directory with Vite + React + TypeScript scaffold
- Configured Tailwind CSS v4 with @tailwindcss/vite plugin
- Added shadcn/ui components (Button, Card, ScrollArea, Badge) with dark theme
- Installed Framer Motion for animations

- Sets foundation for all subsequent UI tasks
- Dark theme and component library provide premium devtool aesthetic

- `pnpm tsc --noEmit` passes without errors
- Dev server starts successfully

- lib/utils.ts created for shadcn component utilities
## Evidence
- Commits: 852672a360959781775004d0561294b54a092e73
- Tests: pnpm tsc --noEmit
- PRs: