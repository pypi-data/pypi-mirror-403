"""Tests for GitHub tool functions."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from bond.tools.github._exceptions import (
    FileNotFoundError,
    PRNotFoundError,
    RateLimitedError,
    RepoNotFoundError,
)
from bond.tools.github._models import (
    Error,
    GetCommitsRequest,
    GetPRRequest,
    GetRepoRequest,
    ListFilesRequest,
    ReadFileRequest,
    SearchCodeRequest,
)
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
from bond.tools.github.tools import (
    github_get_commits,
    github_get_pr,
    github_get_repo,
    github_list_files,
    github_read_file,
    github_search_code,
)


class MockGitHub:
    """Mock implementation of GitHubProtocol for testing."""

    def __init__(
        self,
        repo_info: RepoInfo | Exception | None = None,
        tree_entries: list[TreeEntry] | Exception | None = None,
        file_content: FileContent | Exception | None = None,
        search_results: list[CodeSearchResult] | Exception | None = None,
        commits: list[Commit] | Exception | None = None,
        pull_request: PullRequest | Exception | None = None,
    ) -> None:
        """Initialize mock with configurable return values."""
        self._repo_info = repo_info
        self._tree_entries = tree_entries if tree_entries is not None else []
        self._file_content = file_content
        self._search_results = search_results if search_results is not None else []
        self._commits = commits if commits is not None else []
        self._pull_request = pull_request

    async def get_repo(self, owner: str, repo: str) -> RepoInfo:
        if isinstance(self._repo_info, Exception):
            raise self._repo_info
        if self._repo_info is None:
            raise ValueError("No repo info configured")
        return self._repo_info

    async def list_tree(
        self, owner: str, repo: str, path: str = "", ref: str | None = None
    ) -> list[TreeEntry]:
        if isinstance(self._tree_entries, Exception):
            raise self._tree_entries
        return self._tree_entries

    async def get_file(
        self, owner: str, repo: str, path: str, ref: str | None = None
    ) -> FileContent:
        if isinstance(self._file_content, Exception):
            raise self._file_content
        if self._file_content is None:
            raise ValueError("No file content configured")
        return self._file_content

    async def search_code(
        self, query: str, owner: str | None = None, repo: str | None = None, limit: int = 10
    ) -> list[CodeSearchResult]:
        if isinstance(self._search_results, Exception):
            raise self._search_results
        return self._search_results

    async def get_commits(
        self,
        owner: str,
        repo: str,
        path: str | None = None,
        ref: str | None = None,
        limit: int = 10,
    ) -> list[Commit]:
        if isinstance(self._commits, Exception):
            raise self._commits
        return self._commits

    async def get_pr(self, owner: str, repo: str, number: int) -> PullRequest:
        if isinstance(self._pull_request, Exception):
            raise self._pull_request
        if self._pull_request is None:
            raise ValueError("No PR configured")
        return self._pull_request


@pytest.fixture
def sample_repo_info() -> RepoInfo:
    """Create a sample repository info for tests."""
    return RepoInfo(
        owner="facebook",
        name="react",
        full_name="facebook/react",
        description="A declarative UI library",
        default_branch="main",
        topics=("javascript", "ui", "frontend"),
        language="JavaScript",
        stars=200000,
        forks=40000,
        is_private=False,
        created_at=datetime(2013, 5, 24, tzinfo=UTC),
        updated_at=datetime(2024, 6, 15, tzinfo=UTC),
    )


@pytest.fixture
def sample_tree_entries() -> list[TreeEntry]:
    """Create sample tree entries for tests."""
    return [
        TreeEntry(path="README.md", name="README.md", type="file", size=1234, sha="abc123"),
        TreeEntry(path="src", name="src", type="dir", size=None, sha="def456"),
        TreeEntry(path="package.json", name="package.json", type="file", size=500, sha="ghi789"),
    ]


@pytest.fixture
def sample_file_content() -> FileContent:
    """Create sample file content for tests."""
    return FileContent(
        path="README.md",
        content="# React\n\nA JavaScript library for building user interfaces.",
        encoding="base64",
        size=60,
        sha="abc123",
    )


@pytest.fixture
def sample_commits() -> list[Commit]:
    """Create sample commits for tests."""
    author = CommitAuthor(
        name="Developer",
        email="dev@example.com",
        date=datetime(2024, 6, 15, 10, 30, tzinfo=UTC),
    )
    return [
        Commit(
            sha="abc123def456",
            message="Fix bug in component",
            author=author,
            committer=author,
            html_url="https://github.com/facebook/react/commit/abc123def456",
        ),
    ]


@pytest.fixture
def sample_pr() -> PullRequest:
    """Create sample pull request for tests."""
    return PullRequest(
        number=12345,
        title="Fix rendering issue",
        body="This PR fixes the rendering issue.",
        state="merged",
        user=PullRequestUser(login="developer", html_url="https://github.com/developer"),
        html_url="https://github.com/facebook/react/pull/12345",
        created_at=datetime(2024, 6, 10, tzinfo=UTC),
        updated_at=datetime(2024, 6, 15, tzinfo=UTC),
        merged_at=datetime(2024, 6, 15, tzinfo=UTC),
        base_branch="main",
        head_branch="fix-rendering",
    )


def create_mock_ctx(github: MockGitHub) -> MagicMock:
    """Create a mock RunContext with GitHub deps."""
    ctx = MagicMock()
    ctx.deps = github
    return ctx


class TestGitHubGetRepo:
    """Tests for github_get_repo tool function."""

    @pytest.mark.asyncio
    async def test_returns_repo_info(self, sample_repo_info: RepoInfo) -> None:
        """Test github_get_repo returns RepoInfo on success."""
        github = MockGitHub(repo_info=sample_repo_info)
        ctx = create_mock_ctx(github)
        request = GetRepoRequest(owner="facebook", repo="react")

        result = await github_get_repo(ctx, request)

        assert isinstance(result, RepoInfo)
        assert result.full_name == "facebook/react"
        assert result.stars == 200000

    @pytest.mark.asyncio
    async def test_handles_repo_not_found(self) -> None:
        """Test github_get_repo returns Error when repo not found."""
        github = MockGitHub(repo_info=RepoNotFoundError("facebook", "nonexistent"))
        ctx = create_mock_ctx(github)
        request = GetRepoRequest(owner="facebook", repo="nonexistent")

        result = await github_get_repo(ctx, request)

        assert isinstance(result, Error)
        assert "not found" in result.description.lower()


class TestGitHubListFiles:
    """Tests for github_list_files tool function."""

    @pytest.mark.asyncio
    async def test_returns_tree_entries(self, sample_tree_entries: list[TreeEntry]) -> None:
        """Test github_list_files returns list of TreeEntry."""
        github = MockGitHub(tree_entries=sample_tree_entries)
        ctx = create_mock_ctx(github)
        request = ListFilesRequest(owner="facebook", repo="react", path="")

        result = await github_list_files(ctx, request)

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0].name == "README.md"
        assert result[1].type == "dir"

    @pytest.mark.asyncio
    async def test_handles_path_not_found(self) -> None:
        """Test github_list_files returns Error when path not found."""
        github = MockGitHub(tree_entries=FileNotFoundError("facebook", "react", "nonexistent"))
        ctx = create_mock_ctx(github)
        request = ListFilesRequest(owner="facebook", repo="react", path="nonexistent")

        result = await github_list_files(ctx, request)

        assert isinstance(result, Error)
        assert "not found" in result.description.lower()


class TestGitHubReadFile:
    """Tests for github_read_file tool function."""

    @pytest.mark.asyncio
    async def test_returns_file_content(self, sample_file_content: FileContent) -> None:
        """Test github_read_file returns FileContent on success."""
        github = MockGitHub(file_content=sample_file_content)
        ctx = create_mock_ctx(github)
        request = ReadFileRequest(owner="facebook", repo="react", path="README.md")

        result = await github_read_file(ctx, request)

        assert isinstance(result, FileContent)
        assert "# React" in result.content
        assert result.path == "README.md"

    @pytest.mark.asyncio
    async def test_handles_file_not_found(self) -> None:
        """Test github_read_file returns Error when file not found."""
        github = MockGitHub(file_content=FileNotFoundError("facebook", "react", "missing.txt"))
        ctx = create_mock_ctx(github)
        request = ReadFileRequest(owner="facebook", repo="react", path="missing.txt")

        result = await github_read_file(ctx, request)

        assert isinstance(result, Error)
        assert "not found" in result.description.lower()


class TestGitHubSearchCode:
    """Tests for github_search_code tool function."""

    @pytest.mark.asyncio
    async def test_returns_search_results(self) -> None:
        """Test github_search_code returns list of CodeSearchResult."""
        results = [
            CodeSearchResult(
                path="src/React.js",
                repository="facebook/react",
                html_url="https://github.com/facebook/react/blob/main/src/React.js",
                text_matches=("export default React;",),
            ),
        ]
        github = MockGitHub(search_results=results)
        ctx = create_mock_ctx(github)
        request = SearchCodeRequest(query="export default React", owner="facebook", repo="react")

        result = await github_search_code(ctx, request)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].path == "src/React.js"

    @pytest.mark.asyncio
    async def test_handles_rate_limit(self) -> None:
        """Test github_search_code returns Error when rate limited."""
        github = MockGitHub(search_results=RateLimitedError())
        ctx = create_mock_ctx(github)
        request = SearchCodeRequest(query="test")

        result = await github_search_code(ctx, request)

        assert isinstance(result, Error)
        assert "rate limit" in result.description.lower()


class TestGitHubGetCommits:
    """Tests for github_get_commits tool function."""

    @pytest.mark.asyncio
    async def test_returns_commits(self, sample_commits: list[Commit]) -> None:
        """Test github_get_commits returns list of Commit."""
        github = MockGitHub(commits=sample_commits)
        ctx = create_mock_ctx(github)
        request = GetCommitsRequest(owner="facebook", repo="react", limit=10)

        result = await github_get_commits(ctx, request)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].sha == "abc123def456"
        assert result[0].author.email == "dev@example.com"

    @pytest.mark.asyncio
    async def test_handles_repo_not_found(self) -> None:
        """Test github_get_commits returns Error when repo not found."""
        github = MockGitHub(commits=RepoNotFoundError("owner", "missing"))
        ctx = create_mock_ctx(github)
        request = GetCommitsRequest(owner="owner", repo="missing")

        result = await github_get_commits(ctx, request)

        assert isinstance(result, Error)
        assert "not found" in result.description.lower()


class TestGitHubGetPR:
    """Tests for github_get_pr tool function."""

    @pytest.mark.asyncio
    async def test_returns_pull_request(self, sample_pr: PullRequest) -> None:
        """Test github_get_pr returns PullRequest on success."""
        github = MockGitHub(pull_request=sample_pr)
        ctx = create_mock_ctx(github)
        request = GetPRRequest(owner="facebook", repo="react", number=12345)

        result = await github_get_pr(ctx, request)

        assert isinstance(result, PullRequest)
        assert result.number == 12345
        assert result.state == "merged"
        assert result.merged_at is not None

    @pytest.mark.asyncio
    async def test_handles_pr_not_found(self) -> None:
        """Test github_get_pr returns Error when PR not found."""
        github = MockGitHub(pull_request=PRNotFoundError("facebook", "react", 99999))
        ctx = create_mock_ctx(github)
        request = GetPRRequest(owner="facebook", repo="react", number=99999)

        result = await github_get_pr(ctx, request)

        assert isinstance(result, Error)
        assert "not found" in result.description.lower()
