"""
Workflow comparison logic
"""

from typing import Dict, Any, List
from datetime import datetime


class WorkflowComparator:
    """Compare two workflow runs and generate diff data"""

    def __init__(self, run1_data: Dict[str, Any], run2_data: Dict[str, Any], api_client=None):
        """
        Initialize comparator with two workflow run datasets

        Args:
            run1_data: First workflow run data (from GitHubAPI.get_workflow_run_full)
            run2_data: Second workflow run data (from GitHubAPI.get_workflow_run_full)
            api_client: Optional GitHubAPI client for fetching logs
        """
        self.run1_data = run1_data
        self.run2_data = run2_data
        self.api_client = api_client

    @staticmethod
    def _parse_duration(started_at: str, completed_at: str) -> float:
        """Parse duration between two ISO timestamp strings, return seconds"""
        if not started_at or not completed_at:
            return 0.0

        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        return (end - start).total_seconds()

    def _extract_error_from_job(self, job_id: int) -> str:
        """Extract key error message from job logs"""
        if not self.api_client:
            return None

        try:
            import re

            logs = self.api_client.get_job_logs(job_id)

            # Look for common error patterns (order matters - most specific first)
            error_patterns = [
                # GitHub Actions specific
                r"Error:\s*(.+?)$",
                # TT Metal specific errors
                r"TT_FATAL @ ([^:]+):(\d+): (.+?)$",
                r"TT_THROW @ ([^:]+):(\d+): (.+?)$",
                # Python/C++ errors
                r"what\(\):\s*(.+?)$",
                r"FAILED:\s*(.+?)$",
                r"AssertionError:\s*(.+?)$",
                r"RuntimeError:\s*(.+?)$",
                r"ValueError:\s*(.+?)$",
                r"terminate called after throwing an instance of \'([^\']+)\'",
                # Test failures
                r"FAILED\s+(.+?)\s+-",
                r"\[  FAILED  \]\s+(.+?)$",
                # Build errors
                r"error:\s*(.+?)$",
            ]

            errors = []
            for pattern in error_patterns:
                matches = re.findall(pattern, logs, re.MULTILINE | re.IGNORECASE)
                if matches:
                    if isinstance(matches[0], tuple):
                        errors.extend(matches[:3])  # Get first 3 matches
                    else:
                        errors.extend(matches[:3])

            if errors:
                # Format the error message
                if isinstance(errors[0], tuple) and len(errors[0]) >= 3:
                    # TT_FATAL/TT_THROW format
                    file_path, line_num, message = errors[0]
                    return f"{message} @ {file_path}:{line_num}"
                else:
                    # Simple error message - clean it up
                    error_msg = str(errors[0]).strip()
                    # Limit length but try to keep it meaningful
                    if len(error_msg) > 300:
                        error_msg = error_msg[:297] + "..."
                    return error_msg

            return None
        except Exception:
            return None

    def compare_runs(self) -> Dict[str, Any]:
        """
        Compare the two workflow runs at a high level

        Returns:
            Comparison data for the overall runs
        """
        run1 = self.run1_data["run"]
        run2 = self.run2_data["run"]

        run1_duration = self._parse_duration(run1.get("created_at"), run1.get("updated_at"))
        run2_duration = self._parse_duration(run2.get("created_at"), run2.get("updated_at"))

        return {
            "run1": {
                "id": run1.get("id"),
                "name": run1.get("name"),
                "status": run1.get("status"),
                "conclusion": run1.get("conclusion"),
                "created_at": run1.get("created_at"),
                "updated_at": run1.get("updated_at"),
                "duration_seconds": run1_duration,
                "run_number": run1.get("run_number"),
                "workflow_name": run1.get("name"),
                "head_branch": run1.get("head_branch"),
                "head_sha": run1.get("head_sha", "")[:7],
            },
            "run2": {
                "id": run2.get("id"),
                "name": run2.get("name"),
                "status": run2.get("status"),
                "conclusion": run2.get("conclusion"),
                "created_at": run2.get("created_at"),
                "updated_at": run2.get("updated_at"),
                "duration_seconds": run2_duration,
                "run_number": run2.get("run_number"),
                "workflow_name": run2.get("name"),
                "head_branch": run2.get("head_branch"),
                "head_sha": run2.get("head_sha", "")[:7],
            },
            "duration_diff_seconds": run2_duration - run1_duration,
            "conclusion_changed": run1.get("conclusion") != run2.get("conclusion"),
        }

    def compare_jobs(self) -> List[Dict[str, Any]]:
        """
        Compare jobs between the two runs

        Returns:
            List of job comparisons
        """
        jobs1 = {job["name"]: job for job in self.run1_data["jobs"]}
        jobs2 = {job["name"]: job for job in self.run2_data["jobs"]}

        # Get all unique job names
        all_job_names = set(jobs1.keys()) | set(jobs2.keys())

        comparisons = []

        for job_name in sorted(all_job_names):
            job1 = jobs1.get(job_name)
            job2 = jobs2.get(job_name)

            comparison = {
                "name": job_name,
                "only_in_run1": job1 is not None and job2 is None,
                "only_in_run2": job1 is None and job2 is not None,
            }

            if job1:
                job1_duration = self._parse_duration(
                    job1.get("started_at"), job1.get("completed_at")
                )
                # Extract failed steps if job failed
                failed_steps = []
                error_message = None
                if job1.get("conclusion") == "failure":
                    for step in job1.get("steps", []):
                        if step.get("conclusion") == "failure":
                            failed_steps.append(step.get("name"))
                    # Try to fetch error message from logs
                    try:
                        error_message = self._extract_error_from_job(job1.get("id"))
                    except Exception:
                        pass  # If we can't get logs, continue without them

                comparison["run1"] = {
                    "id": job1.get("id"),
                    "status": job1.get("status"),
                    "conclusion": job1.get("conclusion"),
                    "started_at": job1.get("started_at"),
                    "completed_at": job1.get("completed_at"),
                    "duration_seconds": job1_duration,
                    "failed_steps": failed_steps,
                    "error_message": error_message,
                    "html_url": job1.get("html_url"),
                }
            else:
                comparison["run1"] = None

            if job2:
                job2_duration = self._parse_duration(
                    job2.get("started_at"), job2.get("completed_at")
                )
                # Extract failed steps if job failed
                failed_steps = []
                error_message = None
                if job2.get("conclusion") == "failure":
                    for step in job2.get("steps", []):
                        if step.get("conclusion") == "failure":
                            failed_steps.append(step.get("name"))
                    # Try to fetch error message from logs
                    try:
                        error_message = self._extract_error_from_job(job2.get("id"))
                    except Exception:
                        pass  # If we can't get logs, continue without them

                comparison["run2"] = {
                    "id": job2.get("id"),
                    "status": job2.get("status"),
                    "conclusion": job2.get("conclusion"),
                    "started_at": job2.get("started_at"),
                    "completed_at": job2.get("completed_at"),
                    "duration_seconds": job2_duration,
                    "failed_steps": failed_steps,
                    "error_message": error_message,
                    "html_url": job2.get("html_url"),
                }
            else:
                comparison["run2"] = None

            # Calculate differences
            if job1 and job2:
                comparison["conclusion_changed"] = job1.get("conclusion") != job2.get("conclusion")
                comparison["duration_diff_seconds"] = (
                    comparison["run2"]["duration_seconds"] - comparison["run1"]["duration_seconds"]
                )
                comparison["duration_diff_percent"] = (
                    (
                        comparison["duration_diff_seconds"]
                        / comparison["run1"]["duration_seconds"]
                        * 100
                    )
                    if comparison["run1"]["duration_seconds"] > 0
                    else 0
                )

            comparisons.append(comparison)

        return comparisons

    def compare_steps(self, job_name: str) -> List[Dict[str, Any]]:
        """
        Compare steps for a specific job

        Args:
            job_name: Name of the job to compare steps for

        Returns:
            List of step comparisons
        """
        jobs1 = {job["name"]: job for job in self.run1_data["jobs"]}
        jobs2 = {job["name"]: job for job in self.run2_data["jobs"]}

        job1 = jobs1.get(job_name)
        job2 = jobs2.get(job_name)

        if not job1 or not job2:
            return []

        steps1 = {step["name"]: step for step in job1.get("steps", [])}
        steps2 = {step["name"]: step for step in job2.get("steps", [])}

        all_step_names = set(steps1.keys()) | set(steps2.keys())

        comparisons = []

        for step_name in all_step_names:
            step1 = steps1.get(step_name)
            step2 = steps2.get(step_name)

            comparison = {
                "name": step_name,
                "only_in_run1": step1 is not None and step2 is None,
                "only_in_run2": step1 is None and step2 is not None,
            }

            if step1:
                step1_duration = self._parse_duration(
                    step1.get("started_at"), step1.get("completed_at")
                )
                comparison["run1"] = {
                    "status": step1.get("status"),
                    "conclusion": step1.get("conclusion"),
                    "started_at": step1.get("started_at"),
                    "completed_at": step1.get("completed_at"),
                    "duration_seconds": step1_duration,
                }
            else:
                comparison["run1"] = None

            if step2:
                step2_duration = self._parse_duration(
                    step2.get("started_at"), step2.get("completed_at")
                )
                comparison["run2"] = {
                    "status": step2.get("status"),
                    "conclusion": step2.get("conclusion"),
                    "started_at": step2.get("started_at"),
                    "completed_at": step2.get("completed_at"),
                    "duration_seconds": step2_duration,
                }
            else:
                comparison["run2"] = None

            # Calculate differences
            if step1 and step2:
                comparison["conclusion_changed"] = step1.get("conclusion") != step2.get(
                    "conclusion"
                )
                comparison["duration_diff_seconds"] = (
                    comparison["run2"]["duration_seconds"] - comparison["run1"]["duration_seconds"]
                )
                comparison["duration_diff_percent"] = (
                    (
                        comparison["duration_diff_seconds"]
                        / comparison["run1"]["duration_seconds"]
                        * 100
                    )
                    if comparison["run1"]["duration_seconds"] > 0
                    else 0
                )

            comparisons.append(comparison)

        return comparisons

    def get_full_comparison(self) -> Dict[str, Any]:
        """
        Get complete comparison of both workflow runs

        Returns:
            Complete comparison data
        """
        return {"runs": self.compare_runs(), "jobs": self.compare_jobs()}
