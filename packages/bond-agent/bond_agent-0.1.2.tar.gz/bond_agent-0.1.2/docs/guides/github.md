# GitHub Toolset

The GitHub toolset enables agents to browse and analyze any GitHub repository. Agents can read files, search code, explore commit history, and inspect pull requests.

## Overview

GitHub tools answer questions like:

- **"What's in this repo?"** → `github_get_repo` + `github_list_files`
- **"Show me this file"** → `github_read_file`
- **"Where is X defined?"** → `github_search_code`
- **"What changed recently?"** → `github_get_commits`
- **"What does this PR do?"** → `github_get_pr`

## Quick Start

```python
import os
from bond import BondAgent
from bond.tools.github import github_toolset, GitHubAdapter

# Create adapter with GitHub token
adapter = GitHubAdapter(token=os.environ["GITHUB_TOKEN"])

# Create agent with GitHub tools
agent = BondAgent(
    name="code-explorer",
    instructions="""You help users understand GitHub repositories.
    Browse files, search code, and explain what you find.""",
    model="openai:gpt-4o",
    toolsets=[github_toolset],
    deps=adapter,
)

# Explore a repository
result = await agent.ask("What is the facebook/react repository about?")
```

## Available Tools

### github_get_repo

Get repository metadata.

```python
github_get_repo({
    "owner": "facebook",
    "repo": "react"
})
```

**Returns:** `RepoInfo` with description, default branch, topics, stars, forks.

### github_list_files

List directory contents.

```python
github_list_files({
    "owner": "facebook",
    "repo": "react",
    "path": "packages/react/src",
    "ref": "main"  # optional: branch, tag, or commit
})
```

**Returns:** List of `TreeEntry` with name, path, type (file/dir), size.

### github_read_file

Read file content.

```python
github_read_file({
    "owner": "facebook",
    "repo": "react",
    "path": "packages/react/package.json",
    "ref": "main"
})
```

**Returns:** `FileContent` with decoded content, size, SHA.

### github_search_code

Search code within a repository.

```python
github_search_code({
    "query": "useState",
    "owner": "facebook",
    "repo": "react",
    "limit": 10
})
```

**Returns:** List of `CodeSearchResult` with file paths and matching fragments.

### github_get_commits

Get recent commits.

```python
github_get_commits({
    "owner": "facebook",
    "repo": "react",
    "path": "packages/react/src/React.js",  # optional: filter by file
    "limit": 10
})
```

**Returns:** List of `Commit` with SHA, message, author, date.

### github_get_pr

Get pull request details.

```python
github_get_pr({
    "owner": "facebook",
    "repo": "react",
    "number": 25000
})
```

**Returns:** `PullRequest` with title, body, state, author, merge status.

## Authentication

GitHub tools require a personal access token:

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

Or pass directly:

```python
adapter = GitHubAdapter(token="ghp_xxxxxxxxxxxx")
```

**Required scopes:**
- `repo` - For private repositories
- `public_repo` - For public repositories only

## Use Cases

| Scenario | Tools | Example Query |
|----------|-------|---------------|
| Explore structure | `github_get_repo` + `github_list_files` | "What's the structure of this repo?" |
| Read documentation | `github_read_file` | "Show me the README" |
| Find implementations | `github_search_code` | "Where is the login function defined?" |
| Track changes | `github_get_commits` | "What changed in auth.py recently?" |
| Review PRs | `github_get_pr` | "Summarize PR #123" |
| Code review | All tools | "Review the changes in PR #456" |

## Combining with GitHunter

For deeper code forensics, combine GitHub tools with GitHunter:

```python
from bond.tools import BondToolDeps, github_toolset, githunter_toolset

deps = BondToolDeps(github_token=os.environ["GITHUB_TOKEN"])

agent = BondAgent(
    name="forensic-analyst",
    instructions="You investigate code history and ownership.",
    model="openai:gpt-4o",
    toolsets=[github_toolset, githunter_toolset],
    deps=deps,
)

# Now agent can:
# - Browse any GitHub repo (github_*)
# - Blame lines in local repos (blame_line)
# - Find PR discussions (find_pr_discussion)
# - Identify file experts (get_file_experts)
```

## Rate Limiting

The adapter handles GitHub API rate limits automatically with exponential backoff. If rate limited, tools return an `Error`:

```python
Error(description="GitHub API rate limit exceeded (resets at 1234567890)")
```

Increase limits by using an authenticated token (5000 requests/hour vs 60 unauthenticated).

## Error Handling

All tools return `Error` on failure:

```python
from bond.tools.github import Error

result = await agent.ask("Read nonexistent.txt from facebook/react")
# Agent receives Error(description="File not found: facebook/react/nonexistent.txt")
```

Common errors:
- `RepoNotFoundError` - Repository doesn't exist or is private
- `FileNotFoundError` - Path doesn't exist
- `PRNotFoundError` - PR number doesn't exist
- `RateLimitedError` - API rate limit exceeded
- `AuthenticationError` - Invalid or missing token

## See Also

- [Streaming Server](./streaming-server.md) - Serve agents via SSE/WebSocket
- [GitHunter Toolset](./githunter.md) - Local git forensics
- [API Reference: GitHub](../api/tools.md#github-toolset) - Full type definitions
