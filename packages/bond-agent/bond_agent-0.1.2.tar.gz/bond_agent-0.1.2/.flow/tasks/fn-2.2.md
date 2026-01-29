# fn-2.2 Implement GitHunter tool functions

## Description
Create tool functions in `src/bond/tools/githunter/tools.py` wrapping adapter methods.

### Tools to Implement

```python
async def blame_line(
    ctx: RunContext[GitHunterProtocol],
    request: BlameLineRequest,
) -> BlameResult | Error:
    """Get blame information for a specific line.

    Agent Usage: Call when you need to know who last modified a line of code,
    what commit changed it, and when.
    """
    try:
        return await ctx.deps.blame_line(
            repo_path=Path(request.repo_path),
            file_path=request.file_path,
            line_no=request.line_no,
        )
    except GitHunterError as e:
        return Error(message=str(e))

async def find_pr_discussion(
    ctx: RunContext[GitHunterProtocol],
    request: FindPRDiscussionRequest,
) -> PRDiscussion | None | Error:
    """Find the PR discussion for a commit."""
    ...

async def get_file_experts(
    ctx: RunContext[GitHunterProtocol],
    request: GetExpertsRequest,
) -> list[FileExpert] | Error:
    """Get experts for a file based on commit frequency."""
    ...
```

### Export

```python
githunter_toolset: list[Tool[GitHunterProtocol]] = [
    Tool(blame_line),
    Tool(find_pr_discussion),
    Tool(get_file_experts),
]
```

### Reference Files

- Pattern: `src/bond/tools/memory/tools.py:45-144`
- Protocol: `src/bond/tools/githunter/_protocols.py`
- Exceptions: `src/bond/tools/githunter/_exceptions.py`
## Acceptance
- [ ] `tools.py` contains 3 async tool functions
- [ ] All tools use `RunContext[GitHunterProtocol]` dependency injection
- [ ] All tools catch `GitHunterError` and return `Error` model
- [ ] All tools have "Agent Usage" in docstrings
- [ ] `githunter_toolset` list is exported
- [ ] `mypy` and `ruff` pass on `tools.py`
## Done summary
Created tools.py with 3 PydanticAI tool functions:
- blame_line: Gets blame info (author, commit, date) for a line
- find_pr_discussion: Finds PR discussion for a commit hash
- get_file_experts: Gets file experts by commit frequency

All tools:
- Use RunContext[GitHunterProtocol] for dependency injection
- Catch GitHunterError and return Error model
- Have detailed "Agent Usage" docstrings with examples

Exports githunter_toolset list for BondAgent integration.
Passed mypy and ruff checks.
## Evidence
- Commits: 2d87f6a
- Tests:
- PRs: