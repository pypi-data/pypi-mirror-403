# fn-2.3 Add GitHunter toolset tests

## Description
Add tests for GitHunter tools in `tests/unit/tools/githunter/test_tools.py`.

### Test Structure

```python
class MockGitHunter:
    """Mock implementation of GitHunterProtocol for testing."""

    async def blame_line(self, repo_path, file_path, line_no):
        return BlameResult(...)

    async def find_pr_discussion(self, repo_path, commit_hash):
        return PRDiscussion(...) or None

    async def get_expert_for_file(self, repo_path, file_path, window_days, limit):
        return [FileExpert(...)]

@pytest.fixture
def mock_hunter():
    return MockGitHunter()

@pytest.fixture
def run_context(mock_hunter):
    # Create RunContext with mock deps
    ...

class TestBlameLine:
    async def test_returns_blame_result(self, run_context):
        ...

    async def test_handles_error(self, run_context):
        ...
```

### Test Cases

1. **blame_line**: Success case, FileNotFoundError, LineOutOfRangeError
2. **find_pr_discussion**: Success case, None case (no PR), RateLimitedError
3. **get_file_experts**: Success case, empty list, RepoNotFoundError

### Reference Files

- Pattern: `tests/unit/tools/schema/test_tools.py`
- Mock pattern: `tests/unit/tools/memory/test_backends.py`
## Acceptance
- [ ] `test_tools.py` exists with MockGitHunter class
- [ ] Tests cover success cases for all 3 tools
- [ ] Tests cover error handling (GitHunterError → Error)
- [ ] `uv run pytest tests/unit/tools/githunter/test_tools.py -v` passes
- [ ] All existing GitHunter tests still pass
## Done summary
Created test_tools.py with 13 comprehensive tests:

TestBlameLine (4 tests):
- test_returns_blame_result: success case
- test_handles_file_not_found_error
- test_handles_line_out_of_range_error
- test_handles_repo_not_found_error

TestFindPRDiscussion (4 tests):
- test_returns_pr_discussion: success case
- test_returns_none_when_no_pr
- test_handles_rate_limited_error
- test_handles_repo_not_found_error

TestGetFileExperts (5 tests):
- test_returns_expert_list: success case
- test_returns_empty_list
- test_handles_repo_not_found_error
- test_handles_file_not_found_error
- test_uses_custom_window_and_limit

Includes MockGitHunter class implementing GitHunterProtocol.
All tests pass with mypy and ruff checks.
## Evidence
- Commits: 69dcdcc
- Tests: tests/unit/tools/githunter/test_tools.py
- PRs: