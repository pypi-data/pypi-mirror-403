#!/bin/bash
# Script to run coverage analysis and identify gaps

set -e

echo "Running test coverage analysis..."
echo "=================================="
echo ""

# Run tests with coverage
pytest \
    --cov=pydantic_ai_toolsets \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    --cov-fail-under=90 \
    -v

echo ""
echo "Coverage report generated:"
echo "  - Terminal: See above"
echo "  - HTML: htmlcov/index.html"
echo "  - XML: coverage.xml"
echo ""
echo "To view HTML report: open htmlcov/index.html"
echo ""
echo "If coverage is below 90%, review the 'Missing' column above"
echo "and add tests for uncovered lines."
