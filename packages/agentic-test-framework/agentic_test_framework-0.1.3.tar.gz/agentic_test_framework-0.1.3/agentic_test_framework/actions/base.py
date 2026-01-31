from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ActionType(str, Enum):
    """Supported browser actions"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    SCROLL = "scroll"
    ASSERT = "assert"
    EXTRACT = "extract"


class Action(BaseModel):
    """Base action model for all browser operations"""
    type: ActionType
    description: str = Field(..., description="Human-readable description of the action")
    
    model_config = ConfigDict(use_enum_values=True)


class NavigateAction(Action):
    """Navigate to a URL"""
    type: ActionType = ActionType.NAVIGATE
    url: str = Field(..., description="URL to navigate to")


class ClickAction(Action):
    """Click an element on the page"""
    type: ActionType = ActionType.CLICK
    selector: Optional[str] = Field(None, description="CSS selector for the element")
    text: Optional[str] = Field(None, description="Text content to find and click")


class TypeAction(Action):
    """Type text into an input field"""
    type: ActionType = ActionType.TYPE
    selector: Optional[str] = Field(None, description="CSS selector for the input field")
    text: str = Field(..., description="Text to type")
    label: Optional[str] = Field(None, description="Label of the input field")


class ScreenshotAction(Action):
    """Take a screenshot of the page"""
    type: ActionType = ActionType.SCREENSHOT
    name: Optional[str] = Field(None, description="Optional name for the screenshot")
    full_page: bool = Field(True, description="Capture full page or just viewport")


class WaitAction(Action):
    """Wait for a condition or duration"""
    type: ActionType = ActionType.WAIT
    duration: Optional[int] = Field(None, description="Duration in milliseconds")
    selector: Optional[str] = Field(None, description="Wait for element to be visible")


class AssertAction(Action):
    """Assert/verify a condition on the page"""
    type: ActionType = ActionType.ASSERT
    condition: str = Field(..., description="What to verify (e.g., 'page title contains Python')")
    selector: Optional[str] = Field(None, description="Element selector to check")
    expected_text: Optional[str] = Field(None, description="Expected text content")
    expected_url: Optional[str] = Field(None, description="Expected URL pattern")


class ExtractAction(Action):
    """Extract and display information from the page"""
    type: ActionType = ActionType.EXTRACT
    selector: Optional[str] = Field(None, description="Element selector to extract from")
    text: Optional[str] = Field(None, description="Text pattern to find and extract")
    attribute: Optional[str] = Field(None, description="Attribute to extract (e.g., 'href', 'src')")


class ActionResult(BaseModel):
    """Result of executing an action"""
    success: bool
    action: Action
    message: str
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    extracted_data: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
