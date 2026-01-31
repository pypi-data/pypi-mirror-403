"""Tests for environment setup utilities"""

import pytest
from pathlib import Path
from agentic_test_framework.config import EnvSetup


class TestEnvSetup:
    """Test environment setup functionality"""
    
    def test_get_env_template(self):
        """Test getting env template content"""
        template = EnvSetup.get_env_template()
        
        assert "OPENAI_API_KEY=" in template
        assert "your-api-key-here" in template
        assert "https://platform.openai.com/api-keys" in template
        assert "OPENAI_MODEL=" in template
    
    def test_create_env_file(self, tmp_path):
        """Test creating .env file"""
        created, env_path = EnvSetup.create_env_file(project_dir=str(tmp_path))
        
        assert created is True
        assert Path(env_path).exists()
        
        content = Path(env_path).read_text()
        assert "OPENAI_API_KEY=" in content
    
    def test_create_env_file_exists_no_overwrite(self, tmp_path):
        """Test creating .env when it exists without overwrite"""
        env_path = tmp_path / ".env"
        env_path.write_text("existing content")
        
        created, path = EnvSetup.create_env_file(project_dir=str(tmp_path), overwrite=False)
        
        assert created is False
        assert env_path.read_text() == "existing content"
    
    def test_create_env_file_exists_with_overwrite(self, tmp_path):
        """Test creating .env when it exists with overwrite"""
        env_path = tmp_path / ".env"
        env_path.write_text("existing content")
        
        created, path = EnvSetup.create_env_file(project_dir=str(tmp_path), overwrite=True)
        
        assert created is True
        content = env_path.read_text()
        assert "OPENAI_API_KEY=" in content
        assert "existing content" not in content
    
    def test_check_env_not_exists(self, tmp_path):
        """Test checking non-existent .env file"""
        exists, configured = EnvSetup.check_env_configured(project_dir=str(tmp_path))
        
        assert exists is False
        assert configured is False
    
    def test_check_env_exists_not_configured(self, tmp_path):
        """Test checking .env with placeholder value"""
        env_path = tmp_path / ".env"
        env_path.write_text("OPENAI_API_KEY=your-api-key-here\n")
        
        exists, configured = EnvSetup.check_env_configured(project_dir=str(tmp_path))
        
        assert exists is True
        assert configured is False
    
    def test_check_env_exists_configured(self, tmp_path):
        """Test checking .env with actual API key"""
        env_path = tmp_path / ".env"
        env_path.write_text("OPENAI_API_KEY=sk-proj-abc123xyz789\n")
        
        exists, configured = EnvSetup.check_env_configured(project_dir=str(tmp_path))
        
        assert exists is True
        assert configured is True
    
    def test_check_env_empty_key(self, tmp_path):
        """Test checking .env with empty key"""
        env_path = tmp_path / ".env"
        env_path.write_text("OPENAI_API_KEY=\n")
        
        exists, configured = EnvSetup.check_env_configured(project_dir=str(tmp_path))
        
        assert exists is True
        assert configured is False
    
    def test_check_env_with_comments(self, tmp_path):
        """Test checking .env with comments and valid key"""
        env_path = tmp_path / ".env"
        env_path.write_text("""
# Configuration
OPENAI_API_KEY=sk-real-key-123
# Other settings
""")
        
        exists, configured = EnvSetup.check_env_configured(project_dir=str(tmp_path))
        
        assert exists is True
        assert configured is True
    
    def test_get_setup_instructions(self):
        """Test getting setup instructions"""
        instructions = EnvSetup.get_setup_instructions()
        
        assert "Setup Required" in instructions
        assert "platform.openai.com" in instructions
        assert ".env" in instructions
        assert "OPENAI_API_KEY" in instructions
    
    def test_create_env_file_default_dir(self, tmp_path, monkeypatch):
        """Test creating .env in current directory"""
        monkeypatch.chdir(tmp_path)
        
        created, env_path = EnvSetup.create_env_file()
        
        assert created is True
        assert Path(".env").exists()
        assert Path(env_path).parent == tmp_path
