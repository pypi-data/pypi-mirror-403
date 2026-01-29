"""GitHunter tools for PydanticAI agents.

This module provides the agent-facing tool functions that use
RunContext to access the GitHunter adapter via dependency injection.
"""

from pathlib import Path

from pydantic_ai import RunContext
from pydantic_ai.tools import Tool

from bond.tools.githunter._exceptions import GitHunterError
from bond.tools.githunter._models import (
    BlameLineRequest,
    Error,
    FindPRDiscussionRequest,
    GetExpertsRequest,
)
from bond.tools.githunter._protocols import GitHunterProtocol
from bond.tools.githunter._types import BlameResult, FileExpert, PRDiscussion


async def blame_line(
    ctx: RunContext[GitHunterProtocol],
    request: BlameLineRequest,
) -> BlameResult | Error:
    """Get blame information for a specific line.

    Agent Usage:
        Call this tool when you need to know who last modified a specific
        line of code, what commit changed it, and when:
        - "Who wrote this line?" → blame_line with the file and line number
        - "When was this changed?" → check commit_date in result
        - "What was the commit message?" → check commit_message in result

    Example:
        ```python
        blame_line({
            "repo_path": "/path/to/repo",
            "file_path": "src/main.py",
            "line_no": 42
        })
        ```

    Returns:
        BlameResult with author, commit hash, date, and message,
        or Error if the operation failed.
    """
    try:
        return await ctx.deps.blame_line(
            repo_path=Path(request.repo_path),
            file_path=request.file_path,
            line_no=request.line_no,
        )
    except GitHunterError as e:
        return Error(description=str(e))


async def find_pr_discussion(
    ctx: RunContext[GitHunterProtocol],
    request: FindPRDiscussionRequest,
) -> PRDiscussion | None | Error:
    """Find the PR discussion for a commit.

    Agent Usage:
        Call this tool when you have a commit hash and want to find
        the pull request discussion that introduced it:
        - "What PR introduced this commit?" → find_pr_discussion
        - "What was discussed when this was merged?" → check PR comments
        - "Why was this change made?" → read PR description and comments

    Example:
        ```python
        find_pr_discussion({
            "repo_path": "/path/to/repo",
            "commit_hash": "abc123def"
        })
        ```

    Returns:
        PRDiscussion with PR number, title, body, and comments,
        None if no PR is associated with the commit,
        or Error if the operation failed.
    """
    try:
        return await ctx.deps.find_pr_discussion(
            repo_path=Path(request.repo_path),
            commit_hash=request.commit_hash,
        )
    except GitHunterError as e:
        return Error(description=str(e))


async def get_file_experts(
    ctx: RunContext[GitHunterProtocol],
    request: GetExpertsRequest,
) -> list[FileExpert] | Error:
    """Get experts for a file based on commit frequency.

    Agent Usage:
        Call this tool when you need to identify who has the most
        knowledge about a file based on their commit history:
        - "Who knows this file best?" → get_file_experts
        - "Who should review changes to this?" → check top experts
        - "Who to ask about this code?" → contact the experts

    Example:
        ```python
        get_file_experts({
            "repo_path": "/path/to/repo",
            "file_path": "src/auth/login.py",
            "window_days": 90,
            "limit": 3
        })
        ```

    Returns:
        List of FileExpert sorted by commit count (descending),
        containing author info, commit count, and last commit date,
        or Error if the operation failed.
    """
    try:
        return await ctx.deps.get_expert_for_file(
            repo_path=Path(request.repo_path),
            file_path=request.file_path,
            window_days=request.window_days,
            limit=request.limit,
        )
    except GitHunterError as e:
        return Error(description=str(e))


# Export as toolset for BondAgent
githunter_toolset: list[Tool[GitHunterProtocol]] = [
    Tool(blame_line),
    Tool(find_pr_discussion),
    Tool(get_file_experts),
]
