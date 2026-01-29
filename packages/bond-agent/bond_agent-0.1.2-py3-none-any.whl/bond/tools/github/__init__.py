"""GitHub toolset for Bond agents.

Provides tools to browse and analyze any GitHub repository.

Example:
    ```python
    from bond import BondAgent
    from bond.tools.github import github_toolset, GitHubAdapter

    # Create adapter with token
    adapter = GitHubAdapter(token=os.environ["GITHUB_TOKEN"])

    # Create agent with GitHub tools
    agent = BondAgent(
        name="code-analyst",
        instructions="You analyze code repositories.",
        model="openai:gpt-4o",
        toolsets=[github_toolset],
        deps=adapter,
    )

    # Use the agent
    response = await agent.ask("What is the structure of the react repo?")
    ```
"""

from bond.tools.github._adapter import GitHubAdapter
from bond.tools.github._exceptions import (
    AuthenticationError,
    FileNotFoundError,
    GitHubAPIError,
    GitHubError,
    PRNotFoundError,
    RateLimitedError,
    RepoNotFoundError,
)
from bond.tools.github._protocols import GitHubProtocol
from bond.tools.github._types import (
    CodeSearchResult,
    Commit,
    CommitAuthor,
    FileContent,
    PullRequest,
    PullRequestUser,
    RepoInfo,
    TreeEntry,
)
from bond.tools.github.tools import github_toolset

__all__ = [
    # Main exports
    "github_toolset",
    "GitHubAdapter",
    "GitHubProtocol",
    # Types
    "RepoInfo",
    "TreeEntry",
    "FileContent",
    "CodeSearchResult",
    "Commit",
    "CommitAuthor",
    "PullRequest",
    "PullRequestUser",
    # Exceptions
    "GitHubError",
    "RepoNotFoundError",
    "FileNotFoundError",
    "PRNotFoundError",
    "RateLimitedError",
    "AuthenticationError",
    "GitHubAPIError",
]
