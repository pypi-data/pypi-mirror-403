import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from ..actions import (
    Action, NavigateAction, ClickAction, TypeAction, 
    ScreenshotAction, WaitAction, AssertAction, ExtractAction, ActionType
)

load_dotenv()


class OpenAIParser:
    """Parses natural language test descriptions into structured actions using OpenAI"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.client = OpenAI(api_key=self.api_key)
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
    
    def parse(self, test_description: str) -> List[Action]:
        """
        Parse natural language test description into a list of actions.
        
        Args:
            test_description: Natural language description of the test
            
        Returns:
            List of Action objects to execute
        """
        system_prompt = self._get_system_prompt()
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": test_description}
            ],
            functions=[self._get_function_schema()],
            function_call={"name": "execute_test_actions"},
            temperature=0.1,  # Low temperature for deterministic outputs
        )
        
        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "execute_test_actions":
            import json
            args = json.loads(function_call.arguments)
            return self._convert_to_actions(args.get("actions", []))
        
        return []
    
    def _get_system_prompt(self) -> str:
        """System prompt for guiding the AI to generate test actions"""
        return """You are a test automation expert. Convert natural language test descriptions into structured browser actions.

Available actions:
- navigate: Go to a URL
- click: Click an element (use selector or text)
- type: Type text into a field (use selector or label)
- screenshot: Capture a screenshot
- wait: Wait for a duration or element
- assert: Verify/check a condition (e.g., URL, text content, page title)
- extract: Extract and display information from the page (e.g., version numbers, text content)

Guidelines:
- Use data-testid, ARIA labels, or visible text for selectors when possible
- Break complex interactions into atomic steps
- Add screenshots after important actions or before assertions
- Use 'extract' action when user wants to see/print/display information
- Use 'assert' action when user wants to verify/check/validate something
- Be explicit about what to click or type into
- Default to 2-second waits after navigation or clicks if timing is unclear"""
    
    def _get_function_schema(self) -> dict:
        """OpenAI function calling schema for test actions"""
        return {
            "name": "execute_test_actions",
            "description": "Execute a sequence of browser automation actions",
            "parameters": {
                "type": "object",
                "properties": {
                    "actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["navigate", "click", "type", "screenshot", "wait", "assert", "extract"],
                                    "description": "Type of action to perform"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Human-readable description of the action"
                                },
                                "url": {
                                    "type": "string",
                                    "description": "URL for navigate action"
                                },
                                "selector": {
                                    "type": "string",
                                    "description": "CSS selector for element"
                                },
                                "text": {
                                    "type": "string",
                                    "description": "Text to type or text content to find"
                                },
                                "label": {
                                    "type": "string",
                                    "description": "Label of input field for type action"
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Name for screenshot"
                                },
                                "duration": {
                                    "type": "integer",
                                    "description": "Wait duration in milliseconds"
                                },
                                "condition": {
                                    "type": "string",
                                    "description": "Condition to assert/verify"
                                },
                                "expected_text": {
                                    "type": "string",
                                    "description": "Expected text for assertion"
                                },
                                "expected_url": {
                                    "type": "string",
                                    "description": "Expected URL pattern for assertion"
                                },
                                "attribute": {
                                    "type": "string",
                                    "description": "Attribute name to extract (e.g., 'href', 'src')"
                                }
                            },
                            "required": ["type", "description"]
                        }
                    }
                },
                "required": ["actions"]
            }
        }
    
    def _convert_to_actions(self, raw_actions: List[dict]) -> List[Action]:
        """Convert raw JSON actions to typed Action objects"""
        actions = []
        
        for raw in raw_actions:
            action_type = raw.get("type")
            
            if action_type == ActionType.NAVIGATE:
                actions.append(NavigateAction(
                    description=raw["description"],
                    url=raw["url"]
                ))
            elif action_type == ActionType.CLICK:
                actions.append(ClickAction(
                    description=raw["description"],
                    selector=raw.get("selector"),
                    text=raw.get("text")
                ))
            elif action_type == ActionType.TYPE:
                actions.append(TypeAction(
                    description=raw["description"],
                    selector=raw.get("selector"),
                    text=raw["text"],
                    label=raw.get("label")
                ))
            elif action_type == ActionType.SCREENSHOT:
                actions.append(ScreenshotAction(
                    description=raw["description"],
                    name=raw.get("name")
                ))
            elif action_type == ActionType.WAIT:
                actions.append(WaitAction(
                    description=raw["description"],
                    duration=raw.get("duration"),
                    selector=raw.get("selector")
                ))
            elif action_type == ActionType.ASSERT:
                actions.append(AssertAction(
                    description=raw["description"],
                    condition=raw.get("condition", ""),
                    selector=raw.get("selector"),
                    expected_text=raw.get("expected_text"),
                    expected_url=raw.get("expected_url")
                ))
            elif action_type == ActionType.EXTRACT:
                actions.append(ExtractAction(
                    description=raw["description"],
                    selector=raw.get("selector"),
                    text=raw.get("text"),
                    attribute=raw.get("attribute")
                ))
        
        return actions
