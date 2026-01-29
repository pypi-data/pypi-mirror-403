# Example usage script
# This demonstrates how to use workflow-compare programmatically

from workflow_compare import GitHubAPI, WorkflowComparator, Reporter
import os

# Get token from environment
token = os.environ.get('GITHUB_TOKEN')

# Initialize API client (defaults to tenstorrent/tt-metal)
api = GitHubAPI(token=token)

# Or specify a different repo
# api = GitHubAPI(token=token, repo="owner/repo")

# Fetch two workflow runs
print("Fetching workflow run 1...")
run1 = api.get_workflow_run_full(12345678)  # Replace with actual run ID

print("Fetching workflow run 2...")
run2 = api.get_workflow_run_full(12345679)  # Replace with actual run ID

# Compare the runs
print("Comparing runs...")
comparator = WorkflowComparator(run1, run2)
comparison = comparator.get_full_comparison()

# Generate reports in different formats
reporter = Reporter(comparison)

# Text report
print("\n" + "="*80)
print(reporter.to_text())

# Save JSON report
with open('comparison.json', 'w') as f:
    f.write(reporter.to_json())
print("\nJSON report saved to comparison.json")

# Save Markdown report
with open('comparison.md', 'w') as f:
    f.write(reporter.to_markdown())
print("Markdown report saved to comparison.md")

# Save HTML report
with open('comparison.html', 'w') as f:
    f.write(reporter.to_html())
print("HTML report saved to comparison.html")
