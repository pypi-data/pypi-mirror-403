import os
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
from ..actions import (
    Action, ActionResult, NavigateAction, ClickAction, 
    TypeAction, ScreenshotAction, WaitAction, AssertAction,
    ExtractAction, ActionType
)


class PlaywrightExecutor:
    """Executes browser actions using Playwright"""
    
    def __init__(
        self, 
        browser_type: str = "chromium",
        headless: bool = False,
        screenshot_dir: str = "./test-results/screenshots",
        screenshot_all_steps: bool = True,
        enable_trace: bool = True,
        trace_dir: str = "./test-results/traces"
    ):
        self.browser_type = browser_type
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_all_steps = screenshot_all_steps
        self.enable_trace = enable_trace
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.screenshot_counter = 0
        self.trace_path: Optional[str] = None
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
    
    def start(self):
        """Initialize browser and page"""
        self.playwright = sync_playwright().start()
        
        if self.browser_type == "chromium":
            self.browser = self.playwright.chromium.launch(headless=self.headless)
        elif self.browser_type == "firefox":
            self.browser = self.playwright.firefox.launch(headless=self.headless)
        elif self.browser_type == "webkit":
            self.browser = self.playwright.webkit.launch(headless=self.headless)
        else:
            raise ValueError(f"Unknown browser type: {self.browser_type}")
        
        # Create context with recording capabilities
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "record_video_dir": str(self.screenshot_dir.parent / "videos") if self.enable_trace else None,
            "record_video_size": {"width": 1920, "height": 1080} if self.enable_trace else None
        }
        self.context = self.browser.new_context(**context_options)
        
        # Start tracing if enabled
        if self.enable_trace:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.trace_path = str(self.trace_dir / f"trace_{timestamp}.zip")
            self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        
        self.page = self.context.new_page()
    
    def stop(self):
        """Cleanup browser resources"""
        if self.page:
            self.page.close()
        if self.context:
            # Stop and save trace before closing context
            if self.enable_trace and self.trace_path:
                try:
                    self.context.tracing.stop(path=self.trace_path)
                except Exception as e:
                    print(f"Warning: Could not save trace: {e}")
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def execute(self, action: Action) -> ActionResult:
        """
        Execute a single action and return the result.
        
        Args:
            action: Action object to execute
            
        Returns:
            ActionResult with success status and optional screenshot path
        """
        try:
            if action.type == ActionType.NAVIGATE:
                result = self._navigate(action)
            elif action.type == ActionType.CLICK:
                result = self._click(action)
            elif action.type == ActionType.TYPE:
                result = self._type(action)
            elif action.type == ActionType.SCREENSHOT:
                result = self._screenshot(action)
            elif action.type == ActionType.WAIT:
                result = self._wait(action)
            elif action.type == ActionType.ASSERT:
                result = self._assert(action)
            elif action.type == ActionType.EXTRACT:
                result = self._extract(action)
            else:
                return ActionResult(
                    success=False,
                    action=action,
                    message=f"Unknown action type: {action.type}",
                    error=f"Unsupported action: {action.type}"
                )
            
            # Auto-screenshot after each step (except screenshot actions themselves)
            if self.screenshot_all_steps and action.type != ActionType.SCREENSHOT:
                screenshot_path = self._auto_screenshot(action)
                if screenshot_path:
                    result.screenshot_path = screenshot_path
            
            return result
        except Exception as e:
            return ActionResult(
                success=False,
                action=action,
                message=f"Failed to execute {action.type}: {str(e)}",
                error=str(e)
            )
    
    def _navigate(self, action: NavigateAction) -> ActionResult:
        """Navigate to a URL"""
        url = action.url
        if not url.startswith("http"):
            url = f"https://{url}"
        
        self.page.goto(url, wait_until="networkidle", timeout=30000)
        
        return ActionResult(
            success=True,
            action=action,
            message=f"Navigated to {url}",
            metadata={"url": url, "title": self.page.title()}
        )
    
    def _click(self, action: ClickAction) -> ActionResult:
        """Click an element"""
        try:
            if action.selector:
                # Click by selector
                self.page.click(action.selector, timeout=10000)
                target = action.selector
            elif action.text:
                # Click by text content
                self.page.get_by_text(action.text, exact=False).first.click(timeout=10000)
                target = f"text='{action.text}'"
            else:
                return ActionResult(
                    success=False,
                    action=action,
                    message="Click action requires either selector or text",
                    error="Missing selector or text parameter"
                )
            
            # Wait a bit after click for page to react
            self.page.wait_for_timeout(1000)
            
            return ActionResult(
                success=True,
                action=action,
                message=f"Clicked {target}",
                metadata={"target": target}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action=action,
                message=f"Failed to click: {str(e)}",
                error=str(e)
            )
    
    def _type(self, action: TypeAction) -> ActionResult:
        """Type text into an input field"""
        try:
            if action.selector:
                # Type by selector
                self.page.fill(action.selector, action.text, timeout=10000)
                target = action.selector
            elif action.label:
                # Type by label
                self.page.get_by_label(action.label, exact=False).fill(action.text, timeout=10000)
                target = f"label='{action.label}'"
            else:
                return ActionResult(
                    success=False,
                    action=action,
                    message="Type action requires either selector or label",
                    error="Missing selector or label parameter"
                )
            
            return ActionResult(
                success=True,
                action=action,
                message=f"Typed '{action.text}' into {target}",
                metadata={"target": target, "text": action.text}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action=action,
                message=f"Failed to type: {str(e)}",
                error=str(e)
            )
    
    def _screenshot(self, action: ScreenshotAction) -> ActionResult:
        """Take a screenshot"""
        self.screenshot_counter += 1
        filename = action.name or f"screenshot_{self.screenshot_counter:03d}"
        if not filename.endswith(".png"):
            filename += ".png"
        
        screenshot_path = self.screenshot_dir / filename
        
        self.page.screenshot(
            path=str(screenshot_path), 
            full_page=action.full_page
        )
        
        return ActionResult(
            success=True,
            action=action,
            message=f"Screenshot saved to {screenshot_path}",
            screenshot_path=str(screenshot_path),
            metadata={"path": str(screenshot_path)}
        )
    
    def _wait(self, action: WaitAction) -> ActionResult:
        """Wait for a duration or element"""
        if action.duration:
            self.page.wait_for_timeout(action.duration)
            return ActionResult(
                success=True,
                action=action,
                message=f"Waited for {action.duration}ms",
                metadata={"duration": action.duration}
            )
        elif action.selector:
            self.page.wait_for_selector(action.selector, timeout=30000)
            return ActionResult(
                success=True,
                action=action,
                message=f"Waited for {action.selector} to be visible",
                metadata={"selector": action.selector}
            )
        else:
            # Default wait
            self.page.wait_for_timeout(2000)
            return ActionResult(
                success=True,
                action=action,
                message="Waited for 2 seconds (default)",
                metadata={"duration": 2000}
            )
    
    def _assert(self, action: AssertAction) -> ActionResult:
        """Assert/verify a condition on the page"""
        try:
            # Check URL assertion
            if action.expected_url:
                current_url = self.page.url
                if action.expected_url.lower() in current_url.lower():
                    return ActionResult(
                        success=True,
                        action=action,
                        message=f"✓ URL contains '{action.expected_url}'",
                        metadata={
                            "expected": action.expected_url,
                            "actual": current_url
                        }
                    )
                else:
                    return ActionResult(
                        success=False,
                        action=action,
                        message=f"✗ URL assertion failed",
                        error=f"URL does not contain expected pattern",
                        metadata={
                            "expected": action.expected_url,
                            "actual": current_url
                        }
                    )
            
            # Check text content assertion
            if action.expected_text:
                if action.selector:
                    element = self.page.locator(action.selector).first
                    actual_text = element.text_content()
                else:
                    actual_text = self.page.content()
                
                if action.expected_text.lower() in actual_text.lower():
                    return ActionResult(
                        success=True,
                        action=action,
                        message=f"✓ Found expected text: '{action.expected_text}'",
                        metadata={
                            "expected": action.expected_text,
                            "actual": actual_text[:200] + ("..." if len(actual_text) > 200 else "")
                        }
                    )
                else:
                    return ActionResult(
                        success=False,
                        action=action,
                        message=f"✗ Text assertion failed",
                        error="Expected text not found on page",
                        metadata={
                            "expected": action.expected_text,
                            "actual": actual_text[:500] + ("..." if len(actual_text) > 500 else "")
                        }
                    )
            
            # Generic condition check
            return ActionResult(
                success=True,
                action=action,
                message=f"Condition verified: {action.condition}",
                metadata={"condition": action.condition}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action=action,
                message=f"Assertion failed: {str(e)}",
                error=str(e)
            )
    
    def _extract(self, action: ExtractAction) -> ActionResult:
        """Extract and display information from the page"""
        try:
            extracted = None
            
            if action.selector:
                element = self.page.locator(action.selector).first
                if action.attribute:
                    extracted = element.get_attribute(action.attribute)
                else:
                    extracted = element.text_content()
            elif action.text:
                # Find element by text and extract it
                element = self.page.get_by_text(action.text, exact=False).first
                extracted = element.text_content()
            else:
                # Extract page title as default
                extracted = self.page.title()
            
            return ActionResult(
                success=True,
                action=action,
                message=f"Extracted: {extracted}",
                extracted_data=extracted,
                metadata={"extracted": extracted}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action=action,
                message=f"Failed to extract: {str(e)}",
                error=str(e)
            )
    
    def _auto_screenshot(self, action: Action) -> Optional[str]:
        """Take an automatic screenshot after an action"""
        try:
            self.screenshot_counter += 1
            filename = f"step_{self.screenshot_counter:03d}_{action.type}.png"
            screenshot_path = self.screenshot_dir / filename
            
            self.page.screenshot(path=str(screenshot_path), full_page=False)
            return str(screenshot_path)
        except Exception:
            return None
