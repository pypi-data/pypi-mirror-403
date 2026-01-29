# Workflow Compare

Compare GitHub workflow runs with detailed analysis.

## Publishing to PyPI

### Prerequisites

1. Install build tools:
```bash
pip install build twine
```

2. Get PyPI credentials:
   - Create account at https://pypi.org
   - Generate API token at https://pypi.org/manage/account/token/

### Build the Package

```bash
cd workflow-compare
python -m build
```

This creates distribution files in `dist/`:
- `workflow_compare-0.1.0-py3-none-any.whl`
- `workflow_compare-0.1.0.tar.gz`

### Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ workflow-compare
```

### Publish to PyPI

```bash
python -m twine upload dist/*
```

Enter your PyPI username and API token when prompted.

### After Publishing

Install from PyPI:
```bash
pip install workflow-compare
```

### Version Updates

To publish a new version:
1. Update version in `pyproject.toml`
2. Clean old builds: `rm -rf dist/ build/ *.egg-info`
3. Build: `python -m build`
4. Upload: `python -m twine upload dist/*`

## Quick Start After Installation

```bash
# Set your GitHub token
export GITHUB_TOKEN=your_token_here

# Compare two workflow runs
workflow-compare 12345678 12345679

# Generate HTML report
workflow-compare 12345678 12345679 --format html -o report.html
```

See README.md for full documentation.
