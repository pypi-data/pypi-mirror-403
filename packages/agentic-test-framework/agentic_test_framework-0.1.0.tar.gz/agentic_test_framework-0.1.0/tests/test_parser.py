"""Tests for OpenAI parser"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agentic_test_framework.parser import OpenAIParser
from agentic_test_framework.actions import (
    NavigateAction,
    ClickAction,
    TypeAction,
    ScreenshotAction,
    ActionType
)


class TestOpenAIParser:
    """Test OpenAI parser functionality"""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance with mocked API key"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            return OpenAIParser(api_key='test-key')
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly"""
        assert parser.api_key == 'test-key'
        assert parser.model in ['gpt-4-turbo-preview', 'gpt-4']
        assert parser.client is not None
    
    def test_parser_requires_api_key(self):
        """Test parser raises error without API key"""
        from openai import OpenAIError
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(OpenAIError, match="api_key"):
                OpenAIParser(api_key=None)
    
    @patch('agentic_test_framework.parser.openai_parser.OpenAI')
    def test_parse_simple_navigation(self, mock_openai, parser):
        """Test parsing simple navigation command"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.function_call = Mock()
        mock_response.choices[0].message.function_call.name = "execute_test_actions"
        mock_response.choices[0].message.function_call.arguments = '''
        {
            "actions": [
                {
                    "type": "navigate",
                    "description": "Go to example.com",
                    "url": "https://example.com"
                }
            ]
        }
        '''
        
        parser.client.chat.completions.create = Mock(return_value=mock_response)
        
        actions = parser.parse("Go to example.com")
        
        assert len(actions) == 1
        assert isinstance(actions[0], NavigateAction)
        assert actions[0].url == "https://example.com"
    
    @patch('agentic_test_framework.parser.openai_parser.OpenAI')
    def test_parse_multi_step_test(self, mock_openai, parser):
        """Test parsing multi-step test scenario"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.function_call = Mock()
        mock_response.choices[0].message.function_call.name = "execute_test_actions"
        mock_response.choices[0].message.function_call.arguments = '''
        {
            "actions": [
                {
                    "type": "navigate",
                    "description": "Go to example.com",
                    "url": "https://example.com"
                },
                {
                    "type": "click",
                    "description": "Click login button",
                    "text": "Login"
                },
                {
                    "type": "screenshot",
                    "description": "Take screenshot",
                    "name": "login_page"
                }
            ]
        }
        '''
        
        parser.client.chat.completions.create = Mock(return_value=mock_response)
        
        actions = parser.parse("Go to example.com, click Login, take screenshot")
        
        assert len(actions) == 3
        assert isinstance(actions[0], NavigateAction)
        assert isinstance(actions[1], ClickAction)
        assert isinstance(actions[2], ScreenshotAction)
    
    def test_system_prompt_contains_actions(self, parser):
        """Test system prompt includes all action types"""
        prompt = parser._get_system_prompt()
        
        assert "navigate" in prompt
        assert "click" in prompt
        assert "type" in prompt
        assert "screenshot" in prompt
        assert "wait" in prompt
        assert "assert" in prompt
        assert "extract" in prompt
    
    def test_function_schema_has_required_fields(self, parser):
        """Test function schema includes all required fields"""
        schema = parser._get_function_schema()
        
        assert schema["name"] == "execute_test_actions"
        assert "parameters" in schema
        assert "actions" in schema["parameters"]["properties"]
        
        action_schema = schema["parameters"]["properties"]["actions"]["items"]["properties"]
        assert "type" in action_schema
        assert "description" in action_schema
        assert "url" in action_schema
        assert "selector" in action_schema
        assert "text" in action_schema
    
    def test_convert_navigate_action(self, parser):
        """Test converting raw navigate action"""
        raw_actions = [
            {
                "type": "navigate",
                "description": "Go to test site",
                "url": "https://test.com"
            }
        ]
        
        actions = parser._convert_to_actions(raw_actions)
        
        assert len(actions) == 1
        assert isinstance(actions[0], NavigateAction)
        assert actions[0].url == "https://test.com"
    
    def test_convert_type_action(self, parser):
        """Test converting raw type action"""
        raw_actions = [
            {
                "type": "type",
                "description": "Enter username",
                "selector": "#username",
                "text": "testuser"
            }
        ]
        
        actions = parser._convert_to_actions(raw_actions)
        
        assert len(actions) == 1
        assert isinstance(actions[0], TypeAction)
        assert actions[0].selector == "#username"
        assert actions[0].text == "testuser"
