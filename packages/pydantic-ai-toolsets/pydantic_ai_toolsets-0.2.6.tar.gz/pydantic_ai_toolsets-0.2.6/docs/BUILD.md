# Building Documentation Locally

This guide explains how to build and test the Sphinx documentation locally, matching the ReadTheDocs environment.

## Quick Start

### Option 1: Using Make (Recommended)

```bash
# Navigate to docs directory
cd docs

# Install dependencies (if using uv)
uv pip install -e ..[docs]

# Or if using pip
pip install -e ..[docs]

# Build HTML documentation
make html

# View the documentation
# Open docs/build/html/index.html in your browser
```

### Option 2: Using Sphinx Directly

```bash
# Navigate to docs directory
cd docs

# Install dependencies
pip install -e ..[docs]

# Build HTML documentation
sphinx-build -b html source build/html

# View the documentation
# Open docs/build/html/index.html in your browser
```

### Option 3: Using the Build Script

```bash
# From project root
./scripts/build_docs.sh
```

## Detailed Steps

### 1. Install Dependencies

The documentation requires the `docs` extra dependencies:

```bash
# Using uv (recommended)
uv pip install -e .[docs]

# Using pip
pip install -e .[docs]
```

This installs:
- `sphinx>=9.1.0`
- `sphinx-conestack-theme>=1.1.0`
- `myst-parser>=5.0.0`

### 2. Build the Documentation

```bash
cd docs
make html
```

This will:
- Read source files from `docs/source/`
- Generate HTML output in `docs/build/html/`
- Show any warnings or errors

### 3. View the Documentation

After building, open `docs/build/html/index.html` in your web browser:

```bash
# Linux
xdg-open docs/build/html/index.html

# macOS
open docs/build/html/index.html

# Windows
start docs/build/html/index.html
```

Or use a simple HTTP server:

```bash
cd docs/build/html
python -m http.server 8000
# Then open http://localhost:8000 in your browser
```

### 4. Clean Build (if needed)

To remove all build artifacts:

```bash
cd docs
make clean
```

Or manually:

```bash
rm -rf docs/build
```

## Testing Different Build Types

### HTML (default)
```bash
make html
```

### PDF (requires LaTeX)
```bash
make latexpdf
```

### Check for Errors
```bash
make html SPHINXOPTS="-W"  # Treat warnings as errors
```

## Matching ReadTheDocs Environment

To exactly match ReadTheDocs:

1. **Python Version**: Use Python 3.12 (as specified in `.readthedocs.yaml`)
2. **Dependencies**: Install using `pip install -e .[docs]` (same as RTD)
3. **Build Command**: RTD uses `sphinx-build -b html source build/html`

## Troubleshooting

### Import Errors
If you see import errors, make sure the package is installed:
```bash
pip install -e .
```

### Theme Not Found
If the Conestack theme is not found:
```bash
pip install sphinx-conestack-theme
```

### Code Blocks Not Rendering
Check that the custom processor in `conf.py` is working. You can test by adding a print statement in the `convert_markdown_code_blocks` function.

### Warnings
Most warnings are non-critical. To see only errors:
```bash
make html SPHINXOPTS="-W --keep-going"
```

## Continuous Development

For continuous development, you can use `sphinx-autobuild`:

```bash
pip install sphinx-autobuild
cd docs
sphinx-autobuild source build/html
```

This will automatically rebuild when you change source files and serve the docs at `http://localhost:8000`.
