"""GitHub domain types.

Frozen dataclass types for GitHub API responses.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RepoInfo:
    """Repository metadata.

    Attributes:
        owner: Repository owner (user or organization).
        name: Repository name.
        full_name: Full name in owner/repo format.
        description: Repository description.
        default_branch: Default branch name (e.g., "main").
        topics: List of repository topics.
        language: Primary programming language.
        stars: Star count.
        forks: Fork count.
        is_private: Whether the repository is private.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    owner: str
    name: str
    full_name: str
    description: str | None
    default_branch: str
    topics: tuple[str, ...]
    language: str | None
    stars: int
    forks: int
    is_private: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TreeEntry:
    """Entry in a repository file tree.

    Attributes:
        path: Path relative to repository root.
        name: File or directory name.
        type: Either "file" or "dir".
        size: File size in bytes (None for directories).
        sha: Git SHA hash.
    """

    path: str
    name: str
    type: str  # "file" or "dir"
    size: int | None
    sha: str


@dataclass(frozen=True)
class FileContent:
    """File content from a repository.

    Attributes:
        path: Path relative to repository root.
        content: Decoded file content.
        encoding: Original encoding (usually "base64").
        size: File size in bytes.
        sha: Git SHA hash.
    """

    path: str
    content: str
    encoding: str
    size: int
    sha: str


@dataclass(frozen=True)
class CodeSearchResult:
    """Result from code search.

    Attributes:
        path: File path where match was found.
        repository: Repository full name (owner/repo).
        html_url: URL to view file on GitHub.
        text_matches: List of matching text fragments.
    """

    path: str
    repository: str
    html_url: str
    text_matches: tuple[str, ...]


@dataclass(frozen=True)
class CommitAuthor:
    """Commit author information.

    Attributes:
        name: Author's name.
        email: Author's email.
        date: Commit date.
    """

    name: str
    email: str
    date: datetime


@dataclass(frozen=True)
class Commit:
    """Git commit information.

    Attributes:
        sha: Full commit SHA.
        message: Commit message.
        author: Author information.
        committer: Committer information.
        html_url: URL to view commit on GitHub.
    """

    sha: str
    message: str
    author: CommitAuthor
    committer: CommitAuthor
    html_url: str


@dataclass(frozen=True)
class PullRequestUser:
    """GitHub user in PR context.

    Attributes:
        login: GitHub username.
        html_url: Profile URL.
    """

    login: str
    html_url: str


@dataclass(frozen=True)
class PullRequest:
    """Pull request information.

    Attributes:
        number: PR number.
        title: PR title.
        body: PR description/body.
        state: PR state (open, closed, merged).
        user: PR author.
        html_url: URL to view PR on GitHub.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        merged_at: Merge timestamp (None if not merged).
        base_branch: Target branch name.
        head_branch: Source branch name.
    """

    number: int
    title: str
    body: str | None
    state: str
    user: PullRequestUser
    html_url: str
    created_at: datetime
    updated_at: datetime
    merged_at: datetime | None
    base_branch: str
    head_branch: str
