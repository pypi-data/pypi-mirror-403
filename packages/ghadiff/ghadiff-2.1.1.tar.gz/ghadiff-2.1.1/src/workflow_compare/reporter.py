"""
Reporter for generating comparison output
"""

import json
from typing import Dict, Any


class Reporter:
    """Generate formatted reports from comparison data"""

    def __init__(self, comparison_data: Dict[str, Any]):
        """
        Initialize reporter with comparison data

        Args:
            comparison_data: Output from WorkflowComparator.get_full_comparison()
        """
        self.data = comparison_data

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable string"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    @staticmethod
    def _format_diff(diff_seconds: float) -> str:
        """Format duration difference with +/- sign"""
        sign = "+" if diff_seconds > 0 else ""
        return f"{sign}{Reporter._format_duration(abs(diff_seconds))}"

    @staticmethod
    def _get_status_emoji(conclusion: str) -> str:
        """Get emoji for conclusion status"""
        if conclusion == "success":
            return "✅"
        elif conclusion == "failure":
            return "❌"
        elif conclusion == "cancelled":
            return "🚫"
        elif conclusion == "skipped":
            return "⏭️"
        else:
            return "⚪"

    def to_text(self, verbose: bool = False) -> str:
        """
        Generate text report

        Args:
            verbose: Include detailed information

        Returns:
            Formatted text report
        """
        lines = []
        runs = self.data["runs"]

        lines.append("=" * 80)
        lines.append("GitHub Workflow Run Comparison")
        lines.append("=" * 80)
        lines.append("")

        # Run comparison
        lines.append("OVERVIEW")
        lines.append("-" * 80)

        branch1 = runs["run1"]["head_branch"]
        branch2 = runs["run2"]["head_branch"]

        lines.append(f"{branch1}: #{runs['run1']['run_number']} ({runs['run1']['id']})")
        lines.append(f"  SHA: {runs['run1']['head_sha']}")
        lines.append(f"  Status: {runs['run1']['status']} / {runs['run1']['conclusion']}")
        lines.append(f"  Duration: {self._format_duration(runs['run1']['duration_seconds'])}")
        lines.append("")
        lines.append(f"{branch2}: #{runs['run2']['run_number']} ({runs['run2']['id']})")
        lines.append(f"  SHA: {runs['run2']['head_sha']}")
        lines.append(f"  Status: {runs['run2']['status']} / {runs['run2']['conclusion']}")
        lines.append(f"  Duration: {self._format_duration(runs['run2']['duration_seconds'])}")
        lines.append("")

        diff_seconds = runs["duration_diff_seconds"]
        lines.append(f"Duration Difference: {self._format_diff(diff_seconds)}")

        if runs["conclusion_changed"]:
            lines.append(
                f"⚠️  Conclusion changed: {runs['run1']['conclusion']} → {runs['run2']['conclusion']}"
            )

        lines.append("")

        # Store branch names for later use
        self.branch1 = branch1
        self.branch2 = branch2

        # Jobs comparison
        lines.append("JOBS COMPARISON")
        lines.append("-" * 80)

        jobs = self.data["jobs"]

        # Categorize jobs
        only_in_run1 = [j for j in jobs if j["only_in_run1"]]
        only_in_run2 = [j for j in jobs if j["only_in_run2"]]
        in_both = [j for j in jobs if not j["only_in_run1"] and not j["only_in_run2"]]

        # For jobs in both, categorize by status
        both_skipped = []
        both_success = []
        status_changed = []
        failures = []

        for job in in_both:
            if job.get("conclusion_changed"):
                status_changed.append(job)
            elif job["run1"]["conclusion"] == "skipped" and job["run2"]["conclusion"] == "skipped":
                both_skipped.append(job)
            elif job["run1"]["conclusion"] == "success" and job["run2"]["conclusion"] == "success":
                # Both passed - hide completely regardless of time difference
                both_success.append(job)
            else:
                # Has failures
                failures.append(job)

        # Summary counts
        lines.append(f"Total jobs compared: {len(jobs)}")
        lines.append(f"  In both branches: {len(in_both)}")
        lines.append(f"  Only in {self.branch1}: {len(only_in_run1)}")
        lines.append(f"  Only in {self.branch2}: {len(only_in_run2)}")
        lines.append("")
        lines.append("Status Summary:")
        lines.append(f"  ✅ Both passed: {len(both_success)}")
        lines.append(f"  ⏭️  Both skipped: {len(both_skipped)}")
        lines.append(f"  ⚠️  Status changed between branches: {len(status_changed)}")
        lines.append(f"  ❌ Has failures: {len(failures)}")
        lines.append("")

        # Show interesting jobs first
        interesting_jobs = []

        # 1. Status changed jobs (most important)
        if status_changed:
            lines.append("=" * 80)
            lines.append("⚠️  JOBS WITH STATUS CHANGES")
            lines.append("=" * 80)
            lines.append("")
            for job in status_changed:
                interesting_jobs.append(job)

        # 2. Jobs with failures
        if failures:
            lines.append("=" * 80)
            lines.append("❌ JOBS WITH FAILURES")
            lines.append("=" * 80)
            lines.append("")
            for job in failures:
                interesting_jobs.append(job)

        # 3. Jobs only in one run
        if only_in_run1 or only_in_run2:
            lines.append("=" * 80)
            lines.append("❓ JOBS IN ONLY ONE RUN")
            lines.append("=" * 80)
            lines.append("")

        # Now show the details for interesting jobs
        for job in interesting_jobs:
            changed_marker = "⚠️ " if job.get("conclusion_changed") else ""
            lines.append(f"{changed_marker}{job['name']}")

            run1_emoji = self._get_status_emoji(job["run1"]["conclusion"])
            run2_emoji = self._get_status_emoji(job["run2"]["conclusion"])

            # Simple format - just status and error
            lines.append(f"   {self.branch1}: {run1_emoji} {job['run1']['conclusion']}")
            if job["run1"].get("error_message"):
                lines.append(f"          {job['run1']['error_message']}")

            lines.append(f"   {self.branch2}: {run2_emoji} {job['run2']['conclusion']}")
            if job["run2"].get("error_message"):
                lines.append(f"          {job['run2']['error_message']}")

            # Verbose mode - show timing and URLs
            if verbose:
                lines.append(f"   {self.branch1} details:")
                lines.append(
                    f"          Duration: {self._format_duration(job['run1']['duration_seconds'])}"
                )
                if job["run1"].get("failed_steps"):
                    lines.append(
                        f"          Failed steps: {', '.join(job['run1']['failed_steps'])}"
                    )
                if job["run1"].get("html_url"):
                    lines.append(f"          URL: {job['run1']['html_url']}")

                lines.append(f"   {self.branch2} details:")
                lines.append(
                    f"          Duration: {self._format_duration(job['run2']['duration_seconds'])}"
                )
                if job["run2"].get("failed_steps"):
                    lines.append(
                        f"          Failed steps: {', '.join(job['run2']['failed_steps'])}"
                    )
                if job["run2"].get("html_url"):
                    lines.append(f"          URL: {job['run2']['html_url']}")

                if "duration_diff_seconds" in job:
                    diff = job["duration_diff_seconds"]
                    diff_pct = job["duration_diff_percent"]
                    lines.append(f"   Time diff: {self._format_diff(diff)} ({diff_pct:+.1f}%)")

            lines.append("")

        # Show jobs only in one branch
        for job in only_in_run1:
            lines.append(f"❓ {job['name']} (only in {self.branch1})")
            lines.append(
                f"   {self.branch1}: {self._get_status_emoji(job['run1']['conclusion'])} {job['run1']['conclusion']}"
            )
            if verbose:
                lines.append(
                    f"          Duration: {self._format_duration(job['run1']['duration_seconds'])}"
                )
            lines.append("")

        for job in only_in_run2:
            lines.append(f"❓ {job['name']} (only in {self.branch2})")
            lines.append(
                f"   {self.branch2}: {self._get_status_emoji(job['run2']['conclusion'])} {job['run2']['conclusion']}"
            )
            if verbose:
                lines.append(
                    f"          Duration: {self._format_duration(job['run2']['duration_seconds'])}"
                )
            lines.append("")

        # Show verbose details if requested
        if verbose:
            if both_success:
                lines.append("=" * 80)
                lines.append(f"✅ JOBS THAT PASSED IN BOTH BRANCHES ({len(both_success)})")
                lines.append("=" * 80)
                lines.append("")
                for job in both_success:
                    lines.append(f"{job['name']}")
                    lines.append(
                        f"   {self.branch1}: ✅ success - {self._format_duration(job['run1']['duration_seconds'])}"
                    )
                    lines.append(
                        f"   {self.branch2}: ✅ success - {self._format_duration(job['run2']['duration_seconds'])}"
                    )
                    if "duration_diff_seconds" in job:
                        diff = job["duration_diff_seconds"]
                        diff_pct = job["duration_diff_percent"]
                        lines.append(f"   Diff:  {self._format_diff(diff)} ({diff_pct:+.1f}%)")
                    lines.append("")

            if both_skipped:
                lines.append("=" * 80)
                lines.append(f"⏭️  JOBS SKIPPED IN BOTH BRANCHES ({len(both_skipped)})")
                lines.append("=" * 80)
                lines.append("")
                for job in both_skipped[:10]:  # Limit to first 10
                    lines.append(f"⏭️  {job['name']}")
                if len(both_skipped) > 10:
                    lines.append(f"... and {len(both_skipped) - 10} more skipped jobs")
                lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def to_json(self, pretty: bool = True) -> str:
        """
        Generate JSON report

        Args:
            pretty: Pretty-print JSON

        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(self.data, indent=2)
        return json.dumps(self.data)

    def to_markdown(self) -> str:
        """
        Generate Markdown report

        Returns:
            Markdown formatted string
        """
        lines = []
        runs = self.data["runs"]

        lines.append("# GitHub Workflow Run Comparison")
        lines.append("")

        # Overview table
        lines.append("## Overview")
        lines.append("")
        lines.append("| Metric | Run 1 | Run 2 |")
        lines.append("|--------|-------|-------|")
        lines.append(
            f"| Run ID | #{runs['run1']['run_number']} ({runs['run1']['id']}) | #{runs['run2']['run_number']} ({runs['run2']['id']}) |"
        )
        lines.append(f"| Branch | {runs['run1']['head_branch']} | {runs['run2']['head_branch']} |")
        lines.append(f"| SHA | {runs['run1']['head_sha']} | {runs['run2']['head_sha']} |")
        lines.append(f"| Status | {runs['run1']['status']} | {runs['run2']['status']} |")
        lines.append(
            f"| Conclusion | {runs['run1']['conclusion']} | {runs['run2']['conclusion']} |"
        )
        lines.append(
            f"| Duration | {self._format_duration(runs['run1']['duration_seconds'])} | {self._format_duration(runs['run2']['duration_seconds'])} |"
        )
        lines.append("")

        diff_seconds = runs["duration_diff_seconds"]
        lines.append(f"**Duration Difference:** {self._format_diff(diff_seconds)}")
        lines.append("")

        # Jobs comparison
        lines.append("## Jobs Comparison")
        lines.append("")
        lines.append(
            "| Job Name | Run 1 Status | Run 1 Duration | Run 2 Status | Run 2 Duration | Difference |"
        )
        lines.append(
            "|----------|--------------|----------------|--------------|----------------|------------|"
        )

        for job in self.data["jobs"]:
            name = job["name"]

            if job["only_in_run1"]:
                r1_status = f"{self._get_status_emoji(job['run1']['conclusion'])} {job['run1']['conclusion']}"
                r1_duration = self._format_duration(job["run1"]["duration_seconds"])
                lines.append(f"| {name} | {r1_status} | {r1_duration} | - | - | - |")
            elif job["only_in_run2"]:
                r2_status = f"{self._get_status_emoji(job['run2']['conclusion'])} {job['run2']['conclusion']}"
                r2_duration = self._format_duration(job["run2"]["duration_seconds"])
                lines.append(f"| {name} | - | - | {r2_status} | {r2_duration} | - |")
            else:
                r1_status = f"{self._get_status_emoji(job['run1']['conclusion'])} {job['run1']['conclusion']}"
                r1_duration = self._format_duration(job["run1"]["duration_seconds"])
                r2_status = f"{self._get_status_emoji(job['run2']['conclusion'])} {job['run2']['conclusion']}"
                r2_duration = self._format_duration(job["run2"]["duration_seconds"])
                diff = (
                    self._format_diff(job["duration_diff_seconds"])
                    if "duration_diff_seconds" in job
                    else "-"
                )
                lines.append(
                    f"| {name} | {r1_status} | {r1_duration} | {r2_status} | {r2_duration} | {diff} |"
                )

        lines.append("")

        return "\n".join(lines)

    def to_html(self) -> str:
        """
        Generate HTML report

        Returns:
            HTML string
        """
        runs = self.data["runs"]

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Workflow Comparison</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2 {{
            color: #333;
        }}
        .overview {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .cancelled {{ color: #6c757d; }}
        .positive {{ color: #dc3545; }}
        .negative {{ color: #28a745; }}
        .neutral {{ color: #6c757d; }}
    </style>
</head>
<body>
    <h1>GitHub Workflow Run Comparison</h1>

    <div class="overview">
        <h2>Overview</h2>
        <table>
            <tr><th>Metric</th><th>Run 1</th><th>Run 2</th></tr>
            <tr><td>Run ID</td><td>#{runs['run1']['run_number']} ({runs['run1']['id']})</td><td>#{runs['run2']['run_number']} ({runs['run2']['id']})</td></tr>
            <tr><td>Branch</td><td>{runs['run1']['head_branch']}</td><td>{runs['run2']['head_branch']}</td></tr>
            <tr><td>SHA</td><td>{runs['run1']['head_sha']}</td><td>{runs['run2']['head_sha']}</td></tr>
            <tr><td>Status</td><td>{runs['run1']['status']}</td><td>{runs['run2']['status']}</td></tr>
            <tr><td>Conclusion</td><td class="{runs['run1']['conclusion']}">{runs['run1']['conclusion']}</td><td class="{runs['run2']['conclusion']}">{runs['run2']['conclusion']}</td></tr>
            <tr><td>Duration</td><td>{self._format_duration(runs['run1']['duration_seconds'])}</td><td>{self._format_duration(runs['run2']['duration_seconds'])}</td></tr>
        </table>
        <p><strong>Duration Difference:</strong> <span class="{'positive' if runs['duration_diff_seconds'] > 0 else 'negative'}">{self._format_diff(runs['duration_diff_seconds'])}</span></p>
    </div>

    <h2>Jobs Comparison</h2>
    <table>
        <tr>
            <th>Job Name</th>
            <th>Run 1 Status</th>
            <th>Run 1 Duration</th>
            <th>Run 2 Status</th>
            <th>Run 2 Duration</th>
            <th>Difference</th>
        </tr>
"""

        for job in self.data["jobs"]:
            if job["only_in_run1"]:
                html += f"""
        <tr>
            <td>{job['name']}</td>
            <td class="{job['run1']['conclusion']}">{self._get_status_emoji(job['run1']['conclusion'])} {job['run1']['conclusion']}</td>
            <td>{self._format_duration(job['run1']['duration_seconds'])}</td>
            <td>-</td>
            <td>-</td>
            <td>-</td>
        </tr>
"""
            elif job["only_in_run2"]:
                html += f"""
        <tr>
            <td>{job['name']}</td>
            <td>-</td>
            <td>-</td>
            <td class="{job['run2']['conclusion']}">{self._get_status_emoji(job['run2']['conclusion'])} {job['run2']['conclusion']}</td>
            <td>{self._format_duration(job['run2']['duration_seconds'])}</td>
            <td>-</td>
        </tr>
"""
            else:
                diff_class = "positive" if job["duration_diff_seconds"] > 0 else "negative"
                html += f"""
        <tr>
            <td>{job['name']}</td>
            <td class="{job['run1']['conclusion']}">{self._get_status_emoji(job['run1']['conclusion'])} {job['run1']['conclusion']}</td>
            <td>{self._format_duration(job['run1']['duration_seconds'])}</td>
            <td class="{job['run2']['conclusion']}">{self._get_status_emoji(job['run2']['conclusion'])} {job['run2']['conclusion']}</td>
            <td>{self._format_duration(job['run2']['duration_seconds'])}</td>
            <td class="{diff_class}">{self._format_diff(job['duration_diff_seconds'])}</td>
        </tr>
"""

        html += """
    </table>
</body>
</html>
"""

        return html
