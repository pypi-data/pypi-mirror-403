# fn-1.7 Fix version and metadata inconsistencies

## Description

Fix version and metadata inconsistencies between pyproject.toml and package __init__.py.

### Issues to Fix

1. **Version mismatch**
   - `pyproject.toml` says `version = "0.0.1"`
   - `src/bond/__init__.py` says `__version__ = "0.1.0"`
   - Decision: Use `0.1.0` as canonical (more mature signaling)

2. **Author metadata**
   - Current: `authors = [{ name = "dataing team" }]`
   - Should be: Bond-specific author/team

3. **Project URLs** (if missing)
   - Add documentation URL (once deployed)
   - Add repository URL

4. **Package description**
   - Current may be generic
   - Update to reflect "Forensic Runtime" positioning

### Files to Update

| File | Changes |
|------|---------|
| `pyproject.toml` | version, authors, description, urls |
| `src/bond/__init__.py` | Verify __version__ matches |
## Acceptance
- [ ] pyproject.toml version matches src/bond/__init__.py version
- [ ] Author metadata is updated (not "dataing team")
- [ ] Project description reflects Bond positioning
- [ ] `pip install -e .` works without errors
- [ ] `python -c "import bond; print(bond.__version__)"` prints correct version
## Done summary
Fixed version and metadata inconsistencies. Version synced to 0.1.0, description updated to Forensic Runtime positioning, authors updated to Bond Contributors, added project URLs and PyPI classifiers. Verified: pip install -e . and python -c 'import bond; print(bond.__version__)' both work correctly.
## Evidence
- Commits:
- Tests:
- PRs: