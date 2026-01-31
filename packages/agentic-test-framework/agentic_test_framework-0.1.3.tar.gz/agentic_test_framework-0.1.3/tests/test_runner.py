"""Tests for test runner"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agentic_test_framework.runner import AgenticTestRunner
from agentic_test_framework.actions import (
    NavigateAction,
    ActionResult,
    ActionType
)


class TestTestRunner:
    """Test TestRunner functionality"""
    
    @pytest.fixture
    def runner(self, mock_openai_key):
        """Create test runner instance"""
        with patch('agentic_test_framework.parser.openai_parser.OpenAI'):
            return AgenticTestRunner(
                openai_api_key=mock_openai_key,
                browser_type="chromium",
                headless=True,
                generate_report=False
            )
    
    def test_runner_initialization(self, mock_openai_key):
        """Test runner initializes correctly"""
        with patch('agentic_test_framework.parser.openai_parser.OpenAI'):
            runner = AgenticTestRunner(
                openai_api_key=mock_openai_key,
                browser_type="firefox",
                headless=True
            )
            assert runner.browser_type == "firefox"
            assert runner.headless is True
            assert runner.parser is not None
    
    def test_runner_with_report_generation(self, mock_openai_key):
        """Test runner with report generation enabled"""
        with patch('agentic_test_framework.parser.openai_parser.OpenAI'):
            runner = AgenticTestRunner(
                openai_api_key=mock_openai_key,
                generate_report=True
            )
            assert runner.generate_report is True
            assert runner.reporter is not None
    
    def test_runner_without_report_generation(self, mock_openai_key):
        """Test runner with report generation disabled"""
        with patch('agentic_test_framework.parser.openai_parser.OpenAI'):
            runner = AgenticTestRunner(
                openai_api_key=mock_openai_key,
                generate_report=False
            )
            assert runner.generate_report is False
            assert runner.reporter is None
    
    @patch('agentic_test_framework.parser.OpenAIParser.parse')
    @patch('agentic_test_framework.executor.PlaywrightExecutor')
    def test_run_simple_test(self, mock_executor, mock_parse, runner):
        """Test running a simple test scenario"""
        # Mock parser
        nav_action = NavigateAction(description="Navigate", url="https://example.com")
        mock_parse.return_value = [nav_action]
        
        # Mock executor
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        result = ActionResult(
            success=True,
            action=nav_action,
            message="Success"
        )
        mock_executor_instance.execute.return_value = result
        
        # Run test
        results = runner.run("Go to example.com")
        
        assert len(results) == 1
        assert results[0].success is True
        mock_parse.assert_called_once()
    
    @patch('agentic_test_framework.parser.OpenAIParser.parse')
    @patch('agentic_test_framework.executor.PlaywrightExecutor')
    def test_run_returns_empty_on_no_actions(self, mock_executor, mock_parse, runner):
        """Test run returns empty list when no actions generated"""
        mock_parse.return_value = []
        
        results = runner.run("Invalid test description")
        
        assert results == []
        mock_executor.assert_not_called()
    
    @patch('agentic_test_framework.runner.test_runner.PlaywrightExecutor')
    @patch('agentic_test_framework.parser.OpenAIParser.parse')
    def test_run_handles_failed_actions(self, mock_parse, mock_executor, runner):
        """Test run handles failed actions correctly"""
        # Mock parser
        action = NavigateAction(description="Navigate", url="https://example.com")
        mock_parse.return_value = [action]
        
        # Mock executor with failure
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        result = ActionResult(
            success=False,
            action=action,
            message="Failed",
            error="Connection timeout"
        )
        mock_executor_instance.execute.return_value = result
        
        # Run test
        results = runner.run("Go to example.com")
        
        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error == "Connection timeout"
