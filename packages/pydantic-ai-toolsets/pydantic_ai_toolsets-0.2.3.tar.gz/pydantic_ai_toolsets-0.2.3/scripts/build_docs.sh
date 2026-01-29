#!/bin/bash
# Build script for Sphinx documentation
# This mimics the ReadTheDocs build process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs"

echo -e "${GREEN}Building Sphinx documentation...${NC}"
echo "Project root: $PROJECT_ROOT"
echo "Docs directory: $DOCS_DIR"
echo ""

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Are you in the project root?${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "Python version: $PYTHON_VERSION"

# Install/upgrade dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
if command -v uv &> /dev/null; then
    echo "Using uv..."
    cd "$PROJECT_ROOT"
    uv pip install -e .[docs]
else
    echo "Using pip..."
    cd "$PROJECT_ROOT"
    pip install -e .[docs]
fi

# Change to docs directory
cd "$DOCS_DIR"

# Clean previous build (optional, comment out if you want incremental builds)
# echo -e "${YELLOW}Cleaning previous build...${NC}"
# make clean 2>/dev/null || true

# Build documentation
echo -e "${YELLOW}Building HTML documentation...${NC}"
if command -v make &> /dev/null; then
    make html
else
    # Fallback to sphinx-build directly
    sphinx-build -b html source build/html
fi

# Check if build was successful
if [ -f "$DOCS_DIR/build/html/index.html" ]; then
    echo ""
    echo -e "${GREEN}✓ Documentation built successfully!${NC}"
    echo ""
    echo "To view the documentation:"
    echo "  cd $DOCS_DIR/build/html"
    echo "  python3 -m http.server 8000"
    echo ""
    echo "Then open http://localhost:8000 in your browser"
    echo ""
    echo "Or open directly:"
    echo "  file://$DOCS_DIR/build/html/index.html"
else
    echo -e "${RED}✗ Build failed! Check the errors above.${NC}"
    exit 1
fi
