# fn-2.4 Update exports and documentation

## Description
Update exports and API documentation.

### Update `__init__.py`

Add to `src/bond/tools/githunter/__init__.py`:

```python
from .tools import githunter_toolset
from ._models import BlameLineRequest, FindPRDiscussionRequest, GetExpertsRequest, Error

__all__ = [
    # Existing exports...
    # Add:
    "githunter_toolset",
    "BlameLineRequest",
    "FindPRDiscussionRequest",
    "GetExpertsRequest",
    "Error",
]
```

### Update API Docs

Add GitHunter section to `docs/api/tools.md`:

```markdown
## GitHunter Toolset

::: bond.tools.githunter.githunter_toolset
    options:
      show_source: true

### Request Models

::: bond.tools.githunter.BlameLineRequest

::: bond.tools.githunter.FindPRDiscussionRequest

::: bond.tools.githunter.GetExpertsRequest
```

### Verify Import

Test that this works:
```python
from bond.tools.githunter import githunter_toolset, BlameLineRequest
```
## Acceptance
- [ ] `__init__.py` exports `githunter_toolset` and request models
- [ ] `from bond.tools.githunter import githunter_toolset` works
- [ ] `docs/api/tools.md` has GitHunter section
- [ ] `mkdocs build --strict` passes
- [ ] All tests pass: `uv run pytest tests/unit/tools/githunter/ -v`
## Done summary
Updated exports and documentation:

__init__.py exports:
- githunter_toolset (list of 3 PydanticAI Tools)
- BlameLineRequest, FindPRDiscussionRequest, GetExpertsRequest
- Error model

docs/api/tools.md additions:
- GitHunter Toolset section
- Protocol documentation
- Type documentation (BlameResult, FileExpert, PRDiscussion, AuthorProfile)
- Request model documentation
- Toolset reference

Verification:
- from bond.tools.githunter import githunter_toolset works
- mkdocs build --strict passes
- All 51 GitHunter tests pass
## Evidence
- Commits: 8ebeefc
- Tests: tests/unit/tools/githunter/
- PRs: