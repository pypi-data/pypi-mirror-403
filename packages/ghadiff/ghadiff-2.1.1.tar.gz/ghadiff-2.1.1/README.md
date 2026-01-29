# ghadiff

A Python CLI tool to compare two GitHub Actions workflow runs with detailed analysis of timing, status changes, and job differences.

## Features

- 🔍 Compare any two GitHub workflow runs
- 📊 Detailed job and step-level analysis
- ⏱️ Duration comparisons with percentage changes
- 🎨 Multiple output formats: Text, JSON, Markdown, HTML
- 🚀 Defaults to `tenstorrent/tt-metal` repository
- 🔒 GitHub API token support with rate limit handling

## Installation

### From PyPI (once published)

```bash
pip install ghadiff
```

### From source

```bash
git clone https://github.com/Aswintechie/ghadiff.git
cd ghadiff
pip install -e .
```

## Quick Start

### Prerequisites

You'll need a GitHub personal access token for API access:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` and `workflow` scopes
3. Set it as an environment variable:

```bash
export GITHUB_TOKEN=your_token_here
```

### Basic Usage

Compare two workflow runs (defaults to `tenstorrent/tt-metal`):

```bash
ghadiff 12345678 12345679
```

The first argument is Run 1 (baseline), the second is Run 2 (comparison).

### With Custom Repository

```bash
ghadiff 12345678 12345679 --repo owner/repo
```

### Generate Reports

Text format (default):
```bash
ghadiff 12345678 12345679
```

JSON format:
```bash
ghadiff 12345678 12345679 --format json
```

Markdown format:
```bash
ghadiff 12345678 12345679 --format markdown -o report.md
```

HTML format:
```bash
ghadiff 12345678 12345679 --format html -o report.html
```

## Output Examples

### Text Format

```
================================================================================
GitHub Workflow Run Comparison
================================================================================

OVERVIEW
--------------------------------------------------------------------------------
Run 1: #1234 (12345678)
  Branch: main
  SHA: abc1234
  Status: completed / success
  Duration: 45.2m

Run 2: #1235 (12345679)
  Branch: main
  SHA: def5678
  Status: completed / success
  Duration: 38.7m

Duration Difference: -6.5m

JOBS COMPARISON
--------------------------------------------------------------------------------
Total jobs compared: 25
  In both runs: 25
  Only in Run 1: 0
  Only in Run 2: 0

build-and-test
   Run 1: ✅ success    - 12.3m
   Run 2: ✅ success    - 10.1m
   Diff:  -2.2m (-17.9%)

...
```

### JSON Format

Full structured data with all workflow, job, and step details for programmatic access.

### HTML Format

Beautiful, responsive HTML report with color-coded status indicators and sortable tables.

## CLI Interface Example
```bash
ghadiff 12345678 12345679 \
  --repo tenstorrent/tt-metal \
  --format html \
  --output report.html
```

positional arguments:
  run1                  First workflow run ID
  run2                  Second workflow run ID

optional arguments:
  -h, --help            show this help message and exit
  --repo REPO           Repository in format owner/repo
                        (default: tenstorrent/tt-metal)
  --token TOKEN         GitHub personal access token
                        (or use GITHUB_TOKEN env var)
  --format {text,json,markdown,html}
                        Output format (default: text)
  --output OUTPUT, -o OUTPUT
                        Output file (default: stdout)
  --verbose, -v         Verbose output (text format only)
```

## Python API

You can also use the package programmatically:

```python
from workflow_compare import GitHubAPI, WorkflowComparator, Reporter

# Initialize API client
api = GitHubAPI(token="your_token", repo="tenstorrent/tt-metal")

# Fetch workflow runs
run1 = api.get_workflow_run_full(12345678)
run2 = api.get_workflow_run_full(12345679)

# Compare
comparator = WorkflowComparator(run1, run2)
comparison = comparator.get_full_comparison()

# Generate report
reporter = Reporter(comparison)
print(reporter.to_text())
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/Aswintechie/ghadiff.git
cd ghadiff
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
```

## Use Cases

- **Performance Regression Detection**: Compare workflow runs before and after code changes
- **CI/CD Optimization**: Identify which jobs got faster or slower
- **Debugging Failures**: Compare a failing run with a successful baseline
- **Release Validation**: Ensure new releases don't introduce timing regressions
- **Infrastructure Changes**: Validate runner or environment changes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Links

- Repository: https://github.com/Aswintechie/ghadiff
- Issues: https://github.com/Aswintechie/ghadiff/issues
- PyPI: https://pypi.org/project/ghadiff/

## Acknowledgments

Built for the Tenstorrent tt-metal project to improve CI/CD workflow analysis.
