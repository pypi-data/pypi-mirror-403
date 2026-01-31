"""Main entry point for running tests from command line"""

import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from agentic_test_framework import AgenticTestRunner
from agentic_test_framework.parser import ATCParser, ATCTemplateGenerator
from agentic_test_framework.config import EnvSetup


def main():
    # Check if .env exists and create if needed
    env_exists, env_configured = EnvSetup.check_env_configured()
    
    if not env_exists:
        # Automatically create .env file
        created, env_path = EnvSetup.create_env_file()
        if created:
            print(EnvSetup.get_setup_instructions())
            sys.exit(0)
    
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Agentic Test Framework - Run browser tests from natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run natural language test
  agentic-test "Go to google.com and search for playwright"
  
    # Create ATC template file
    agentic-test --create tests/my_test.atc
    agentic-test --create tests/login.atc --template login
  
  # Setup environment
  agentic-test --setup
  
    # Run ATC file
    agentic-test tests/login.atc
    agentic-test tests/suite.atc --scenario "Successful login"
    agentic-test tests/suite.atc --tag smoke
        """
    )
    parser.add_argument(
        "test",
        type=str,
        nargs='?',
        help="Natural language test description or path to .atc file"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Create .env configuration file (interactive setup)"
    )
    parser.add_argument(
        "--create",
        metavar="FILE",
        help="Create a new ATC template file at the specified path"
    )
    parser.add_argument(
        "--template",
        choices=["basic", "login", "ecommerce", "api"],
        default="basic",
        help="Template type when creating ATC file (default: basic)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing file when using --create"
    )
    parser.add_argument(
        "--browser",
        type=str,
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser to use (default: chromium)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Disable HTML report generation"
    )
    parser.add_argument(
        "--no-step-screenshots",
        action="store_true",
        help="Disable automatic screenshots for each step"
    )
    parser.add_argument(
        "--no-trace",
        action="store_true",
        help="Disable Playwright trace recording"
    )
    parser.add_argument(
        "--scenario",
        help="Run specific scenario from ATC file (by name)"
    )
    parser.add_argument(
        "--tag",
        help="Run scenarios with specific tag from ATC file"
    )
    
    args = parser.parse_args()
    
    # Handle --setup flag
    if args.setup:
        env_exists, env_configured = EnvSetup.check_env_configured()
        
        if env_exists and env_configured:
            print("✅ Environment is already configured!")
            print("   .env file exists with OPENAI_API_KEY set")
            print("\nTo reconfigure, edit .env file or use --setup with --overwrite")
            sys.exit(0)
        
        if env_exists and not env_configured:
            print("⚠️  .env file exists but OPENAI_API_KEY is not configured")
            print("   Please edit .env and add your OpenAI API key")
            print("\n📝 Instructions:")
            print("   1. Get API key from: https://platform.openai.com/api-keys")
            print("   2. Edit .env file")
            print("   3. Set OPENAI_API_KEY=your-actual-key")
            sys.exit(0)
        
        # Create .env file
        created, env_path = EnvSetup.create_env_file()
        if created:
            print(EnvSetup.get_setup_instructions())
        sys.exit(0)
    
    # Handle --create flag
    if args.create:
        try:
            created = ATCTemplateGenerator.create_file(
                output_path=args.create,
                template_type=args.template,
                overwrite=args.overwrite
            )
            
            if created:
                if args.create.endswith('.atc'):
                    output_path = args.create
                else:
                    output_path = f"{args.create}.atc"
                print(f"✅ Created ATC template file: {output_path}")
                print(f"   Template type: {args.template}")
                print(f"\n📝 Edit the file to customize your test scenarios, then run:")
                print(f"   agentic-test {output_path}")
            else:
                print(f"❌ File already exists: {args.create}")
                print(f"   Use --overwrite to replace it")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error creating template: {e}")
            sys.exit(1)
        
        sys.exit(0)
    
    # Require test argument if not using --create or --setup
    if not args.test:
        parser.error("the following arguments are required: test (unless using --create or --setup)")
    
    # Check if OpenAI API key is configured before running tests
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY is not configured")
        print("\n🔧 Run setup to create .env file:")
        print("   agentic-test --setup")
        print("\nOr set the environment variable:")
        print("   export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    try:
        # Check if input is an ATC file
        test_input = args.test
        is_atc_file = test_input.endswith('.atc') and Path(test_input).exists()
        
        if is_atc_file:
            # Parse ATC file
            atc_parser = ATCParser()
            test_suite = atc_parser.parse_file(test_input)
            
            # Validate
            issues = atc_parser.validate(test_suite)
            if issues:
                print("⚠️  ATC Validation Warnings:")
                for issue in issues:
                    print(f"  - {issue}")
                print()
            
            # Filter scenarios
            scenarios_to_run = test_suite.scenarios
            
            if args.scenario:
                scenarios_to_run = [s for s in scenarios_to_run if s.name == args.scenario]
                if not scenarios_to_run:
                    print(f"❌ No scenario found with name: {args.scenario}")
                    print(f"Available scenarios: {', '.join(s.name for s in test_suite.scenarios)}")
                    sys.exit(1)
            
            if args.tag:
                scenarios_to_run = [s for s in scenarios_to_run if args.tag in s.tags]
                if not scenarios_to_run:
                    print(f"❌ No scenarios found with tag: {args.tag}")
                    sys.exit(1)
            
            # Use config from ATC file if not overridden by CLI
            browser = args.browser if args.browser != "chromium" else test_suite.config.get("browser", "chromium")
            headless = args.headless if args.headless else test_suite.config.get("headless", False)
            
            print(f"\n{'='*60}")
            print(f"📋 Test Suite: {test_suite.name}")
            if test_suite.description:
                print(f"   {test_suite.description}")
            print(f"{'='*60}\n")
            
            # Run each scenario
            all_results = []
            for scenario in scenarios_to_run:
                print(f"\n🎬 Running Scenario: {scenario.name}")
                if scenario.tags:
                    print(f"   Tags: {', '.join(scenario.tags)}")
                print()
                
                runner = AgenticTestRunner(
                    browser_type=browser,
                    headless=headless,
                    generate_report=not args.no_report,
                    screenshot_all_steps=not args.no_step_screenshots,
                    enable_playwright_trace=not args.no_trace
                )
                
                results = runner.run(scenario.steps)
                all_results.extend(results)
            
            # Exit with error code if any test failed
            failed_count = sum(1 for r in all_results if not r.success)
            sys.exit(1 if failed_count > 0 else 0)
            
        else:
            # Check if it's a plain text file
            if Path(test_input).exists():
                test_input = Path(test_input).read_text()
            
            # Run as natural language description
            runner = AgenticTestRunner(
                browser_type=args.browser,
                headless=args.headless,
                generate_report=not args.no_report,
                screenshot_all_steps=not args.no_step_screenshots,
                enable_playwright_trace=not args.no_trace
            )
            
            results = runner.run(test_input)
            
            # Exit with error code if any test failed
            failed_count = sum(1 for r in results if not r.success)
            sys.exit(1 if failed_count > 0 else 0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

