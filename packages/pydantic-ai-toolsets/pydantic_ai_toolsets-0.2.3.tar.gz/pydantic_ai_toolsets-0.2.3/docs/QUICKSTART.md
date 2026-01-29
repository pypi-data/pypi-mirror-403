# Quick Start: Building Documentation Locally

## Fastest Way

```bash
# From project root
cd docs
pip install -e ..[docs]
make html

# View in browser
python3 -m http.server 8000 -d build/html
# Open http://localhost:8000
```

## Using Build Scripts

### Bash Script
```bash
./scripts/build_docs.sh
```

### Python Script
```bash
python3 scripts/build_docs.py
```

## What ReadTheDocs Does

ReadTheDocs runs these commands (from `.readthedocs.yaml`):

1. **Install dependencies**: `pip install -e .[docs]`
2. **Build docs**: `sphinx-build -b html docs/source docs/build/html`

You can replicate this exactly:

```bash
pip install -e .[docs]
sphinx-build -b html docs/source docs/build/html
```

## Common Commands

```bash
# Build HTML
cd docs && make html

# Clean build
cd docs && make clean

# Build with warnings as errors
cd docs && make html SPHINXOPTS="-W"

# Auto-rebuild on changes (requires sphinx-autobuild)
pip install sphinx-autobuild
cd docs && sphinx-autobuild source build/html
```

## Troubleshooting

- **Import errors**: Run `pip install -e .` first
- **Theme not found**: Ensure `sphinx-conestack-theme` is installed
- **Code blocks not rendering**: Check `conf.py` setup function is registered

For more details, see [BUILD.md](BUILD.md).
