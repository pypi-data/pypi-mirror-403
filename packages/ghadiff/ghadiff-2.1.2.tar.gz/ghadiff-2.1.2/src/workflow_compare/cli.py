#!/usr/bin/env python3
"""
Command-line interface for workflow-compare
"""

import argparse
import sys

from .api import GitHubAPI
from .comparator import WorkflowComparator
from .reporter import Reporter


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Compare two GitHub workflow runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two runs (defaults to tenstorrent/tt-metal repo)
  workflow-compare 12345678 12345679

  # Compare runs with specific repo
  workflow-compare 12345678 12345679 --repo owner/repo

  # Generate HTML report
  workflow-compare 12345678 12345679 --format html --output report.html

  # Use GitHub token from environment or provide directly
  export GITHUB_TOKEN=your_token_here
  workflow-compare 12345678 12345679

  # Or provide token directly
  workflow-compare 12345678 12345679 --token your_token_here
        """,
    )

    parser.add_argument("run1", type=int, help="First workflow run ID")

    parser.add_argument("run2", type=int, help="Second workflow run ID")

    parser.add_argument(
        "--repo",
        type=str,
        default=GitHubAPI.DEFAULT_REPO,
        help=f"Repository in format owner/repo (default: {GitHubAPI.DEFAULT_REPO})",
    )

    parser.add_argument(
        "--token", type=str, help="GitHub personal access token (or use GITHUB_TOKEN env var)"
    )

    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "html"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output (text format only)"
    )

    args = parser.parse_args()

    try:
        # Initialize API client
        print(f"Fetching workflow runs from {args.repo}...", file=sys.stderr)
        api = GitHubAPI(token=args.token, repo=args.repo)

        # Fetch workflow data
        print(f"Fetching Run 1 (ID: {args.run1})...", file=sys.stderr)
        run1_data = api.get_workflow_run_full(args.run1)

        print(f"Fetching Run 2 (ID: {args.run2})...", file=sys.stderr)
        run2_data = api.get_workflow_run_full(args.run2)

        # Compare
        print("Comparing workflow runs...", file=sys.stderr)
        comparator = WorkflowComparator(run1_data, run2_data, api_client=api)
        comparison = comparator.get_full_comparison()

        # Generate report
        reporter = Reporter(comparison)

        if args.format == "text":
            output = reporter.to_text(verbose=args.verbose)
        elif args.format == "json":
            output = reporter.to_json(pretty=True)
        elif args.format == "markdown":
            output = reporter.to_markdown()
        elif args.format == "html":
            output = reporter.to_html()
        else:
            output = reporter.to_text()

        # Write output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"\nReport written to: {args.output}", file=sys.stderr)
        else:
            print(output)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
