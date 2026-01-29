"""GitHub tools for PydanticAI agents.

This module provides the agent-facing tool functions that use
RunContext to access the GitHub adapter via dependency injection.
"""

from pydantic_ai import RunContext
from pydantic_ai.tools import Tool

from bond.tools.github._exceptions import GitHubError
from bond.tools.github._models import (
    Error,
    GetCommitsRequest,
    GetPRRequest,
    GetRepoRequest,
    ListFilesRequest,
    ReadFileRequest,
    SearchCodeRequest,
)
from bond.tools.github._protocols import GitHubProtocol
from bond.tools.github._types import (
    CodeSearchResult,
    Commit,
    FileContent,
    PullRequest,
    RepoInfo,
    TreeEntry,
)


async def github_get_repo(
    ctx: RunContext[GitHubProtocol],
    request: GetRepoRequest,
) -> RepoInfo | Error:
    """Get repository metadata.

    Agent Usage:
        Call this tool to get basic information about a GitHub repository:
        - "What is this repository about?" → get description, language, topics
        - "How popular is this project?" → check stars and forks
        - "What's the default branch?" → get default_branch for other operations

    Example:
        ```python
        github_get_repo({
            "owner": "facebook",
            "repo": "react"
        })
        ```

    Returns:
        RepoInfo with repository metadata (description, default branch,
        topics, language, stars, forks), or Error if the operation failed.
    """
    try:
        return await ctx.deps.get_repo(
            owner=request.owner,
            repo=request.repo,
        )
    except GitHubError as e:
        return Error(description=str(e))


async def github_list_files(
    ctx: RunContext[GitHubProtocol],
    request: ListFilesRequest,
) -> list[TreeEntry] | Error:
    """List directory contents at path.

    Agent Usage:
        Call this tool to browse the file structure of a repository:
        - "What files are in this repo?" → list_files with empty path
        - "What's in the src folder?" → list_files with path="src"
        - "Show me the test directory" → list_files with path="tests"

    Example:
        ```python
        github_list_files({
            "owner": "facebook",
            "repo": "react",
            "path": "packages/react/src",
            "ref": "main"
        })
        ```

    Returns:
        List of TreeEntry with name, path, type (file/dir), and size,
        or Error if the operation failed.
    """
    try:
        return await ctx.deps.list_tree(
            owner=request.owner,
            repo=request.repo,
            path=request.path,
            ref=request.ref,
        )
    except GitHubError as e:
        return Error(description=str(e))


async def github_read_file(
    ctx: RunContext[GitHubProtocol],
    request: ReadFileRequest,
) -> FileContent | Error:
    """Read file content.

    Agent Usage:
        Call this tool to read the contents of a specific file:
        - "Show me the README" → read_file with path="README.md"
        - "What does this file contain?" → read_file with the path
        - "Read the configuration" → read_file with config file path

    Example:
        ```python
        github_read_file({
            "owner": "facebook",
            "repo": "react",
            "path": "packages/react/package.json",
            "ref": "main"
        })
        ```

    Returns:
        FileContent with decoded content, size, and SHA,
        or Error if the operation failed (file not found, binary file, etc).
    """
    try:
        return await ctx.deps.get_file(
            owner=request.owner,
            repo=request.repo,
            path=request.path,
            ref=request.ref,
        )
    except GitHubError as e:
        return Error(description=str(e))


async def github_search_code(
    ctx: RunContext[GitHubProtocol],
    request: SearchCodeRequest,
) -> list[CodeSearchResult] | Error:
    """Search code within repository.

    Agent Usage:
        Call this tool to find code containing specific terms:
        - "Find where X is defined" → search for "class X" or "function X"
        - "Where is Y used?" → search for "Y("
        - "Find all TODO comments" → search for "TODO"

    Example:
        ```python
        github_search_code({
            "query": "useState",
            "owner": "facebook",
            "repo": "react",
            "limit": 10
        })
        ```

    Returns:
        List of CodeSearchResult with file paths and matching text fragments,
        or Error if the operation failed (rate limited, invalid query, etc).
    """
    try:
        return await ctx.deps.search_code(
            query=request.query,
            owner=request.owner,
            repo=request.repo,
            limit=request.limit,
        )
    except GitHubError as e:
        return Error(description=str(e))


async def github_get_commits(
    ctx: RunContext[GitHubProtocol],
    request: GetCommitsRequest,
) -> list[Commit] | Error:
    """Get recent commits for file or repository.

    Agent Usage:
        Call this tool to see the history of changes:
        - "What changed recently?" → get_commits for the repo
        - "Who modified this file?" → get_commits with the file path
        - "Show me recent changes" → get_commits with limit

    Example:
        ```python
        github_get_commits({
            "owner": "facebook",
            "repo": "react",
            "path": "packages/react/src/React.js",
            "limit": 5
        })
        ```

    Returns:
        List of Commit with SHA, message, author info, and date,
        or Error if the operation failed.
    """
    try:
        return await ctx.deps.get_commits(
            owner=request.owner,
            repo=request.repo,
            path=request.path,
            ref=request.ref,
            limit=request.limit,
        )
    except GitHubError as e:
        return Error(description=str(e))


async def github_get_pr(
    ctx: RunContext[GitHubProtocol],
    request: GetPRRequest,
) -> PullRequest | Error:
    """Get pull request details by number.

    Agent Usage:
        Call this tool to get information about a specific PR:
        - "What does PR #123 do?" → get PR title and description
        - "Who created this PR?" → get PR author
        - "Is this PR merged?" → check state and merged_at

    Example:
        ```python
        github_get_pr({
            "owner": "facebook",
            "repo": "react",
            "number": 25000
        })
        ```

    Returns:
        PullRequest with title, body, author, state, and merge info,
        or Error if the operation failed.
    """
    try:
        return await ctx.deps.get_pr(
            owner=request.owner,
            repo=request.repo,
            number=request.number,
        )
    except GitHubError as e:
        return Error(description=str(e))


# Export as toolset for BondAgent
github_toolset: list[Tool[GitHubProtocol]] = [
    Tool(github_get_repo),
    Tool(github_list_files),
    Tool(github_read_file),
    Tool(github_search_code),
    Tool(github_get_commits),
    Tool(github_get_pr),
]
