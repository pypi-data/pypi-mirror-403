# fn-1.4 Create architecture documentation

## Description

Create architecture documentation (docs/architecture.md) explaining Bond's core components and design decisions.

### Page Structure

1. **Overview Diagram**
   - Mermaid diagram showing: User → BondAgent → LLM → StreamHandlers → User
   - Show tool execution flow

2. **StreamHandlers - The Forensic Core**
   - Explain each callback and when it fires
   - Lifecycle: on_block_start → deltas → on_block_end
   - Content: on_text_delta, on_thinking_delta, on_tool_call_delta
   - Execution: on_tool_execute, on_tool_result
   - Completion: on_complete
   - Include sequence diagram

3. **BondAgent**
   - Generic typing: `BondAgent[DepsType]`
   - Constructor parameters
   - Run methods: run(), run_stream()
   - History management: get/set/clear/clone_with_history
   - Dynamic instructions for persona switching

4. **Handler Factories**
   - create_websocket_handlers()
   - create_sse_handlers()
   - create_print_handlers()
   - When to use each

5. **Tool Architecture**
   - Protocol pattern for backends
   - Toolset pattern (list of tools)
   - Example: memory toolset structure

6. **PydanticAI Integration**
   - How Bond wraps PydanticAI Agent
   - Type safety benefits
   - RunContext usage in tools

### Key Files

| Component | Path |
|-----------|------|
| StreamHandlers | `src/bond/agent.py:28-73` |
| BondAgent | `src/bond/agent.py:75-299` |
| Handler factories | `src/bond/utils.py:20-199` |
| Memory toolset | `src/bond/tools/memory/` |
| Schema toolset | `src/bond/tools/schema/` |
## Acceptance
- [ ] docs/architecture.md exists with complete documentation
- [ ] Overview mermaid diagram renders correctly
- [ ] All 8 StreamHandlers callbacks are documented
- [ ] BondAgent section covers constructor, run methods, and history
- [ ] Handler factories section explains when to use each type
- [ ] Tool architecture section references existing patterns
- [ ] Page includes working code snippets where appropriate
## Done summary
- Created comprehensive architecture documentation
- Added 2 mermaid diagrams: sequence diagram and event flowchart
- Documented all 8 StreamHandlers callbacks with tables
- Covered BondAgent constructor, run methods, dynamic_instructions, history
- Explained handler factories with use cases
- Documented tool architecture: protocols, backends, toolsets
- Added PydanticAI integration section

- Verified: `mkdocs build` completes successfully with mermaid rendering
## Evidence
- Commits: ad76102cba5ca49c76b68832ad4ce2cedc5adfd9
- Tests: mkdocs build
- PRs: