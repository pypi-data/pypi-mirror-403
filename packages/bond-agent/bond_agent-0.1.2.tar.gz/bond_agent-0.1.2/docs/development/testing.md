# Testing

This guide covers testing patterns and practices for Bond development.

## Running Tests

Bond uses pytest with automatic async support:

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/tools/githunter/test_tools.py

# Run tests matching a pattern
uv run pytest -k "blame_line"

# Run a specific test class
uv run pytest tests/unit/tools/githunter/test_tools.py::TestBlameLine

# Run a specific test method
uv run pytest tests/unit/tools/githunter/test_tools.py::TestBlameLine::test_returns_blame_result
```

## Test Organization

Tests are organized by type and module:

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── agent/
│   │   └── test_bond_agent.py
│   ├── tools/
│   │   ├── githunter/
│   │   │   ├── test_adapter.py
│   │   │   ├── test_tools.py
│   │   │   └── test_types.py
│   │   ├── memory/
│   │   │   ├── test_backends.py
│   │   │   └── test_models.py
│   │   └── schema/
│   │       ├── test_models.py
│   │       ├── test_protocols.py
│   │       └── test_tools.py
│   └── trace/
│       ├── test_capture.py
│       ├── test_json_store.py
│       ├── test_models.py
│       └── test_replay.py
└── integration/             # Integration tests (future)
```

### Test File Naming

- `test_<module>.py` - Tests for a specific module
- `test_<feature>.py` - Tests for a specific feature

## Async Testing

pytest-asyncio is configured in automatic mode. Simply use `async def` for async tests:

```python
import pytest


class TestMyTool:
    """Tests for my_tool function."""

    @pytest.mark.asyncio
    async def test_returns_result(self) -> None:
        """Test my_tool returns expected result."""
        result = await my_tool(ctx, request)
        assert isinstance(result, MyResult)

    @pytest.mark.asyncio
    async def test_handles_error(self) -> None:
        """Test my_tool handles errors gracefully."""
        result = await my_tool(ctx, bad_request)
        assert isinstance(result, Error)
```

The `@pytest.mark.asyncio` decorator is optional when using `asyncio_mode = "auto"` in `pyproject.toml`, but including it makes the async nature explicit.

## Fixtures

### Creating Fixtures

Use fixtures for shared test data:

```python
import pytest
from datetime import UTC, datetime


@pytest.fixture
def sample_author() -> AuthorProfile:
    """Create a sample author profile for tests."""
    return AuthorProfile(
        git_email="dev@example.com",
        git_name="Developer",
        github_username="devuser",
    )


@pytest.fixture
def sample_result(sample_author: AuthorProfile) -> BlameResult:
    """Create a sample blame result for tests."""
    return BlameResult(
        line_no=42,
        content="    return result",
        author=sample_author,
        commit_hash="abc123def456",
        commit_date=datetime(2024, 6, 15, 10, 30, tzinfo=UTC),
        commit_message="Fix calculation bug",
    )
```

### Using Fixtures

Fixtures are injected by name:

```python
class TestBlameLine:
    @pytest.mark.asyncio
    async def test_returns_blame_result(
        self,
        sample_result: BlameResult,
    ) -> None:
        """Test blame_line returns BlameResult on success."""
        hunter = MockGitHunter(blame_result=sample_result)
        ctx = create_mock_ctx(hunter)
        request = BlameLineRequest(
            repo_path="/path/to/repo",
            file_path="src/processor.py",
            line_no=42,
        )

        result = await blame_line(ctx, request)

        assert isinstance(result, BlameResult)
        assert result.line_no == 42
```

## Mocking Adapters

### Mock Protocol Implementation

Create a mock class that implements the protocol:

```python
from pathlib import Path


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
        """Mock find_pr_discussion that returns configured result."""
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
        """Mock get_expert_for_file that returns configured result."""
        if isinstance(self._experts, Exception):
            raise self._experts
        return self._experts
```

### Mock RunContext

Create a helper to build mock contexts:

```python
from unittest.mock import MagicMock


def create_mock_ctx(hunter: MockGitHunter) -> MagicMock:
    """Create a mock RunContext with GitHunter deps."""
    ctx = MagicMock()
    ctx.deps = hunter
    return ctx
```

### Testing Success Cases

```python
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
```

### Testing Error Cases

```python
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
```

## Coverage

### Viewing Coverage

Coverage is enabled by default. After running tests:

```bash
# Terminal report (default)
uv run pytest

# HTML report
uv run pytest --cov-report=html
# Open htmlcov/index.html in browser

# XML report (for CI)
uv run pytest --cov-report=xml
```

### Coverage Configuration

Coverage is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-v --import-mode=importlib --cov=src/bond --cov-report=term-missing"
```

This enables:

- Verbose output (`-v`)
- Coverage for `src/bond` (`--cov=src/bond`)
- Missing line reporting (`--cov-report=term-missing`)

## Test Patterns

### Testing Models

Test Pydantic model validation:

```python
import pytest
from pydantic import ValidationError


class TestBlameLineRequest:
    """Tests for BlameLineRequest model."""

    def test_valid_request(self) -> None:
        """Test creating a valid request."""
        request = BlameLineRequest(
            repo_path="/path/to/repo",
            file_path="src/main.py",
            line_no=42,
        )
        assert request.line_no == 42

    def test_line_no_must_be_positive(self) -> None:
        """Test line_no validation rejects zero and negative."""
        with pytest.raises(ValidationError):
            BlameLineRequest(
                repo_path="/repo",
                file_path="file.py",
                line_no=0,
            )

    def test_defaults(self) -> None:
        """Test optional fields have correct defaults."""
        request = GetExpertsRequest(
            repo_path="/repo",
            file_path="file.py",
        )
        assert request.window_days == 90
        assert request.limit == 3
```

### Testing Protocols

Verify protocol conformance:

```python
def test_adapter_implements_protocol() -> None:
    """Test GitHunterAdapter satisfies GitHunterProtocol."""
    adapter = GitHunterAdapter()
    assert isinstance(adapter, GitHunterProtocol)
```

### Testing Tools

Test both success and error paths:

```python
class TestBlameLine:
    """Tests for blame_line tool function."""

    @pytest.mark.asyncio
    async def test_returns_blame_result(self) -> None:
        """Test successful blame operation."""
        # ... success case

    @pytest.mark.asyncio
    async def test_handles_file_not_found(self) -> None:
        """Test file not found error handling."""
        # ... error case

    @pytest.mark.asyncio
    async def test_handles_repo_not_found(self) -> None:
        """Test repo not found error handling."""
        # ... error case

    @pytest.mark.asyncio
    async def test_handles_line_out_of_range(self) -> None:
        """Test line out of range error handling."""
        # ... error case
```

## See Also

- [Development Overview](index.md) - Setup and commands
- [Adding Tools](adding-tools.md) - Creating testable tools
