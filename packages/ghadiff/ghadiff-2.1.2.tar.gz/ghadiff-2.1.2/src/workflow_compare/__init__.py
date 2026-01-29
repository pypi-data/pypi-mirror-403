"""
Workflow Compare - A tool to compare GitHub workflow runs
"""

__version__ = "2.1.2"

from .api import GitHubAPI
from .comparator import WorkflowComparator
from .reporter import Reporter

__all__ = ["GitHubAPI", "WorkflowComparator", "Reporter"]
