"""
Unit tests for workflow_compare package
"""

import pytest
from unittest.mock import Mock, patch
from workflow_compare.api import GitHubAPI
from workflow_compare.comparator import WorkflowComparator
from workflow_compare.reporter import Reporter


class TestGitHubAPI:
    """Test GitHubAPI class"""
    
    def test_init_with_defaults(self):
        """Test initialization with default values"""
        api = GitHubAPI()
        assert api.repo == "tenstorrent/tt-metal"
        assert api.token is None or isinstance(api.token, str)
    
    def test_init_with_custom_repo(self):
        """Test initialization with custom repository"""
        api = GitHubAPI(repo="owner/repo")
        assert api.repo == "owner/repo"
    
    @patch('workflow_compare.api.requests.Session.get')
    def test_get_workflow_run(self, mock_get):
        """Test getting workflow run"""
        mock_response = Mock()
        mock_response.json.return_value = {'id': 123, 'name': 'Test'}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        api = GitHubAPI(token="test_token")
        result = api.get_workflow_run(123)
        
        assert result['id'] == 123
        assert result['name'] == 'Test'


class TestWorkflowComparator:
    """Test WorkflowComparator class"""
    
    @pytest.fixture
    def sample_run_data(self):
        """Sample workflow run data"""
        return {
            'run': {
                'id': 123,
                'name': 'Test Workflow',
                'status': 'completed',
                'conclusion': 'success',
                'created_at': '2025-01-01T00:00:00Z',
                'updated_at': '2025-01-01T00:10:00Z',
                'run_number': 1,
                'head_branch': 'main',
                'head_sha': 'abc123def456'
            },
            'jobs': [
                {
                    'id': 1,
                    'name': 'Build',
                    'status': 'completed',
                    'conclusion': 'success',
                    'started_at': '2025-01-01T00:00:00Z',
                    'completed_at': '2025-01-01T00:05:00Z',
                    'steps': []
                }
            ]
        }
    
    def test_compare_runs(self, sample_run_data):
        """Test run comparison"""
        comparator = WorkflowComparator(sample_run_data, sample_run_data)
        comparison = comparator.compare_runs()
        
        assert comparison['run1']['id'] == 123
        assert comparison['run2']['id'] == 123
        assert comparison['duration_diff_seconds'] == 0
    
    def test_compare_jobs(self, sample_run_data):
        """Test job comparison"""
        comparator = WorkflowComparator(sample_run_data, sample_run_data)
        jobs = comparator.compare_jobs()
        
        assert len(jobs) == 1
        assert jobs[0]['name'] == 'Build'
        assert not jobs[0]['only_in_run1']
        assert not jobs[0]['only_in_run2']


class TestReporter:
    """Test Reporter class"""
    
    @pytest.fixture
    def sample_comparison(self):
        """Sample comparison data"""
        return {
            'runs': {
                'run1': {
                    'id': 123,
                    'name': 'Test',
                    'status': 'completed',
                    'conclusion': 'success',
                    'duration_seconds': 600,
                    'run_number': 1,
                    'head_branch': 'main',
                    'head_sha': 'abc123'
                },
                'run2': {
                    'id': 124,
                    'name': 'Test',
                    'status': 'completed',
                    'conclusion': 'success',
                    'duration_seconds': 550,
                    'run_number': 2,
                    'head_branch': 'main',
                    'head_sha': 'def456'
                },
                'duration_diff_seconds': -50,
                'conclusion_changed': False
            },
            'jobs': []
        }
    
    def test_to_text(self, sample_comparison):
        """Test text report generation"""
        reporter = Reporter(sample_comparison)
        text = reporter.to_text()
        
        assert 'GitHub Workflow Run Comparison' in text
        assert 'main: #1' in text
        assert 'main: #2' in text
    
    def test_to_json(self, sample_comparison):
        """Test JSON report generation"""
        reporter = Reporter(sample_comparison)
        json_output = reporter.to_json()
        
        assert '"run1"' in json_output
        assert '"run2"' in json_output
    
    def test_to_markdown(self, sample_comparison):
        """Test Markdown report generation"""
        reporter = Reporter(sample_comparison)
        md = reporter.to_markdown()
        
        assert '# GitHub Workflow Run Comparison' in md
        assert '## Overview' in md
        assert '| Metric | Run 1 | Run 2 |' in md
    
    def test_to_html(self, sample_comparison):
        """Test HTML report generation"""
        reporter = Reporter(sample_comparison)
        html = reporter.to_html()
        
        assert '<!DOCTYPE html>' in html
        assert '<title>Workflow Comparison</title>' in html
