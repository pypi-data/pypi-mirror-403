#!/usr/bin/env bash
# Publish bond to PyPI
#
# Usage:
#   ./scripts/publish.sh           # Publish to PyPI
#   ./scripts/publish.sh --test    # Publish to TestPyPI
#   ./scripts/publish.sh --dry-run # Build only, no upload
#
# Requirements:
#   - PYPI_TOKEN environment variable (or TESTPYPI_TOKEN for --test)
#   - uv installed
#
# The script will:
#   1. Run all quality checks (ruff, mypy, pytest)
#   2. Build the package
#   3. Upload to PyPI/TestPyPI

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
USE_TEST_PYPI=false
DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --test)
            USE_TEST_PYPI=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--test] [--dry-run]"
            echo ""
            echo "Options:"
            echo "  --test     Upload to TestPyPI instead of PyPI"
            echo "  --dry-run  Build only, skip upload"
            echo ""
            echo "Environment variables:"
            echo "  PYPI_TOKEN      API token for PyPI (required unless --dry-run)"
            echo "  TESTPYPI_TOKEN  API token for TestPyPI (required with --test)"
            exit 0
            ;;
    esac
done

echo -e "${GREEN}=== Bond PyPI Publisher ===${NC}"
echo ""

# Check for required tools
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed${NC}"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check for API token (unless dry run)
if [ "$DRY_RUN" = false ]; then
    if [ "$USE_TEST_PYPI" = true ]; then
        if [ -z "${TESTPYPI_TOKEN:-}" ]; then
            echo -e "${RED}Error: TESTPYPI_TOKEN environment variable not set${NC}"
            echo "Get a token from: https://test.pypi.org/manage/account/token/"
            exit 1
        fi
        UPLOAD_TOKEN="$TESTPYPI_TOKEN"
        REPO_URL="https://test.pypi.org/legacy/"
        REPO_NAME="TestPyPI"
    else
        if [ -z "${PYPI_TOKEN:-}" ]; then
            echo -e "${RED}Error: PYPI_TOKEN environment variable not set${NC}"
            echo "Get a token from: https://pypi.org/manage/account/token/"
            exit 1
        fi
        UPLOAD_TOKEN="$PYPI_TOKEN"
        REPO_URL="https://upload.pypi.org/legacy/"
        REPO_NAME="PyPI"
    fi
fi

# Get version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | head -1 | cut -d'"' -f2)
echo -e "Package version: ${YELLOW}${VERSION}${NC}"
echo ""

# Step 1: Quality checks
echo -e "${GREEN}[1/4] Running quality checks...${NC}"

echo "  - Running ruff format check..."
uv run ruff format --check src tests

echo "  - Running ruff lint..."
uv run ruff check src tests

echo "  - Running mypy..."
uv run mypy src/bond

echo "  - Running tests..."
uv run pytest tests -q --tb=short

echo -e "${GREEN}  ✓ All checks passed${NC}"
echo ""

# Step 2: Clean previous builds
echo -e "${GREEN}[2/4] Cleaning previous builds...${NC}"
rm -rf dist/ build/ *.egg-info src/*.egg-info
echo -e "${GREEN}  ✓ Cleaned${NC}"
echo ""

# Step 3: Build package
echo -e "${GREEN}[3/4] Building package...${NC}"
uv build
echo ""
echo "Built artifacts:"
ls -la dist/
echo -e "${GREEN}  ✓ Build complete${NC}"
echo ""

# Step 4: Upload
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[4/4] Dry run - skipping upload${NC}"
    echo ""
    echo "To upload manually:"
    echo "  uv run twine upload dist/*"
    echo ""
else
    echo -e "${GREEN}[4/4] Uploading to ${REPO_NAME}...${NC}"

    # Install twine if needed
    uv pip install twine --quiet

    # Upload using twine
    uv run twine upload \
        --repository-url "$REPO_URL" \
        --username __token__ \
        --password "$UPLOAD_TOKEN" \
        dist/*

    echo -e "${GREEN}  ✓ Upload complete${NC}"
    echo ""

    if [ "$USE_TEST_PYPI" = true ]; then
        echo -e "View package: ${YELLOW}https://test.pypi.org/project/bond-agent/${VERSION}/${NC}"
        echo ""
        echo "Install with:"
        echo "  pip install --index-url https://test.pypi.org/simple/ bond==${VERSION}"
    else
        echo -e "View package: ${YELLOW}https://pypi.org/project/bond-agent/${VERSION}/${NC}"
        echo ""
        echo "Install with:"
        echo "  pip install bond-agent==${VERSION}"
    fi
fi

echo ""
echo -e "${GREEN}Done!${NC}"
