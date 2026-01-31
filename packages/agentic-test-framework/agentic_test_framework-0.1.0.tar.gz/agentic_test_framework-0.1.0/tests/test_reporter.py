"""Tests for HTML reporter"""

import pytest
from pathlib import Path
from datetime import datetime
from agentic_test_framework.reporter import HTMLReporter
from agentic_test_framework.actions import (
    NavigateAction,
    ClickAction,
    ActionResult,
    ActionType
)


class TestHTMLReporter:
    """Test HTML report generation"""
    
    @pytest.fixture
    def reporter(self, tmp_path):
        """Create reporter with temporary directory"""
        return HTMLReporter(output_dir=str(tmp_path))
    
    @pytest.fixture
    def sample_results(self):
        """Create sample test results"""
        nav_action = NavigateAction(description="Go to example.com", url="https://example.com")
        nav_result = ActionResult(
            success=True,
            action=nav_action,
            message="Navigated successfully",
            metadata={"url": "https://example.com"}
        )
        
        click_action = ClickAction(description="Click button", selector="#btn")
        click_result = ActionResult(
            success=False,
            action=click_action,
            message="Failed to click",
            error="Element not found",
            metadata={"expected": "#btn", "actual": "Element not visible"}
        )
        
        return [nav_result, click_result]
    
    def test_reporter_initialization(self, tmp_path):
        """Test reporter initializes with correct directory"""
        reporter = HTMLReporter(output_dir=str(tmp_path / "reports"))
        assert reporter.output_dir.exists()
        assert reporter.output_dir.is_dir()
    
    def test_generate_report_creates_file(self, reporter, sample_results):
        """Test report file is created"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        report_path = reporter.generate_report(
            test_description="Test scenario",
            results=sample_results,
            start_time=start_time,
            end_time=end_time
        )
        
        assert Path(report_path).exists()
        assert report_path.endswith(".html")
    
    def test_report_contains_test_description(self, reporter, sample_results):
        """Test report includes test description"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        report_path = reporter.generate_report(
            test_description="Go to example.com and click button",
            results=sample_results,
            start_time=start_time,
            end_time=end_time
        )
        
        content = Path(report_path).read_text()
        assert "Go to example.com and click button" in content
    
    def test_report_shows_pass_fail_counts(self, reporter, sample_results):
        """Test report displays correct pass/fail counts"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        report_path = reporter.generate_report(
            test_description="Test",
            results=sample_results,
            start_time=start_time,
            end_time=end_time
        )
        
        content = Path(report_path).read_text()
        # Check that report contains count of 1 for both passed and failed
        assert ">1<" in content or "1 passed" in content.lower()
        assert ">1<" in content or "1 failed" in content.lower()
    
    def test_report_includes_status(self, reporter, sample_results):
        """Test report shows FAIL status when tests fail"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        report_path = reporter.generate_report(
            test_description="Test",
            results=sample_results,
            start_time=start_time,
            end_time=end_time
        )
        
        content = Path(report_path).read_text()
        assert "FAIL" in content
    
    def test_report_shows_duration(self, reporter, sample_results):
        """Test report displays execution duration"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        report_path = reporter.generate_report(
            test_description="Test",
            results=sample_results,
            start_time=start_time,
            end_time=end_time
        )
        
        content = Path(report_path).read_text()
        assert "Duration" in content
    
    def test_report_contains_expected_vs_actual(self, reporter):
        """Test report shows expected vs actual comparison for failures"""
        action = ClickAction(description="Click", selector="#btn")
        result = ActionResult(
            success=False,
            action=action,
            message="Failed",
            error="Not found",
            metadata={
                "expected": "Button element",
                "actual": "Element not visible"
            }
        )
        
        start_time = datetime.now()
        end_time = datetime.now()
        
        report_path = reporter.generate_report(
            test_description="Test",
            results=[result],
            start_time=start_time,
            end_time=end_time
        )
        
        content = Path(report_path).read_text()
        assert "Expected:" in content
        assert "Actual:" in content
        assert "Button element" in content
        assert "Element not visible" in content
    
    def test_report_includes_action_types(self, reporter, sample_results):
        """Test report displays action types"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        report_path = reporter.generate_report(
            test_description="Test",
            results=sample_results,
            start_time=start_time,
            end_time=end_time
        )
        
        content = Path(report_path).read_text()
        assert "ActionType.NAVIGATE" in content or "navigate" in content.lower()
        assert "ActionType.CLICK" in content or "click" in content.lower()
    
    def test_report_is_valid_html(self, reporter, sample_results):
        """Test report is valid HTML"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        report_path = reporter.generate_report(
            test_description="Test",
            results=sample_results,
            start_time=start_time,
            end_time=end_time
        )
        
        content = Path(report_path).read_text()
        assert content.startswith("<!DOCTYPE html>")
        assert "<html" in content
        assert "</html>" in content
        assert "<body>" in content or "<body" in content
        assert "</body>" in content
