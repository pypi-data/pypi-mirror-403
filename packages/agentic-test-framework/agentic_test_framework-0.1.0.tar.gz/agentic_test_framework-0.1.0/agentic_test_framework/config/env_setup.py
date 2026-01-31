"""Environment setup and configuration utilities"""

from pathlib import Path
from typing import Optional


class EnvSetup:
    """Utilities for setting up .env configuration"""
    
    @staticmethod
    def get_env_template() -> str:
        """Get the .env file template content"""
        return """# Agentic Test Framework Configuration

# OpenAI API Configuration (Required)
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your-api-key-here

# Optional: Specify OpenAI model (default: gpt-4-turbo-preview)
# OPENAI_MODEL=gpt-4-turbo-preview
# OPENAI_MODEL=gpt-4
# OPENAI_MODEL=gpt-3.5-turbo

# Optional: OpenAI API base URL (for custom endpoints)
# OPENAI_API_BASE=https://api.openai.com/v1

# Optional: OpenAI organization ID
# OPENAI_ORG_ID=your-org-id

# Browser Configuration (Optional - can be overridden via CLI)
# BROWSER_TYPE=chromium
# HEADLESS=false

# Test Results Directory (Optional)
# TEST_RESULTS_DIR=./test-results

# Debugging (Optional)
# DEBUG=false
# VERBOSE=false
"""
    
    @staticmethod
    def create_env_file(
        project_dir: Optional[str] = None,
        overwrite: bool = False
    ) -> tuple[bool, str]:
        """Create .env file from template
        
        Args:
            project_dir: Directory where to create .env file (default: current directory)
            overwrite: Whether to overwrite existing .env file
            
        Returns:
            Tuple of (success: bool, path: str)
        """
        if project_dir is None:
            project_dir = Path.cwd()
        else:
            project_dir = Path(project_dir)
        
        env_path = project_dir / ".env"
        
        # Check if file exists
        if env_path.exists() and not overwrite:
            return False, str(env_path)
        
        # Write template
        content = EnvSetup.get_env_template()
        env_path.write_text(content)
        
        return True, str(env_path)
    
    @staticmethod
    def check_env_configured(project_dir: Optional[str] = None) -> tuple[bool, bool]:
        """Check if .env file exists and is configured
        
        Args:
            project_dir: Directory to check (default: current directory)
            
        Returns:
            Tuple of (exists: bool, configured: bool)
            configured is True if OPENAI_API_KEY is set and not a placeholder
        """
        if project_dir is None:
            project_dir = Path.cwd()
        else:
            project_dir = Path(project_dir)
        
        env_path = project_dir / ".env"
        
        if not env_path.exists():
            return False, False
        
        # Check if configured (not just placeholder)
        content = env_path.read_text()
        
        # Look for OPENAI_API_KEY line
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('OPENAI_API_KEY='):
                value = line.split('=', 1)[1].strip()
                # Check if it's not empty and not a placeholder
                if value and value not in ['your-api-key-here', 'sk-...', '']:
                    return True, True
        
        return True, False
    
    @staticmethod
    def get_setup_instructions() -> str:
        """Get instructions for setting up the .env file"""
        return """
╔═══════════════════════════════════════════════════════════════╗
║          🚀 Agentic Test Framework - Setup Required          ║
╚═══════════════════════════════════════════════════════════════╝

A .env file has been created, but you need to add your OpenAI API key.

📝 Steps to complete setup:

  1. Get your OpenAI API key:
     → Visit: https://platform.openai.com/api-keys
     → Create a new API key if you don't have one

  2. Edit the .env file:
     → Open: .env
     → Replace 'your-api-key-here' with your actual API key
     → Save the file

  3. Run your first test:
     → agentic-test "Go to example.com and take a screenshot"

Example .env configuration:
  OPENAI_API_KEY=sk-proj-abc123...your-key-here...xyz789

Need help? Check the documentation:
  → README.md
  → docs/CREATING_TESTS.md

"""
