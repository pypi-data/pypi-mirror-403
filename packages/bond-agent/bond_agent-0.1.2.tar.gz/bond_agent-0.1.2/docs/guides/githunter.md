# GitHunter Toolset

The GitHunter toolset provides forensic code ownership analysis for AI agents. It enables agents to understand who wrote code, why changes were made, and who the experts are for any file.

## Overview

GitHunter wraps git operations to answer questions like:

- **"Who wrote this line?"** → `blame_line` returns author, commit, date, message
- **"Why was this changed?"** → `find_pr_discussion` returns PR title, body, comments
- **"Who should review this?"** → `get_file_experts` returns ranked contributors

## Quick Start

```python
from bond import BondAgent
from bond.tools.githunter import githunter_toolset, GitHunterAdapter

# Create the GitHunter adapter (implements GitHunterProtocol)
adapter = GitHunterAdapter()

# Create agent with GitHunter tools
agent = BondAgent(
    name="code-analyst",
    instructions="""You are a code analysis assistant.
    Use GitHunter tools to understand code ownership and history.""",
    model="anthropic:claude-sonnet-4-20250514",
    toolsets=[githunter_toolset],
    deps=adapter,
)

# Ask questions about code
result = await agent.ask(
    "Who wrote line 42 of src/auth/login.py and why?"
)
```

## Available Tools

### blame_line

Get blame information for a specific line of code.

```python
blame_line({
    "repo_path": "/path/to/repo",
    "file_path": "src/main.py",
    "line_no": 42
})
```

**Returns:** `BlameResult` with:

- `author`: Who last modified the line
- `commit_hash`: The commit that changed it
- `commit_date`: When it was changed
- `commit_message`: Why it was changed

### find_pr_discussion

Find the pull request discussion for a commit.

```python
find_pr_discussion({
    "repo_path": "/path/to/repo",
    "commit_hash": "abc123def"
})
```

**Returns:** `PRDiscussion` with:

- `pr_number`: The PR number
- `title`: PR title
- `body`: PR description
- `comments`: Discussion comments

### get_file_experts

Identify experts for a file based on commit frequency.

```python
get_file_experts({
    "repo_path": "/path/to/repo",
    "file_path": "src/auth/login.py",
    "window_days": 90,
    "limit": 3
})
```

**Returns:** List of `FileExpert` with:

- `author`: Contributor info
- `commit_count`: Number of commits to this file
- `last_commit_date`: Most recent contribution

## Use Cases

| Scenario | Tool | Example Query |
|----------|------|---------------|
| Debug a bug | `blame_line` | "Who wrote this problematic line?" |
| Understand a change | `find_pr_discussion` | "What was the reasoning behind this commit?" |
| Find reviewer | `get_file_experts` | "Who should review changes to this file?" |
| Code review | `blame_line` + `find_pr_discussion` | "Explain the history of this function" |

## Protocol Pattern

GitHunter uses Bond's protocol pattern for backend flexibility:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class GitHunterProtocol(Protocol):
    """Protocol for git forensics backends."""

    async def blame_line(
        self,
        repo_path: Path,
        file_path: str,
        line_no: int,
    ) -> BlameResult: ...

    async def find_pr_discussion(
        self,
        repo_path: Path,
        commit_hash: str,
    ) -> PRDiscussion | None: ...

    async def get_expert_for_file(
        self,
        repo_path: Path,
        file_path: str,
        window_days: int = 90,
        limit: int = 5,
    ) -> list[FileExpert]: ...
```

This allows you to implement custom backends (e.g., GitHub API, GitLab API) while keeping the same tool interface.

## Error Handling

All tools return `Error` on failure:

```python
from bond.tools.githunter import Error

result = await agent.ask("Who wrote line 9999 of nonexistent.py?")
# Agent receives Error(description="File not found: nonexistent.py")
```

The agent can handle errors gracefully and ask for clarification.

## See Also

- [API Reference: GitHunter](../api/tools.md#githunter-toolset) - Full type definitions
- [Architecture](../architecture.md) - Protocol pattern details
