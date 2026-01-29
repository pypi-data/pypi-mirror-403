# Phase 1: Bond Forensic Runtime Documentation

## Overview

Establish the Bond runtime as the "Forensic Runtime" for AI agents by building comprehensive MkDocs Material documentation that positions its full-spectrum streaming architecture as a differentiator for transparency and debugging.

## Scope

**In Scope:**
- MkDocs Material documentation site setup
- Landing page with "Forensic Runtime" positioning
- Quickstart guide with working examples
- Architecture documentation (StreamHandlers, BondAgent, Tools)
- API reference generation via mkdocstrings
- Custom branding (colors, CSS, theme)
- Fix version/metadata inconsistencies

**Out of Scope:**
- Adding new forensic features (replay, trace persistence) - positioning existing features only
- CI/CD for docs deployment (defer to Phase 2)
- GitHunter tool documentation (incomplete implementation)
- Contributing guide and changelog

## Approach

1. **Setup Infrastructure First** - Add MkDocs dependencies, create mkdocs.yml mirroring dataing structure
2. **Core Content Pages** - Build landing, quickstart, architecture docs in parallel
3. **API Reference** - Configure mkdocstrings with proper paths and verify docstring parsing
4. **Branding Layer** - Add custom CSS, Bond color palette, dark/light mode support
5. **Cleanup** - Fix version mismatch, update pyproject.toml metadata

## Quick Commands

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Build and serve docs locally
mkdocs serve

# Build static docs
mkdocs build
```

## Key Files

| Existing File | Purpose |
|---------------|---------|
| `src/bond/agent.py:28-73` | StreamHandlers - core forensic observability |
| `src/bond/agent.py:75-299` | BondAgent - dynamic persona, history management |
| `src/bond/utils.py:20-199` | Handler factories (WebSocket, SSE, Print) |
| `src/bond/tools/memory/` | Memory toolset pattern example |
| `src/bond/tools/schema/` | Schema toolset pattern example |

| New File | Purpose |
|----------|---------|
| `mkdocs.yml` | MkDocs Material configuration |
| `docs/index.md` | Landing page with hero |
| `docs/quickstart.md` | Getting started guide |
| `docs/architecture.md` | System architecture |
| `docs/api/` | Auto-generated API reference |
| `docs/stylesheets/extra.css` | Custom branding CSS |

## Reference Implementation

Follow patterns from `/Users/bordumb/workspace/repositories/dataing/docs/`:
- `mkdocs.yml` - Full MkDocs Material config with mkdocstrings
- `docs/index.md` - Hero landing with grid cards
- `docs/stylesheets/extra.css` - Dark/light mode CSS

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| mkdocstrings may not parse all docstrings | Verify docstrings are Google-style format |
| Version mismatch (0.0.1 vs 0.1.0) | Task to sync versions explicitly |
| Brand colors undefined | Choose palette during branding task |

## Acceptance Criteria

- [ ] `mkdocs serve` runs without errors
- [ ] Landing page renders with "Forensic Runtime" positioning
- [ ] Quickstart example runs successfully when copy-pasted
- [ ] API reference generates for BondAgent, StreamHandlers, utils
- [ ] Dark/light mode toggle works
- [ ] All internal links resolve correctly
