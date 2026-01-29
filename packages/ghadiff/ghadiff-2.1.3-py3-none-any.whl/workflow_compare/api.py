"""
GitHub API client for fetching workflow run data
"""

import os
import requests
from typing import Dict, Any, Optional, List
import time


class GitHubAPI:
    """Client for interacting with GitHub API to fetch workflow data"""

    BASE_URL = "https://api.github.com"
    DEFAULT_REPO = "tenstorrent/tt-metal"

    def __init__(self, token: Optional[str] = None, repo: Optional[str] = None):
        """
        Initialize GitHub API client

        Args:
            token: GitHub personal access token (defaults to GITHUB_TOKEN env var)
            repo: Repository in format "owner/repo" (defaults to tenstorrent/tt-metal)
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.repo = repo or self.DEFAULT_REPO
        self.session = requests.Session()

        if self.token:
            self.session.headers.update(
                {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}
            )
        else:
            print("Warning: No GitHub token provided. API rate limits will be restrictive.")
            self.session.headers.update({"Accept": "application/vnd.github.v3+json"})

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to GitHub API with rate limit handling"""
        url = f"{self.BASE_URL}{endpoint}"

        while True:
            response = self.session.get(url, params=params)

            # Handle rate limiting
            if response.status_code == 403 and "X-RateLimit-Remaining" in response.headers:
                if int(response.headers["X-RateLimit-Remaining"]) == 0:
                    reset_time = int(response.headers["X-RateLimit-Reset"])
                    sleep_time = reset_time - int(time.time()) + 1
                    print(f"Rate limit exceeded. Waiting {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    continue

            response.raise_for_status()
            return response.json()

    def get_workflow_run(self, run_id: int) -> Dict[str, Any]:
        """
        Get workflow run details

        Args:
            run_id: Workflow run ID

        Returns:
            Workflow run data
        """
        endpoint = f"/repos/{self.repo}/actions/runs/{run_id}"
        return self._make_request(endpoint)

    def get_workflow_jobs(self, run_id: int) -> List[Dict[str, Any]]:
        """
        Get all jobs for a workflow run with proper pagination

        Args:
            run_id: Workflow run ID

        Returns:
            List of job data
        """
        endpoint = f"/repos/{self.repo}/actions/runs/{run_id}/jobs"
        jobs = []
        page = 1
        per_page = 100

        while True:
            params = {"per_page": per_page, "page": page}
            data = self._make_request(endpoint, params=params)

            page_jobs = data.get("jobs", [])
            jobs.extend(page_jobs)

            # If we got fewer jobs than per_page, we've reached the end
            if len(page_jobs) < per_page:
                break

            page += 1

        return jobs

    def get_workflow_logs(self, run_id: int) -> bytes:
        """
        Download workflow run logs (returns as zip file content)

        Args:
            run_id: Workflow run ID

        Returns:
            Zip file content as bytes
        """
        endpoint = f"/repos/{self.repo}/actions/runs/{run_id}/logs"
        url = f"{self.BASE_URL}{endpoint}"

        response = self.session.get(url)
        response.raise_for_status()
        return response.content

    def get_job_logs(self, job_id: int) -> str:
        """
        Get logs for a specific job

        Args:
            job_id: Job ID

        Returns:
            Log content as string
        """
        endpoint = f"/repos/{self.repo}/actions/jobs/{job_id}/logs"
        url = f"{self.BASE_URL}{endpoint}"

        response = self.session.get(url)
        response.raise_for_status()
        return response.text

    def get_workflow_run_full(self, run_id: int) -> Dict[str, Any]:
        """
        Get complete workflow run data including jobs

        Args:
            run_id: Workflow run ID

        Returns:
            Complete workflow data with jobs
        """
        run_data = self.get_workflow_run(run_id)
        jobs_data = self.get_workflow_jobs(run_id)

        return {"run": run_data, "jobs": jobs_data}
