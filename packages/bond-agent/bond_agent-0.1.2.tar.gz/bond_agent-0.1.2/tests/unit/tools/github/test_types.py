"""Tests for GitHub types."""

from datetime import UTC, datetime

import pytest

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


class TestRepoInfo:
    """Tests for RepoInfo dataclass."""

    def test_creation(self) -> None:
        """Test RepoInfo creation with all fields."""
        info = RepoInfo(
            owner="facebook",
            name="react",
            full_name="facebook/react",
            description="A UI library",
            default_branch="main",
            topics=("javascript", "ui"),
            language="JavaScript",
            stars=200000,
            forks=40000,
            is_private=False,
            created_at=datetime(2013, 5, 24, tzinfo=UTC),
            updated_at=datetime(2024, 6, 15, tzinfo=UTC),
        )

        assert info.owner == "facebook"
        assert info.name == "react"
        assert info.full_name == "facebook/react"
        assert info.topics == ("javascript", "ui")

    def test_frozen(self) -> None:
        """Test RepoInfo is immutable."""
        info = RepoInfo(
            owner="a",
            name="b",
            full_name="a/b",
            description=None,
            default_branch="main",
            topics=(),
            language=None,
            stars=0,
            forks=0,
            is_private=False,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

        with pytest.raises(AttributeError):
            info.stars = 100  # type: ignore[misc]


class TestTreeEntry:
    """Tests for TreeEntry dataclass."""

    def test_file_entry(self) -> None:
        """Test file tree entry."""
        entry = TreeEntry(
            path="src/index.js",
            name="index.js",
            type="file",
            size=1234,
            sha="abc123",
        )

        assert entry.type == "file"
        assert entry.size == 1234

    def test_dir_entry(self) -> None:
        """Test directory tree entry."""
        entry = TreeEntry(
            path="src",
            name="src",
            type="dir",
            size=None,
            sha="def456",
        )

        assert entry.type == "dir"
        assert entry.size is None


class TestFileContent:
    """Tests for FileContent dataclass."""

    def test_creation(self) -> None:
        """Test FileContent creation."""
        content = FileContent(
            path="README.md",
            content="# Hello World",
            encoding="base64",
            size=13,
            sha="abc123",
        )

        assert content.path == "README.md"
        assert content.content == "# Hello World"


class TestCodeSearchResult:
    """Tests for CodeSearchResult dataclass."""

    def test_creation(self) -> None:
        """Test CodeSearchResult creation."""
        result = CodeSearchResult(
            path="src/main.js",
            repository="owner/repo",
            html_url="https://github.com/owner/repo/blob/main/src/main.js",
            text_matches=("const x = 1;", "function test() {}"),
        )

        assert result.repository == "owner/repo"
        assert len(result.text_matches) == 2


class TestCommit:
    """Tests for Commit dataclass."""

    def test_creation(self) -> None:
        """Test Commit creation."""
        author = CommitAuthor(
            name="Developer",
            email="dev@example.com",
            date=datetime(2024, 6, 15, tzinfo=UTC),
        )
        commit = Commit(
            sha="abc123def456",
            message="Fix bug",
            author=author,
            committer=author,
            html_url="https://github.com/owner/repo/commit/abc123",
        )

        assert commit.sha == "abc123def456"
        assert commit.author.name == "Developer"


class TestPullRequest:
    """Tests for PullRequest dataclass."""

    def test_creation(self) -> None:
        """Test PullRequest creation."""
        user = PullRequestUser(
            login="developer",
            html_url="https://github.com/developer",
        )
        pr = PullRequest(
            number=123,
            title="Add feature",
            body="This adds a new feature.",
            state="open",
            user=user,
            html_url="https://github.com/owner/repo/pull/123",
            created_at=datetime(2024, 6, 10, tzinfo=UTC),
            updated_at=datetime(2024, 6, 15, tzinfo=UTC),
            merged_at=None,
            base_branch="main",
            head_branch="feature",
        )

        assert pr.number == 123
        assert pr.state == "open"
        assert pr.merged_at is None

    def test_merged_pr(self) -> None:
        """Test merged PullRequest."""
        user = PullRequestUser(login="dev", html_url="https://github.com/dev")
        pr = PullRequest(
            number=456,
            title="Fix",
            body=None,
            state="closed",
            user=user,
            html_url="https://github.com/o/r/pull/456",
            created_at=datetime(2024, 6, 10, tzinfo=UTC),
            updated_at=datetime(2024, 6, 15, tzinfo=UTC),
            merged_at=datetime(2024, 6, 14, tzinfo=UTC),
            base_branch="main",
            head_branch="fix",
        )

        assert pr.state == "closed"
        assert pr.merged_at is not None
