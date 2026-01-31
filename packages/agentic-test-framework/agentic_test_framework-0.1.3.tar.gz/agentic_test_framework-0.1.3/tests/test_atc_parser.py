"""Tests for ATC file parser"""

import pytest
from pathlib import Path
from agentic_test_framework.parser import ATCParser, ATCScenario, ATCTestSuite


class TestATCParser:
    """Test ATC file format parser"""
    
    @pytest.fixture
    def parser(self):
        """Create ATC parser instance"""
        return ATCParser()
    
    @pytest.fixture
    def simple_atc_content(self):
        """Simple ATC file content"""
        return """# Simple Test Suite

Description: A simple test suite

@config browser=firefox
@config headless=true

## Scenario: First Test
@tag smoke
@id TC-001
@reference REQ-001

Go to example.com
Take a screenshot

## Scenario: Second Test
@tag regression
@id TC-002
@reference REQ-002

Navigate to google.com
Search for playwright
"""
    
    def test_parse_simple_content(self, parser, simple_atc_content):
        """Test parsing simple ATC content"""
        suite = parser.parse_content(simple_atc_content)
        
        assert suite.name == "Simple Test Suite"
        assert suite.description == "A simple test suite"
        assert suite.config["browser"] == "firefox"
        assert suite.config["headless"] is True
        assert len(suite.scenarios) == 2
    
    def test_parse_scenarios(self, parser, simple_atc_content):
        """Test parsing scenarios"""
        suite = parser.parse_content(simple_atc_content)
        
        assert suite.scenarios[0].name == "First Test"
        assert "smoke" in suite.scenarios[0].tags
        assert "Go to example.com" in suite.scenarios[0].steps
        assert suite.scenarios[0].id == "TC-001"
        assert suite.scenarios[0].reference == "REQ-001"
        
        assert suite.scenarios[1].name == "Second Test"
        assert "regression" in suite.scenarios[1].tags
        assert suite.scenarios[1].id == "TC-002"
        assert suite.scenarios[1].reference == "REQ-002"
    
    def test_parse_config(self, parser):
        """Test parsing configuration"""
        content = """# Test
        
@config browser=webkit
@config headless=false
@config timeout=5000

## Scenario: Test
Do something
"""
        suite = parser.parse_content(content)
        
        assert suite.config["browser"] == "webkit"
        assert suite.config["headless"] is False
        assert suite.config["timeout"] == "5000"
    
    def test_parse_tags(self, parser):
        """Test parsing multiple tags"""
        content = """# Test

## Scenario: Tagged Test
@tag smoke
@tag login
@tag critical

Test steps
"""
        suite = parser.parse_content(content)
        
        scenario = suite.scenarios[0]
        assert "smoke" in scenario.tags
        assert "login" in scenario.tags
        assert "critical" in scenario.tags
    
    def test_parse_without_description(self, parser):
        """Test parsing without description"""
        content = """# Test Suite

## Scenario: Test
Do something
"""
        suite = parser.parse_content(content)
        
        assert suite.name == "Test Suite"
        assert suite.description == ""
    
    def test_parse_multiple_scenarios(self, parser):
        """Test parsing multiple scenarios"""
        content = """# Multi Test

## Scenario: One
Step 1

## Scenario: Two
Step 2

## Scenario: Three
Step 3
"""
        suite = parser.parse_content(content)
        
        assert len(suite.scenarios) == 3
        assert suite.scenarios[0].name == "One"
        assert suite.scenarios[1].name == "Two"
        assert suite.scenarios[2].name == "Three"
    
    def test_parse_with_test_keyword(self, parser):
        """Test parsing with 'Test:' instead of 'Scenario:'"""
        content = """# Suite

## Test: My Test
Do something
"""
        suite = parser.parse_content(content)
        
        assert len(suite.scenarios) == 1
        assert suite.scenarios[0].name == "My Test"
    
    def test_validate_empty_suite(self, parser):
        """Test validation of empty suite"""
        suite = ATCTestSuite(name="Empty", scenarios=[])
        issues = parser.validate(suite)
        
        assert len(issues) > 0
        assert any("No test scenarios" in issue for issue in issues)
    
    def test_validate_scenario_without_steps(self, parser):
        """Test validation of scenario without steps"""
        scenario = ATCScenario(
            name="Empty",
            steps="",
            attributes={"id": "TC-EMPTY", "reference": "REQ-EMPTY"}
        )
        suite = ATCTestSuite(name="Test", scenarios=[scenario])
        
        issues = parser.validate(suite)
        
        assert len(issues) > 0
        assert any("No steps" in issue for issue in issues)
    
    def test_validate_valid_suite(self, parser):
        """Test validation of valid suite"""
        scenario = ATCScenario(
            name="Valid",
            steps="Go to example.com\nTake screenshot",
            attributes={"id": "TC-VALID", "reference": "REQ-VALID"}
        )
        suite = ATCTestSuite(name="Test", scenarios=[scenario])
        
        issues = parser.validate(suite)
        
        assert len(issues) == 0
    
    def test_parse_multiline_steps(self, parser):
        """Test parsing multi-line test steps"""
        content = """# Test

## Scenario: Multi-line
Go to example.com
Type 'username' into field
Click button
Wait 2 seconds
Verify page contains 'Welcome'
Take a screenshot
"""
        suite = parser.parse_content(content)
        
        steps = suite.scenarios[0].steps
        assert "Go to example.com" in steps
        assert "Type 'username' into field" in steps
        assert "Take a screenshot" in steps
    
    def test_parse_empty_lines_between_scenarios(self, parser):
        """Test handling empty lines between scenarios"""
        content = """# Test

## Scenario: First
Step 1


## Scenario: Second

Step 2
"""
        suite = parser.parse_content(content)
        
        assert len(suite.scenarios) == 2
        assert suite.scenarios[0].steps.strip() == "Step 1"
        assert suite.scenarios[1].steps.strip() == "Step 2"
    
    def test_parse_file_not_found(self, parser):
        """Test parsing non-existent file"""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent.atc")
    
    def test_parse_no_suite_name(self, parser):
        """Test parsing without suite name"""
        content = """
## Scenario: Test
Do something
"""
        suite = parser.parse_content(content)
        
        assert suite.name == "Unnamed Test Suite"
        assert len(suite.scenarios) == 1
