"""Tests for action models"""

import pytest
from agentic_test_framework.actions import (
    NavigateAction,
    ClickAction,
    TypeAction,
    ScreenshotAction,
    WaitAction,
    AssertAction,
    ExtractAction,
    ActionType,
    ActionResult
)


class TestActionModels:
    """Test action model creation and validation"""
    
    def test_navigate_action(self):
        """Test NavigateAction creation"""
        action = NavigateAction(
            description="Go to example.com",
            url="https://example.com"
        )
        assert action.type == ActionType.NAVIGATE
        assert action.url == "https://example.com"
        assert action.description == "Go to example.com"
    
    def test_click_action_with_selector(self):
        """Test ClickAction with selector"""
        action = ClickAction(
            description="Click button",
            selector="#submit-btn"
        )
        assert action.type == ActionType.CLICK
        assert action.selector == "#submit-btn"
        assert action.text is None
    
    def test_click_action_with_text(self):
        """Test ClickAction with text"""
        action = ClickAction(
            description="Click login link",
            text="Login"
        )
        assert action.type == ActionType.CLICK
        assert action.text == "Login"
        assert action.selector is None
    
    def test_type_action(self):
        """Test TypeAction creation"""
        action = TypeAction(
            description="Enter username",
            selector="#username",
            text="testuser"
        )
        assert action.type == ActionType.TYPE
        assert action.selector == "#username"
        assert action.text == "testuser"
    
    def test_screenshot_action(self):
        """Test ScreenshotAction creation"""
        action = ScreenshotAction(
            description="Take screenshot",
            name="test_screen",
            full_page=False
        )
        assert action.type == ActionType.SCREENSHOT
        assert action.name == "test_screen"
        assert action.full_page is False
    
    def test_wait_action_duration(self):
        """Test WaitAction with duration"""
        action = WaitAction(
            description="Wait 2 seconds",
            duration=2000
        )
        assert action.type == ActionType.WAIT
        assert action.duration == 2000
        assert action.selector is None
    
    def test_wait_action_selector(self):
        """Test WaitAction with selector"""
        action = WaitAction(
            description="Wait for element",
            selector="#loading"
        )
        assert action.type == ActionType.WAIT
        assert action.selector == "#loading"
        assert action.duration is None
    
    def test_assert_action_text(self):
        """Test AssertAction with expected text"""
        action = AssertAction(
            description="Verify text",
            condition="Page contains welcome",
            expected_text="Welcome"
        )
        assert action.type == ActionType.ASSERT
        assert action.expected_text == "Welcome"
        assert action.condition == "Page contains welcome"
    
    def test_assert_action_url(self):
        """Test AssertAction with expected URL"""
        action = AssertAction(
            description="Verify URL",
            condition="URL contains login",
            expected_url="login"
        )
        assert action.type == ActionType.ASSERT
        assert action.expected_url == "login"
    
    def test_extract_action(self):
        """Test ExtractAction creation"""
        action = ExtractAction(
            description="Extract version",
            selector=".version",
            text="Version"
        )
        assert action.type == ActionType.EXTRACT
        assert action.selector == ".version"
        assert action.text == "Version"


class TestActionResult:
    """Test ActionResult model"""
    
    def test_successful_result(self):
        """Test successful action result"""
        action = NavigateAction(description="Navigate", url="https://example.com")
        result = ActionResult(
            success=True,
            action=action,
            message="Navigation successful",
            metadata={"url": "https://example.com"}
        )
        assert result.success is True
        assert result.message == "Navigation successful"
        assert result.error is None
        assert result.screenshot_path is None
        assert result.extracted_data is None
        assert result.metadata["url"] == "https://example.com"
    
    def test_failed_result_with_error(self):
        """Test failed action result with error"""
        action = ClickAction(description="Click", selector="#missing")
        result = ActionResult(
            success=False,
            action=action,
            message="Element not found",
            error="Timeout: Element #missing not found",
            metadata={"expected": "Button", "actual": "Not found"}
        )
        assert result.success is False
        assert result.error == "Timeout: Element #missing not found"
        assert result.metadata["expected"] == "Button"
        assert result.metadata["actual"] == "Not found"
    
    def test_result_with_screenshot(self):
        """Test result with screenshot path"""
        action = ScreenshotAction(description="Screenshot", name="test")
        result = ActionResult(
            success=True,
            action=action,
            message="Screenshot captured",
            screenshot_path="/path/to/screenshot.png"
        )
        assert result.screenshot_path == "/path/to/screenshot.png"
    
    def test_result_with_extracted_data(self):
        """Test result with extracted data"""
        action = ExtractAction(description="Extract", selector=".version")
        result = ActionResult(
            success=True,
            action=action,
            message="Data extracted",
            extracted_data="v1.2.3"
        )
        assert result.extracted_data == "v1.2.3"
