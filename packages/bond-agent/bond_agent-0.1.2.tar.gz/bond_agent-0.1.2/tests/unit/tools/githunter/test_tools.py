"""Tests for GitHunter tool functions."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from bond.tools.githunter._exceptions import (
    FileNotFoundInRepoError,
    LineOutOfRangeError,
    RateLimitedError,
    RepoNotFoundError,
)
from bond.tools.githunter._models import (
    BlameLineRequest,
    Error,
    FindPRDiscussionRequest,
    GetExpertsRequest,
)
from bond.tools.githunter._types import (
    AuthorProfile,
    BlameResult,
    FileExpert,
    PRDiscussion,
)
from bond.tools.githunter.tools import (
    blame_line,
    find_pr_discussion,
    get_file_experts,
)


class MockGitHunter:
    """Mock implementation of GitHunterProtocol for testing."""

    def __init__(
        self,
        blame_result: BlameResult | Exception | None = None,
        pr_discussion: PRDiscussion | Exception | None = None,
        experts: list[FileExpert] | Exception | None = None,
    ) -> None:
        """Initialize mock with configurable return values."""
        self._blame_result = blame_result
        self._pr_discussion = pr_discussion
        self._experts = experts if experts is not None else []

    async def blame_line(
        self,
        repo_path: Path,
        file_path: str,
        line_no: int,
    ) -> BlameResult:
        """Mock blame_line that returns configured result or raises exception."""
        if isinstance(self._blame_result, Exception):
            raise self._blame_result
        if self._blame_result is None:
            raise ValueError("No blame result configured")
        return self._blame_result

    async def find_pr_discussion(
        self,
        repo_path: Path,
        commit_hash: str,
    ) -> PRDiscussion | None:
        """Mock find_pr_discussion that returns configured result or raises exception."""
        if isinstance(self._pr_discussion, Exception):
            raise self._pr_discussion
        return self._pr_discussion

    async def get_expert_for_file(
        self,
        repo_path: Path,
        file_path: str,
        window_days: int = 90,
        limit: int = 3,
    ) -> list[FileExpert]:
        """Mock get_expert_for_file that returns configured result or raises exception."""
        if isinstance(self._experts, Exception):
            raise self._experts
        return self._experts


@pytest.fixture
def sample_author() -> AuthorProfile:
    """Create a sample author profile for tests."""
    return AuthorProfile(
        git_email="dev@example.com",
        git_name="Developer",
        github_username="devuser",
    )


@pytest.fixture
def sample_blame_result(sample_author: AuthorProfile) -> BlameResult:
    """Create a sample blame result for tests."""
    return BlameResult(
        line_no=42,
        content="    return result",
        author=sample_author,
        commit_hash="abc123def456",
        commit_date=datetime(2024, 6, 15, 10, 30, tzinfo=UTC),
        commit_message="Fix calculation bug",
    )


@pytest.fixture
def sample_pr_discussion() -> PRDiscussion:
    """Create a sample PR discussion for tests."""
    return PRDiscussion(
        pr_number=123,
        title="Fix calculation bug in processor",
        body="This PR fixes the calculation issue reported in #100.",
        url="https://github.com/owner/repo/pull/123",
        issue_comments=("LGTM!", "Thanks for the fix."),
    )


@pytest.fixture
def sample_experts(sample_author: AuthorProfile) -> list[FileExpert]:
    """Create sample file experts for tests."""
    return [
        FileExpert(
            author=sample_author,
            commit_count=15,
            last_commit_date=datetime(2024, 6, 20, tzinfo=UTC),
        ),
        FileExpert(
            author=AuthorProfile(
                git_email="other@example.com",
                git_name="Other Dev",
            ),
            commit_count=8,
            last_commit_date=datetime(2024, 5, 10, tzinfo=UTC),
        ),
    ]


def create_mock_ctx(hunter: MockGitHunter) -> MagicMock:
    """Create a mock RunContext with GitHunter deps."""
    ctx = MagicMock()
    ctx.deps = hunter
    return ctx


class TestBlameLine:
    """Tests for blame_line tool function."""

    @pytest.mark.asyncio
    async def test_returns_blame_result(self, sample_blame_result: BlameResult) -> None:
        """Test blame_line returns BlameResult on success."""
        hunter = MockGitHunter(blame_result=sample_blame_result)
        ctx = create_mock_ctx(hunter)
        request = BlameLineRequest(
            repo_path="/path/to/repo",
            file_path="src/processor.py",
            line_no=42,
        )

        result = await blame_line(ctx, request)

        assert isinstance(result, BlameResult)
        assert result.line_no == 42
        assert result.commit_hash == "abc123def456"
        assert result.author.git_email == "dev@example.com"

    @pytest.mark.asyncio
    async def test_handles_file_not_found_error(self) -> None:
        """Test blame_line returns Error when file not found."""
        hunter = MockGitHunter(
            blame_result=FileNotFoundInRepoError(
                file_path="nonexistent.py",
                repo_path="/repo",
            )
        )
        ctx = create_mock_ctx(hunter)
        request = BlameLineRequest(
            repo_path="/repo",
            file_path="nonexistent.py",
            line_no=1,
        )

        result = await blame_line(ctx, request)

        assert isinstance(result, Error)
        assert "File not found" in result.description
        assert "nonexistent.py" in result.description

    @pytest.mark.asyncio
    async def test_handles_line_out_of_range_error(self) -> None:
        """Test blame_line returns Error when line out of range."""
        hunter = MockGitHunter(blame_result=LineOutOfRangeError(line_no=1000, max_lines=50))
        ctx = create_mock_ctx(hunter)
        request = BlameLineRequest(
            repo_path="/repo",
            file_path="small.py",
            line_no=1000,
        )

        result = await blame_line(ctx, request)

        assert isinstance(result, Error)
        assert "out of range" in result.description

    @pytest.mark.asyncio
    async def test_handles_repo_not_found_error(self) -> None:
        """Test blame_line returns Error when repo not found."""
        hunter = MockGitHunter(blame_result=RepoNotFoundError(path="/not/a/repo"))
        ctx = create_mock_ctx(hunter)
        request = BlameLineRequest(
            repo_path="/not/a/repo",
            file_path="file.py",
            line_no=1,
        )

        result = await blame_line(ctx, request)

        assert isinstance(result, Error)
        assert "not inside a git repository" in result.description


class TestFindPRDiscussion:
    """Tests for find_pr_discussion tool function."""

    @pytest.mark.asyncio
    async def test_returns_pr_discussion(self, sample_pr_discussion: PRDiscussion) -> None:
        """Test find_pr_discussion returns PRDiscussion when found."""
        hunter = MockGitHunter(pr_discussion=sample_pr_discussion)
        ctx = create_mock_ctx(hunter)
        request = FindPRDiscussionRequest(
            repo_path="/path/to/repo",
            commit_hash="abc123def",
        )

        result = await find_pr_discussion(ctx, request)

        assert isinstance(result, PRDiscussion)
        assert result.pr_number == 123
        assert result.title == "Fix calculation bug in processor"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_pr(self) -> None:
        """Test find_pr_discussion returns None when no PR found."""
        hunter = MockGitHunter(pr_discussion=None)
        ctx = create_mock_ctx(hunter)
        request = FindPRDiscussionRequest(
            repo_path="/path/to/repo",
            commit_hash="xyz789abc",
        )

        result = await find_pr_discussion(ctx, request)

        assert result is None

    @pytest.mark.asyncio
    async def test_handles_rate_limited_error(self) -> None:
        """Test find_pr_discussion returns Error when rate limited."""
        reset_at = datetime(2024, 6, 15, 12, 0, tzinfo=UTC)
        hunter = MockGitHunter(
            pr_discussion=RateLimitedError(
                retry_after_seconds=3600,
                reset_at=reset_at,
            )
        )
        ctx = create_mock_ctx(hunter)
        request = FindPRDiscussionRequest(
            repo_path="/repo",
            commit_hash="abc123def",
        )

        result = await find_pr_discussion(ctx, request)

        assert isinstance(result, Error)
        assert "rate limit" in result.description.lower()

    @pytest.mark.asyncio
    async def test_handles_repo_not_found_error(self) -> None:
        """Test find_pr_discussion returns Error when repo not found."""
        hunter = MockGitHunter(pr_discussion=RepoNotFoundError(path="/not/a/repo"))
        ctx = create_mock_ctx(hunter)
        request = FindPRDiscussionRequest(
            repo_path="/not/a/repo",
            commit_hash="abc123def",
        )

        result = await find_pr_discussion(ctx, request)

        assert isinstance(result, Error)
        assert "not inside a git repository" in result.description


class TestGetFileExperts:
    """Tests for get_file_experts tool function."""

    @pytest.mark.asyncio
    async def test_returns_expert_list(self, sample_experts: list[FileExpert]) -> None:
        """Test get_file_experts returns list of FileExpert on success."""
        hunter = MockGitHunter(experts=sample_experts)
        ctx = create_mock_ctx(hunter)
        request = GetExpertsRequest(
            repo_path="/path/to/repo",
            file_path="src/auth/login.py",
            window_days=90,
            limit=3,
        )

        result = await get_file_experts(ctx, request)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].commit_count == 15
        assert result[0].author.git_email == "dev@example.com"

    @pytest.mark.asyncio
    async def test_returns_empty_list(self) -> None:
        """Test get_file_experts returns empty list when no experts."""
        hunter = MockGitHunter(experts=[])
        ctx = create_mock_ctx(hunter)
        request = GetExpertsRequest(
            repo_path="/path/to/repo",
            file_path="new_file.py",
            window_days=90,
            limit=3,
        )

        result = await get_file_experts(ctx, request)

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_handles_repo_not_found_error(self) -> None:
        """Test get_file_experts returns Error when repo not found."""
        hunter = MockGitHunter(experts=RepoNotFoundError(path="/not/a/repo"))
        ctx = create_mock_ctx(hunter)
        request = GetExpertsRequest(
            repo_path="/not/a/repo",
            file_path="file.py",
            window_days=90,
            limit=3,
        )

        result = await get_file_experts(ctx, request)

        assert isinstance(result, Error)
        assert "not inside a git repository" in result.description

    @pytest.mark.asyncio
    async def test_handles_file_not_found_error(self) -> None:
        """Test get_file_experts returns Error when file not found."""
        hunter = MockGitHunter(
            experts=FileNotFoundInRepoError(
                file_path="missing.py",
                repo_path="/repo",
            )
        )
        ctx = create_mock_ctx(hunter)
        request = GetExpertsRequest(
            repo_path="/repo",
            file_path="missing.py",
            window_days=90,
            limit=3,
        )

        result = await get_file_experts(ctx, request)

        assert isinstance(result, Error)
        assert "File not found" in result.description

    @pytest.mark.asyncio
    async def test_uses_custom_window_and_limit(self) -> None:
        """Test get_file_experts accepts custom window_days and limit."""
        hunter = MockGitHunter(experts=[])
        ctx = create_mock_ctx(hunter)
        request = GetExpertsRequest(
            repo_path="/repo",
            file_path="file.py",
            window_days=180,
            limit=5,
        )

        assert request.window_days == 180
        assert request.limit == 5

        await get_file_experts(ctx, request)
        # Just verify it runs without error
