# fn-1.5 Configure API reference generation with mkdocstrings

## Description

Configure mkdocstrings to auto-generate API reference documentation from docstrings.

### Steps

1. **Update mkdocs.yml plugin config**
   ```yaml
   plugins:
     - mkdocstrings:
         handlers:
           python:
             paths: [src]
             options:
               docstring_section_style: list
               ignore_init_summary: true
               merge_init_into_class: true
               inherited_members: true
               summary: true
               show_symbol_type_heading: true
               signature_crossrefs: true
               line_length: 88
   ```

2. **Create API reference pages**
   - `docs/api/index.md` - Overview
   - `docs/api/agent.md` - BondAgent, StreamHandlers
   - `docs/api/utils.md` - Handler factories
   - `docs/api/tools.md` - Tool patterns (memory, schema)

3. **Verify docstrings parse correctly**
   - Check BondAgent docstrings are Google-style
   - Check StreamHandlers field docstrings
   - Check tool function docstrings

4. **Update navigation**
   - Add API Reference section with sub-pages

### Key Files

| Source | Docstrings to verify |
|--------|---------------------|
| `src/bond/agent.py` | BondAgent, StreamHandlers |
| `src/bond/utils.py` | Handler factory functions |
| `src/bond/tools/memory/tools.py` | Memory tools (already has "Agent Usage:" sections) |

### Reference

- mkdocstrings-python: https://mkdocstrings.github.io/python/
- Dataing config: `/Users/bordumb/workspace/repositories/dataing/docs/mkdocs.yml`
## Acceptance
- [ ] docs/api/index.md exists with API reference overview
- [ ] docs/api/agent.md generates BondAgent and StreamHandlers docs
- [ ] docs/api/utils.md generates handler factory docs
- [ ] `mkdocs build` completes without mkdocstrings errors
- [ ] Type annotations in signatures link to their definitions
- [ ] All public classes/functions have rendered documentation
## Done summary
- Updated mkdocs.yml nav with API Reference sub-pages
- Created docs/api/agent.md for BondAgent and StreamHandlers auto-docs
- Created docs/api/utils.md for handler factory auto-docs
- Created docs/api/tools.md for memory and schema toolset auto-docs
- Updated docs/api/index.md with module overview and quick links

- mkdocstrings now generates documentation from source docstrings
- All public classes/functions have rendered documentation

- Verified: `mkdocs build` completes without mkdocstrings errors
## Evidence
- Commits: a367dfc2fe0d9491ff92349ad622d7a0da7b257b
- Tests: mkdocs build
- PRs: