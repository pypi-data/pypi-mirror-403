# fn-1.3 Create quickstart guide with working examples

## Description

Create a quickstart guide (docs/quickstart.md) with working examples that users can copy-paste and run.

### Page Structure

1. **Installation**
   ```bash
   pip install bond
   ```

2. **Your First Agent**
   - Minimal BondAgent example
   - Simple tool definition
   - Sync run example

3. **Adding Streaming Handlers**
   - Create StreamHandlers with callbacks
   - Show print handlers (simplest)
   - Explain each callback purpose

4. **Dynamic Instructions**
   - Show persona switching with dynamic_instructions
   - Example: analyst vs DBA persona

5. **Using Toolsets**
   - Brief intro to bundled toolsets
   - Link to Architecture for details

### Requirements

- All code examples must be runnable
- Use `create_print_handlers()` from utils for simplest demo
- Include expected output where helpful
- Tabbed code blocks for sync/async variants

### Key Files

| Source | Path |
|--------|------|
| BondAgent | `src/bond/agent.py:75-299` |
| StreamHandlers | `src/bond/agent.py:28-73` |
| create_print_handlers | `src/bond/utils.py:164-199` |
## Acceptance
- [ ] docs/quickstart.md exists with complete guide
- [ ] All code examples are syntactically valid Python
- [ ] First example runs without additional dependencies (except anthropic API key)
- [ ] StreamHandlers example shows at least 3 callback types
- [ ] Dynamic instructions example is included
- [ ] Page renders correctly with proper code highlighting
## Done summary
- Created comprehensive quickstart with async/sync tabs
- Added StreamHandlers section with all 8 callbacks
- Included pre-built handlers (create_print_handlers)
- Added dynamic_instructions persona switching example
- Added tool definition and bundled toolsets examples

- All code examples are syntactically valid Python
- Uses tabbed content for sync/async variants

- Verified: `mkdocs build` completes successfully
## Evidence
- Commits: 2db750797dda6ae5805d1b82112820a3a4d185c7
- Tests: mkdocs build
- PRs: