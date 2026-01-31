#!/bin/bash
# Publish emdash package to PyPI using uv
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== EmDash Package Publisher ===${NC}"
echo

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Run from project root.${NC}"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed.${NC}"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Get current version
VERSION=$(grep -m1 'version = ' pyproject.toml | cut -d'"' -f2)
echo -e "Current version: ${GREEN}$VERSION${NC}"
echo

# Ask for version bump
echo "Version bump options:"
echo "  1) Patch (0.1.0 -> 0.1.1)"
echo "  2) Minor (0.1.0 -> 0.2.0)"
echo "  3) Major (0.1.0 -> 1.0.0)"
echo "  4) Keep current version"
echo
read -p "Select option [1-4]: " bump_option

# Parse current version
IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"

case $bump_option in
    1)
        NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
        # Update version in pyproject.toml
        sed -i '' "s/version = \"$VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
        ;;
    2)
        NEW_VERSION="$MAJOR.$((MINOR + 1)).0"
        sed -i '' "s/version = \"$VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
        ;;
    3)
        NEW_VERSION="$((MAJOR + 1)).0.0"
        sed -i '' "s/version = \"$VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
        ;;
    4)
        NEW_VERSION="$VERSION"
        echo "Keeping version $VERSION"
        ;;
    *) echo -e "${RED}Invalid option${NC}"; exit 1 ;;
esac

echo -e "Publishing version: ${GREEN}$NEW_VERSION${NC}"
echo

# Ask for target
echo "Publish target:"
echo "  1) PyPI (production)"
echo "  2) TestPyPI (testing)"
echo "  3) Build only (no publish)"
echo
read -p "Select target [1-3]: " target_option

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf dist/

# Build package
echo -e "${YELLOW}Building package...${NC}"
uv build

echo -e "${GREEN}Build complete!${NC}"
ls -la dist/
echo

case $target_option in
    1)
        echo -e "${YELLOW}Publishing to PyPI...${NC}"
        if [ -z "$PYPI_TOKEN" ]; then
            echo "Enter PyPI token (or set PYPI_TOKEN env var):"
            read -s PYPI_TOKEN
        fi
        uv publish --token "$PYPI_TOKEN"
        echo -e "${GREEN}Published to PyPI!${NC}"
        echo -e "Install with: ${YELLOW}uv pip install emdash==$NEW_VERSION${NC}"
        ;;
    2)
        echo -e "${YELLOW}Publishing to TestPyPI...${NC}"
        if [ -z "$TEST_PYPI_TOKEN" ]; then
            echo "Enter TestPyPI token (or set TEST_PYPI_TOKEN env var):"
            read -s TEST_PYPI_TOKEN
        fi
        uv publish --publish-url https://test.pypi.org/legacy/ --token "$TEST_PYPI_TOKEN"
        echo -e "${GREEN}Published to TestPyPI!${NC}"
        echo -e "Install with: ${YELLOW}uv pip install -i https://test.pypi.org/simple/ emdash==$NEW_VERSION${NC}"
        ;;
    3)
        echo -e "${GREEN}Build complete. Package not published.${NC}"
        echo "To publish manually:"
        echo "  PyPI:     uv publish --token \$PYPI_TOKEN"
        echo "  TestPyPI: uv publish --publish-url https://test.pypi.org/legacy/ --token \$TEST_PYPI_TOKEN"
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}Done!${NC}"
