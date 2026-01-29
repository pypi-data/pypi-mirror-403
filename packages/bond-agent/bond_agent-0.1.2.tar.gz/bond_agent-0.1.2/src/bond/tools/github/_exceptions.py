"""GitHub-specific exceptions.

Custom exception hierarchy for GitHub operations.
"""


class GitHubError(Exception):
    """Base exception for GitHub operations."""

    pass


class RepoNotFoundError(GitHubError):
    """Repository not found."""

    def __init__(self, owner: str, repo: str) -> None:
        """Initialize error.

        Args:
            owner: Repository owner.
            repo: Repository name.
        """
        self.owner = owner
        self.repo = repo
        super().__init__(f"Repository not found: {owner}/{repo}")


class FileNotFoundError(GitHubError):
    """File not found in repository."""

    def __init__(self, owner: str, repo: str, path: str) -> None:
        """Initialize error.

        Args:
            owner: Repository owner.
            repo: Repository name.
            path: File path that was not found.
        """
        self.owner = owner
        self.repo = repo
        self.path = path
        super().__init__(f"File not found: {owner}/{repo}/{path}")


class PRNotFoundError(GitHubError):
    """Pull request not found."""

    def __init__(self, owner: str, repo: str, number: int) -> None:
        """Initialize error.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: PR number.
        """
        self.owner = owner
        self.repo = repo
        self.number = number
        super().__init__(f"PR not found: {owner}/{repo}#{number}")


class RateLimitedError(GitHubError):
    """GitHub API rate limit exceeded."""

    def __init__(self, reset_at: int | None = None) -> None:
        """Initialize error.

        Args:
            reset_at: Unix timestamp when rate limit resets.
        """
        self.reset_at = reset_at
        msg = "GitHub API rate limit exceeded"
        if reset_at:
            msg += f" (resets at {reset_at})"
        super().__init__(msg)


class AuthenticationError(GitHubError):
    """GitHub authentication failed."""

    def __init__(self) -> None:
        """Initialize error."""
        super().__init__("GitHub authentication failed. Check GITHUB_TOKEN.")


class GitHubAPIError(GitHubError):
    """Generic GitHub API error."""

    def __init__(self, status_code: int, message: str) -> None:
        """Initialize error.

        Args:
            status_code: HTTP status code.
            message: Error message from API.
        """
        self.status_code = status_code
        self.message = message
        super().__init__(f"GitHub API error ({status_code}): {message}")
