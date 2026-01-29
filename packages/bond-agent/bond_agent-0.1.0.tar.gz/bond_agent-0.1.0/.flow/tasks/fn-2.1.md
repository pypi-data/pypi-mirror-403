# fn-2.1 Create GitHunter request models

## Description
Create Pydantic request models for GitHunter tools in `src/bond/tools/githunter/_models.py`.

### Models to Create

```python
class BlameLineRequest(BaseModel):
    """Request for blame_line tool."""
    repo_path: str  # String, converted to Path in tool
    file_path: str
    line_no: int = Field(ge=1, description="Line number (1-indexed)")

class FindPRDiscussionRequest(BaseModel):
    """Request for find_pr_discussion tool."""
    repo_path: str
    commit_hash: str = Field(min_length=7, description="Full or abbreviated SHA")

class GetExpertsRequest(BaseModel):
    """Request for get_expert_for_file tool."""
    repo_path: str
    file_path: str
    window_days: int = Field(default=90, ge=0, description="Days of history (0=all time)")
    limit: int = Field(default=3, ge=1, le=10, description="Max experts to return")
```

### Also Add

- `Error` model following `memory/_models.py:177-187` pattern
- Union types for return values: `BlameResult | Error`, etc.

### Reference Files

- Pattern: `src/bond/tools/memory/_models.py`
- Types: `src/bond/tools/githunter/_types.py` (BlameResult, PRDiscussion, FileExpert)
## Acceptance
- [ ] `_models.py` exists with BlameLineRequest, FindPRDiscussionRequest, GetExpertsRequest
- [ ] All models have Field validators (ge, min_length, etc.)
- [ ] Error model exists for union return types
- [ ] `mypy src/bond/tools/githunter/_models.py` passes
- [ ] `ruff check src/bond/tools/githunter/_models.py` passes
## Done summary
Created _models.py with GitHunter request models:
- BlameLineRequest (repo_path, file_path, line_no with ge=1 validator)
- FindPRDiscussionRequest (repo_path, commit_hash with min_length=7 validator)
- GetExpertsRequest (repo_path, file_path, window_days=90 default, limit=3 default)
- Error model for union return types in tool responses

All models follow the Annotated[..., Field(...)] pattern from memory/_models.py.
Passed mypy and ruff checks.
## Evidence
- Commits: cdc4a2f
- Tests:
- PRs: