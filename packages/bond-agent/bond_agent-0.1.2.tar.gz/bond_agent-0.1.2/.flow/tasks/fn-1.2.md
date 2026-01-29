# fn-1.2 Create landing page with Forensic Runtime positioning

## Description

Create the landing page (docs/index.md) that positions Bond as the "Forensic Runtime" for AI agents.

### Key Messaging

**Tagline:** "The Forensic Runtime for AI Agents"

**Value Proposition:**
- See exactly what your agent is thinking (on_thinking_delta)
- Watch tool calls form in real-time (on_tool_call_delta)
- Observe every tool execution and result (on_tool_execute, on_tool_result)
- Full transparency - nothing hidden

**Differentiation from LangChain/raw APIs:**
- Full-spectrum streaming vs monolithic responses
- Dynamic persona switching without new agent instances
- Type-safe tools via PydanticAI

### Page Structure

1. **Hero Section**
   - Title: "Bond"
   - Subtitle: "The Forensic Runtime for AI Agents"
   - Brief description (2-3 sentences)
   - Quick install: `pip install bond`
   - CTA buttons: Get Started | API Reference

2. **Feature Cards** (grid layout)
   - Full-Spectrum Streaming
   - Dynamic Personas
   - Type-Safe Tools
   - Production Ready

3. **Quick Example**
   - Simple BondAgent with StreamHandlers
   - Show on_thinking_delta, on_tool_result callbacks

4. **Why Bond?**
   - Comparison table or bullet points vs alternatives

### Reference

- Pattern: `/Users/bordumb/workspace/repositories/dataing/docs/docs/index.md`
- StreamHandlers: `src/bond/agent.py:28-73`
## Acceptance
- [ ] docs/index.md exists with complete landing page
- [ ] Hero section includes "Forensic Runtime" positioning
- [ ] Feature cards render in grid layout
- [ ] Quick code example is syntactically correct Python
- [ ] Page renders correctly in both light and dark mode
## Done summary
- Created landing page with "Forensic Runtime" hero section
- Added 4 feature cards in grid layout (streaming, personas, type-safety, production)
- Included quick example with StreamHandlers callbacks
- Added comparison table vs Raw API and LangChain

- Positions Bond as transparent/observable alternative to existing agent libraries
- Provides clear value proposition for new users

- Verified: `mkdocs build` completes successfully
## Evidence
- Commits: c3d84a9af93f101ddc6d069dd077ffa1d1a65100
- Tests: mkdocs build
- PRs: