# GitHunter Toolset Completion

## Overview

Complete the GitHunter toolset by adding `tools.py` that wraps `GitHunterAdapter` methods as PydanticAI `Tool` objects. This follows the existing patterns established in `memory/tools.py` and `schema/tools.py`.

## Scope

### In Scope
- Create request/response Pydantic models for tool inputs
- Wrap 3 adapter methods as PydanticAI tools: `blame_line`, `find_pr_discussion`, `get_expert_for_file`
- Export toolset as `githunter_toolset: list[Tool[GitHunterProtocol]]`
- Add comprehensive tests following existing test patterns
- Update `__init__.py` exports
- Add documentation to API reference

### Out of Scope
- GitLab/Bitbucket support (GitHub only)
- `enrich_author` as a separate tool (internal use only)
- Caching layer for repeated calls
- New adapter functionality

## Approach

Follow the established toolset pattern:

1. **Request Models** (`_models.py`): Create Pydantic models for tool inputs
   - `BlameLineRequest(repo_path: str, file_path: str, line_no: int)`
   - `FindPRDiscussionRequest(repo_path: str, commit_hash: str)`
   - `GetExpertsRequest(repo_path: str, file_path: str, window_days: int = 90, limit: int = 3)`

2. **Tool Functions** (`tools.py`): Async functions with `RunContext[GitHunterProtocol]`
   - Convert string repo_path to Path internally
   - Catch adapter exceptions and convert to Error model returns
   - Include "Agent Usage" docstrings

3. **Toolset Export**: `githunter_toolset: list[Tool[GitHunterProtocol]]`

## Key Files

| File | Purpose |
|------|---------|
| `src/bond/tools/githunter/_models.py` | NEW - Request models |
| `src/bond/tools/githunter/tools.py` | NEW - Tool functions + toolset export |
| `src/bond/tools/githunter/__init__.py` | Update exports |
| `tests/unit/tools/githunter/test_tools.py` | NEW - Tool tests |
| `docs/api/tools.md` | Update API docs |

## Reuse Points

- **Pattern**: `src/bond/tools/memory/tools.py` (lines 45-144) - Tool function structure
- **Pattern**: `src/bond/tools/schema/tools.py` - Simpler toolset example
- **Error model**: `src/bond/tools/memory/_models.py:177-187` - Error return type
- **Test pattern**: `tests/unit/tools/schema/test_tools.py` - Mock protocol pattern
- **Protocol**: `src/bond/tools/githunter/_protocols.py` - Already complete
- **Adapter**: `src/bond/tools/githunter/_adapter.py` - Already complete

## Quick Commands

```bash
# Run GitHunter tests
uv run pytest tests/unit/tools/githunter/ -v

# Type check
uv run mypy src/bond/tools/githunter/

# Lint
uv run ruff check src/bond/tools/githunter/
```

## Acceptance

- [ ] `_models.py` contains 3 request models with validation
- [ ] `tools.py` exports `githunter_toolset` with 3 tools
- [ ] All tools handle adapter exceptions gracefully (return Error, don't raise)
- [ ] Tests pass with MockGitHunter protocol implementation
- [ ] `mypy` and `ruff` pass without errors
- [ ] API docs updated with GitHunter toolset section
- [ ] Exports available: `from bond.tools.githunter import githunter_toolset`

## References

- Memory toolset pattern: `src/bond/tools/memory/tools.py`
- Schema toolset pattern: `src/bond/tools/schema/tools.py`
- GitHunter protocol: `src/bond/tools/githunter/_protocols.py:14-91`
- GitHunter adapter: `src/bond/tools/githunter/_adapter.py`
- PydanticAI Tool docs: https://ai.pydantic.dev/tools/
