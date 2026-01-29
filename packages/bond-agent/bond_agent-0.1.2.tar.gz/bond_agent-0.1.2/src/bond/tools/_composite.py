"""Composite dependencies for Bond agents.

Provides a unified dependencies object that satisfies multiple tool protocols,
enabling agents to use multiple toolsets with a single deps injection.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bond.tools.github._adapter import GitHubAdapter
    from bond.tools.github._types import (
        CodeSearchResult,
        Commit,
        FileContent,
        PullRequest,
        RepoInfo,
        TreeEntry,
    )
    from bond.tools.githunter._adapter import GitHunterAdapter
    from bond.tools.githunter._types import BlameResult, FileExpert, PRDiscussion


class BondToolDeps:
    """Composite dependencies satisfying GitHubProtocol and GitHunterProtocol.

    This class delegates to specialized adapters, allowing a single deps object
    to be used with multiple toolsets. Adapters are lazily initialized based
    on which capabilities are configured.

    Example:
        ```python
        from bond import BondAgent
        from bond.tools import BondToolDeps, github_toolset
        from bond.tools.githunter import githunter_toolset

        # Create composite deps with GitHub capabilities
        deps = BondToolDeps(github_token=os.environ["GITHUB_TOKEN"])

        # Create agent with multiple toolsets
        agent = BondAgent(
            name="code-analyst",
            instructions="You analyze code repositories.",
            model="openai:gpt-4o",
            toolsets=[github_toolset, githunter_toolset],
            deps=deps,
        )
        ```

    Note:
        - GitHub tools require `github_token` to be set
        - GitHunter tools work locally without token but need token for PR lookup
        - All adapters are lazily initialized on first use
    """

    def __init__(
        self,
        github_token: str | None = None,
        repo_path: Path | None = None,
    ) -> None:
        """Initialize composite dependencies.

        Args:
            github_token: GitHub personal access token for API access.
                Falls back to GITHUB_TOKEN environment variable.
            repo_path: Default local repository path for GitHunter tools.
                Can be overridden per-call in tool requests.
        """
        self._github_token = github_token
        self._repo_path = repo_path

        # Lazy-initialized adapters
        self._github_adapter: GitHubAdapter | None = None
        self._githunter_adapter: GitHunterAdapter | None = None

    def _get_github_adapter(self) -> GitHubAdapter:
        """Get or create GitHubAdapter."""
        if self._github_adapter is None:
            from bond.tools.github._adapter import GitHubAdapter

            self._github_adapter = GitHubAdapter(token=self._github_token)
        return self._github_adapter

    def _get_githunter_adapter(self) -> GitHunterAdapter:
        """Get or create GitHunterAdapter."""
        if self._githunter_adapter is None:
            from bond.tools.githunter._adapter import GitHunterAdapter

            self._githunter_adapter = GitHunterAdapter()
        return self._githunter_adapter

    # =========================================================================
    # GitHubProtocol implementation
    # =========================================================================

    async def get_repo(self, owner: str, repo: str) -> RepoInfo:
        """Get repository metadata. Delegates to GitHubAdapter."""
        return await self._get_github_adapter().get_repo(owner, repo)

    async def list_tree(
        self,
        owner: str,
        repo: str,
        path: str = "",
        ref: str | None = None,
    ) -> list[TreeEntry]:
        """List directory contents. Delegates to GitHubAdapter."""
        return await self._get_github_adapter().list_tree(owner, repo, path, ref)

    async def get_file(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str | None = None,
    ) -> FileContent:
        """Read file content. Delegates to GitHubAdapter."""
        return await self._get_github_adapter().get_file(owner, repo, path, ref)

    async def search_code(
        self,
        query: str,
        owner: str | None = None,
        repo: str | None = None,
        limit: int = 10,
    ) -> list[CodeSearchResult]:
        """Search code. Delegates to GitHubAdapter."""
        return await self._get_github_adapter().search_code(query, owner, repo, limit)

    async def get_commits(
        self,
        owner: str,
        repo: str,
        path: str | None = None,
        ref: str | None = None,
        limit: int = 10,
    ) -> list[Commit]:
        """Get commit history. Delegates to GitHubAdapter."""
        return await self._get_github_adapter().get_commits(owner, repo, path, ref, limit)

    async def get_pr(
        self,
        owner: str,
        repo: str,
        number: int,
    ) -> PullRequest:
        """Get pull request details. Delegates to GitHubAdapter."""
        return await self._get_github_adapter().get_pr(owner, repo, number)

    # =========================================================================
    # GitHunterProtocol implementation
    # =========================================================================

    async def blame_line(
        self,
        repo_path: Path,
        file_path: str,
        line_no: int,
    ) -> BlameResult:
        """Get blame information for a line. Delegates to GitHunterAdapter."""
        return await self._get_githunter_adapter().blame_line(repo_path, file_path, line_no)

    async def find_pr_discussion(
        self,
        repo_path: Path,
        commit_hash: str,
    ) -> PRDiscussion | None:
        """Find PR discussion for commit. Delegates to GitHunterAdapter."""
        return await self._get_githunter_adapter().find_pr_discussion(repo_path, commit_hash)

    async def get_expert_for_file(
        self,
        repo_path: Path,
        file_path: str,
        window_days: int = 90,
        limit: int = 3,
    ) -> list[FileExpert]:
        """Get file experts. Delegates to GitHunterAdapter."""
        return await self._get_githunter_adapter().get_expert_for_file(
            repo_path, file_path, window_days, limit
        )

    # =========================================================================
    # Lifecycle management
    # =========================================================================

    async def close(self) -> None:
        """Close all adapter connections."""
        if self._github_adapter:
            await self._github_adapter.close()
            self._github_adapter = None
        if self._githunter_adapter:
            await self._githunter_adapter.close()
            self._githunter_adapter = None

    async def __aenter__(self) -> BondToolDeps:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self.close()
