"""Parser for .atc (Agentic Test Case) files"""

import re
from pathlib import Path
from typing import Dict, List, Optional


class ATCScenario:
    """Represents a single test scenario from an ATC file"""
    
    def __init__(
        self,
        name: str,
        steps: str,
        tags: List[str] = None,
        attributes: Dict[str, str] = None
    ):
        self.name = name
        self.steps = steps
        self.tags = tags or []
        self.attributes = attributes or {}
        self.id = self.attributes.get("id")
        self.reference = self.attributes.get("reference")


class ATCTestSuite:
    """Represents a complete ATC test file"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Dict = None,
        scenarios: List[ATCScenario] = None
    ):
        self.name = name
        self.description = description
        self.config = config or {}
        self.scenarios = scenarios or []


class ATCParser:
    """Parser for .atc (Agentic Test Case) files
    
    ATC Format:
    -----------
    # Test Suite Name
    
    Description: Optional test suite description
    
    @config browser=chromium
    @config headless=false
    
    ## Scenario: Test name
    @tag smoke
    @tag login
    
    Go to example.com
    Click login button
    Verify page contains 'Welcome'
    Take a screenshot
    
    ## Scenario: Another test
    More test steps...
    """
    
    def __init__(self):
        self.suite_name_pattern = re.compile(r'^#\s+(.+)$')
        self.scenario_pattern = re.compile(r'^##\s+(?:Scenario|Test):\s*(.+)$', re.IGNORECASE)
        self.config_pattern = re.compile(r'^@config\s+(\w+)\s*=\s*(.+)$')
        self.tag_pattern = re.compile(r'^@tag\s+(\w+)$')
        self.description_pattern = re.compile(r'^Description:\s*(.+)$', re.IGNORECASE)
        self.attribute_pattern = re.compile(r'^@(\w+)\s+(.+)$')
    
    def parse_file(self, file_path: str) -> ATCTestSuite:
        """Parse an ATC file and return a test suite
        
        Args:
            file_path: Path to .atc file
            
        Returns:
            ATCTestSuite object containing all scenarios
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"ATC file not found: {file_path}")
        
        content = path.read_text()
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> ATCTestSuite:
        """Parse ATC content from string
        
        Args:
            content: ATC file content as string
            
        Returns:
            ATCTestSuite object
        """
        lines = content.split('\n')
        
        suite_name = None
        suite_description = ""
        config = {}
        scenarios = []
        
        current_scenario_name = None
        current_scenario_tags = []
        current_scenario_steps = []
        current_scenario_attributes = {}
        
        for line in lines:
            line = line.rstrip()
            
            # Skip empty lines at the start
            if not line and not suite_name:
                continue
            
            # Parse suite name (# Title)
            if match := self.suite_name_pattern.match(line):
                if not suite_name:  # Only take the first one
                    suite_name = match.group(1).strip()
                continue
            
            # Parse description
            if match := self.description_pattern.match(line):
                suite_description = match.group(1).strip()
                continue
            
            # Parse config (@config key=value)
            if match := self.config_pattern.match(line):
                key = match.group(1).strip()
                value = match.group(2).strip().strip('"\'')
                # Convert boolean strings
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                config[key] = value
                continue
            
            # Parse tags (@tag name)
            if match := self.tag_pattern.match(line):
                current_scenario_tags.append(match.group(1).strip())
                continue

            # Parse scenario attributes (@id, @reference, etc.)
            if current_scenario_name:
                if match := self.attribute_pattern.match(line):
                    key = match.group(1).strip().lower()
                    value = match.group(2).strip().strip('"\'')
                    if key not in ("tag", "config"):
                        current_scenario_attributes[key] = value
                        continue
            
            # Parse scenario header (## Scenario: Name)
            if match := self.scenario_pattern.match(line):
                # Save previous scenario if exists
                if current_scenario_name:
                    steps_text = '\n'.join(current_scenario_steps).strip()
                    if steps_text:
                        scenarios.append(ATCScenario(
                            name=current_scenario_name,
                            steps=steps_text,
                            tags=current_scenario_tags,
                            attributes=current_scenario_attributes
                        ))
                
                # Start new scenario
                current_scenario_name = match.group(1).strip()
                current_scenario_tags = []
                current_scenario_steps = []
                current_scenario_attributes = {}
                continue
            
            # Add line to current scenario steps
            if current_scenario_name:
                # Skip empty lines at the start of scenario
                if not line and not current_scenario_steps:
                    continue
                current_scenario_steps.append(line)
        
        # Save last scenario
        if current_scenario_name:
            steps_text = '\n'.join(current_scenario_steps).strip()
            if steps_text:
                scenarios.append(ATCScenario(
                    name=current_scenario_name,
                    steps=steps_text,
                    tags=current_scenario_tags,
                    attributes=current_scenario_attributes
                ))
        
        # Use filename as suite name if not specified
        if not suite_name:
            suite_name = "Unnamed Test Suite"
        
        return ATCTestSuite(
            name=suite_name,
            description=suite_description,
            config=config,
            scenarios=scenarios
        )
    
    def validate(self, test_suite: ATCTestSuite) -> List[str]:
        """Validate a test suite and return list of warnings/errors
        
        Args:
            test_suite: ATCTestSuite to validate
            
        Returns:
            List of warning/error messages (empty if valid)
        """
        issues = []
        
        if not test_suite.scenarios:
            issues.append("Warning: No test scenarios defined")
        
        for i, scenario in enumerate(test_suite.scenarios, 1):
            if not scenario.id:
                issues.append(f"Scenario {i} '{scenario.name}': Missing id")

            if not scenario.reference:
                issues.append(f"Scenario {i} '{scenario.name}': Missing reference")

            if not scenario.steps:
                issues.append(f"Scenario {i} '{scenario.name}': No steps defined")
            
            if len(scenario.steps.split('\n')) < 1:
                issues.append(f"Scenario {i} '{scenario.name}': Too few steps (at least 1 required)")
        
        return issues
