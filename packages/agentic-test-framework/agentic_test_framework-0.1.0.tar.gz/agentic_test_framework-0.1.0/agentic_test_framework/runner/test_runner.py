from typing import List
from datetime import datetime
from pathlib import Path
from ..parser import OpenAIParser
from ..executor import PlaywrightExecutor
from ..actions import Action, ActionResult
from ..reporter import HTMLReporter


class AgenticTestRunner:
    """Orchestrates the complete test execution flow"""
    
    def __init__(
        self,
        openai_api_key: str = None,
        browser_type: str = "chromium",
        headless: bool = False,
        generate_report: bool = True,
        screenshot_all_steps: bool = True,
        enable_playwright_trace: bool = True
    ):
        self.parser = OpenAIParser(api_key=openai_api_key)
        self.browser_type = browser_type
        self.headless = headless
        self.generate_report = generate_report
        self.screenshot_all_steps = screenshot_all_steps
        self.enable_playwright_trace = enable_playwright_trace
        self.reporter = HTMLReporter() if generate_report else None
    
    def run(self, test_description: str) -> List[ActionResult]:
        """
        Run a complete test from natural language description.
        
        Args:
            test_description: Natural language test description
            
        Returns:
            List of ActionResult objects for each executed action
        """
        # Create timestamped run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(f"test-results/run_{timestamp}")
        run_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        start_time = datetime.now()
        
        print(f"Test Description: {test_description}")
        print(f"{'='*60}\n")
        
        # Parse test description into actions
        print("🤖 Parsing test with OpenAI...")
        actions = self.parser.parse(test_description)
        
        if not actions:
            print("❌ No actions generated from test description")
            return []
        
        print(f"✅ Generated {len(actions)} actions:\n")
        for i, action in enumerate(actions, 1):
            print(f"  {i}. [{action.type}] {action.description}")
        print()
        
        # Execute actions with Playwright
        results = []
        trace_path = None
        with PlaywrightExecutor(
            browser_type=self.browser_type, 
            headless=self.headless,
            screenshot_dir=str(run_dir / "screenshots"),
            screenshot_all_steps=self.screenshot_all_steps,
            enable_trace=self.enable_playwright_trace,
            trace_dir=str(run_dir / "traces")
        ) as executor:
            print("🌐 Starting browser execution...\n")
            trace_path = executor.trace_path
            
            for i, action in enumerate(actions, 1):
                print(f"Executing step {i}/{len(actions)}: {action.description}")
                result = executor.execute(action)
                results.append(result)
                
                if result.success:
                    print(f"  ✅ {result.message}")
                    if result.screenshot_path:
                        print(f"  📸 Screenshot: {result.screenshot_path}")
                    if result.extracted_data:
                        print(f"  📊 Data: {result.extracted_data}")
                else:
                    print(f"  ❌ {result.message}")
                    if result.error:
                        print(f"  Error: {result.error}")
                    if result.screenshot_path:
                        print(f"  📸 Screenshot: {result.screenshot_path}")
                print()
        
        # Summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        end_time = datetime.now()
        
        print(f"{'='*60}")
        print(f"Test Complete: {successful} passed, {failed} failed")
        print(f"{'='*60}\n")
        
        # Generate HTML report
        if self.generate_report and self.reporter:
            report_path = self.reporter.generate_report(
                test_description=test_description,
                results=results,
                start_time=start_time,
                end_time=end_time,
                output_dir=str(run_dir)
            )
            print(f"📄 HTML Report: {report_path}\n")
        
        # Show Playwright artifacts
        if self.enable_playwright_trace and trace_path:
            print(f"🎬 Playwright Trace: {trace_path}")
            print(f"   View with: playwright show-trace {trace_path}\n")
        
        # Show run directory
        print(f"📁 Test artifacts: {run_dir}\n")
        print(f"{'='*60}\n")
        
        return results
