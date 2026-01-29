"""Protocol definition for GitHub tools.

Defines the interface that GitHubAdapter must implement.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ._types import (
    CodeSearchResult,
    Commit,
    FileContent,
    PullRequest,
    RepoInfo,
    TreeEntry,
)


@runtime_checkable
class GitHubProtocol(Protocol):
    """Protocol for GitHub API access.

    Provides methods to:
    - Get repository metadata
    - Browse repository file tree
    - Read file contents
    - Search code
    - Get commit history
    - Get pull request details
    """

    async def get_repo(
        self,
        owner: str,
        repo: str,
    ) -> RepoInfo:
        """Get repository metadata.

        Args:
            owner: Repository owner (user or organization).
            repo: Repository name.

        Returns:
            RepoInfo with repository metadata.

        Raises:
            GitHubError: If repository not found or API error.
        """
        ...

    async def list_tree(
        self,
        owner: str,
        repo: str,
        path: str = "",
        ref: str | None = None,
    ) -> list[TreeEntry]:
        """List directory contents at path.

        Args:
            owner: Repository owner.
            repo: Repository name.
            path: Path relative to repo root (empty string for root).
            ref: Git ref (branch, tag, commit). Uses default branch if None.

        Returns:
            List of TreeEntry for files and directories at path.

        Raises:
            GitHubError: If path not found or API error.
        """
        ...

    async def get_file(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str | None = None,
    ) -> FileContent:
        """Read file content.

        Args:
            owner: Repository owner.
            repo: Repository name.
            path: Path to file relative to repo root.
            ref: Git ref (branch, tag, commit). Uses default branch if None.

        Returns:
            FileContent with decoded file content.

        Raises:
            GitHubError: If file not found or API error.
        """
        ...

    async def search_code(
        self,
        query: str,
        owner: str | None = None,
        repo: str | None = None,
        limit: int = 10,
    ) -> list[CodeSearchResult]:
        """Search code within repository or across GitHub.

        Args:
            query: Search query string.
            owner: Optional owner to scope search.
            repo: Optional repo name to scope search (requires owner).
            limit: Maximum results to return.

        Returns:
            List of CodeSearchResult with matching files.

        Raises:
            GitHubError: If search fails or rate limited.
        """
        ...

    async def get_commits(
        self,
        owner: str,
        repo: str,
        path: str | None = None,
        ref: str | None = None,
        limit: int = 10,
    ) -> list[Commit]:
        """Get recent commits for file or repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            path: Optional path to filter commits by file.
            ref: Git ref to start from. Uses default branch if None.
            limit: Maximum commits to return.

        Returns:
            List of Commit sorted by date descending.

        Raises:
            GitHubError: If repository not found or API error.
        """
        ...

    async def get_pr(
        self,
        owner: str,
        repo: str,
        number: int,
    ) -> PullRequest:
        """Get pull request details by number.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request number.

        Returns:
            PullRequest with PR details.

        Raises:
            GitHubError: If PR not found or API error.
        """
        ...
