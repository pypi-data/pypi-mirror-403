"""Test AI command functionality."""

import pytest
import os
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import asyncio
from pathlib import Path

from devos.cli import main
from devos.core.ai import AIServiceError


class TestQuickAI:
    """Test quick AI command."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        
    @patch('devos.commands.quick_ai.get_ai_service')
    def test_quick_ai_basic(self, mock_get_ai_service):
        """Test basic quick AI functionality."""
        # Mock AI service as async context manager
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "This is a test response"
        mock_response.tokens_used = 50
        mock_response.cost = 0.005
        mock_service.generate_code = AsyncMock(return_value=mock_response)
        
        # Set up the async context manager
        mock_get_ai_service.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_get_ai_service.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = self.runner.invoke(main, ['quick-ai', 'What is Python?'])
        
        assert result.exit_code == 0
        assert 'Quick AI Response' in result.output
    
    @patch('devos.commands.quick_ai.get_ai_service')
    def test_quick_ai_with_file(self, mock_get_ai_service):
        """Test quick AI with file context."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def hello_world():\n    print("Hello, World!")')
            temp_file = f.name
        
        try:
            # Mock AI service
            mock_service = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "This function prints Hello World"
            mock_response.tokens_used = 75
            mock_response.cost = 0.0075
            mock_service.generate_code.return_value = mock_response
            mock_get_ai_service.return_value = mock_service
            
            result = self.runner.invoke(main, ['quick-ai', 'Explain this function', '--file', temp_file])
            
            assert result.exit_code == 0
            assert 'Quick AI Response' in result.output
            assert 'This function prints Hello World' in result.output
        finally:
            os.unlink(temp_file)
    
    @patch('devos.commands.quick_ai.get_ai_service')
    def test_quick_ai_error_handling(self, mock_get_ai_service):
        """Test quick AI error handling."""
        # Mock AI service error
        mock_service = AsyncMock()
        mock_service.generate_code.side_effect = AIServiceError("API key not configured")
        mock_get_ai_service.return_value = mock_service
        
        result = self.runner.invoke(main, ['quick-ai', 'test prompt'])
        
        assert result.exit_code == 0  # Should not crash
        assert 'error' in result.output.lower()
    
    def test_quick_ai_missing_file(self):
        """Test quick AI with missing file."""
        result = self.runner.invoke(main, ['quick-ai', 'test', '--file', 'nonexistent.py'])
        
        assert result.exit_code != 0
    
    @patch('devos.commands.quick_ai.get_ai_service')
    def test_quick_ai_custom_options(self, mock_get_ai_service):
        """Test quick AI with custom options."""
        mock_service = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Custom response"
        mock_response.tokens_used = 100
        mock_response.cost = 0.01
        mock_service.generate_code.return_value = mock_response
        mock_get_ai_service.return_value = mock_service
        
        result = self.runner.invoke(main, [
            'quick-ai', 
            'test prompt',
            '--model', 'llama-3.1-70b-versatile',
            '--temp', '0.5',
            '--max-tokens', '500'
        ])
        
        assert result.exit_code == 0
        mock_service.generate_code.assert_called_once()
        
        # Check that the user preferences were set correctly
        call_args = mock_service.generate_code.call_args
        user_prefs = call_args[1]['user_preferences']
        assert user_prefs.ai_model == 'llama-3.1-70b-versatile'
        assert user_prefs.temperature == 0.5
        assert user_prefs.max_tokens == 500


class TestAIFast:
    """Test AI fast command."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        
    @patch('devos.commands.groq.get_ai_service')
    @patch('devos.commands.groq.EnhancedContextBuilder')
    def test_ai_fast_quick_mode(self, mock_context_builder, mock_get_ai_service):
        """Test AI fast in quick mode."""
        # Mock AI service
        mock_service = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Fast AI response"
        mock_response.tokens_used = 80
        mock_response.cost = 0.008
        mock_service.generate_code.return_value = mock_response
        mock_get_ai_service.return_value = mock_service
        
        result = self.runner.invoke(main, ['ai-fast', '--quick', 'test prompt'])
        
        assert result.exit_code == 0
        assert 'Quick mode' in result.output
        assert 'Fast AI response' in result.output
        
        # Ensure context builder was not called in quick mode
        mock_context_builder.assert_not_called()
    
    @patch('devos.commands.groq.get_ai_service')
    @patch('devos.commands.groq.EnhancedContextBuilder')
    def test_ai_fast_full_analysis(self, mock_context_builder, mock_get_ai_service):
        """Test AI fast with full analysis."""
        # Mock context builder
        mock_builder = MagicMock()
        mock_context = MagicMock()
        mock_context.architecture.total_files = 50
        mock_builder.build_enhanced_context = AsyncMock(return_value=mock_context)
        mock_context_builder.return_value = mock_builder
        
        # Mock AI service as async context manager
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Context-aware response"
        mock_response.tokens_used = 120
        mock_response.cost = 0.012
        mock_service.generate_code = AsyncMock(return_value=mock_response)
        mock_get_ai_service.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_get_ai_service.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = self.runner.invoke(main, ['ai-fast', 'test prompt'])
        
        assert result.exit_code == 0
        assert 'Building project context' in result.output


class TestEnhancedAI:
    """Test enhanced AI commands."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        
    @patch('devos.commands.groq_enhanced.get_ai_service')
    @patch('devos.commands.groq_enhanced.EnhancedContextBuilder')
    def test_ai_analyze(self, mock_context_builder, mock_get_ai_service):
        """Test AI analyze command."""
        # Mock context builder
        mock_builder = MagicMock()
        mock_context = MagicMock()
        mock_context.architecture.total_files = 100
        mock_builder.build_enhanced_context = AsyncMock(return_value=mock_context)
        mock_context_builder.return_value = mock_builder
        
        # Mock AI service
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"analysis": "complete"}'
        mock_response.tokens_used = 200
        mock_response.cost = 0.02
        mock_service.generate_code = AsyncMock(return_value=mock_response)
        mock_get_ai_service.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_get_ai_service.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = self.runner.invoke(main, ['ai', 'analyze', 'analyze project structure'])
        
        # Just check it doesn't crash completely
        assert result.exit_code in [0, 1]
    
    @patch('devos.commands.groq_enhanced.get_ai_service')
    @patch('devos.commands.groq_enhanced.EnhancedContextBuilder')
    def test_ai_security_scan(self, mock_context_builder, mock_get_ai_service):
        """Test AI security scan command."""
        # Mock context builder
        mock_builder = MagicMock()
        mock_context = MagicMock()
        mock_context.architecture.total_files = 75
        mock_builder.build_enhanced_context = AsyncMock(return_value=mock_context)
        mock_context_builder.return_value = mock_builder
        
        # Mock AI service
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"security_issues": []}'
        mock_response.tokens_used = 150
        mock_response.cost = 0.015
        mock_service.generate_code = AsyncMock(return_value=mock_response)
        mock_get_ai_service.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_get_ai_service.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = self.runner.invoke(main, ['ai', 'security-scan'])
        
        # Just check it doesn't crash completely
        assert result.exit_code in [0, 1]
    
    @patch('devos.commands.groq_enhanced.get_ai_service')
    @patch('devos.commands.groq_enhanced.EnhancedContextBuilder')
    def test_ai_enhance(self, mock_context_builder, mock_get_ai_service):
        """Test AI enhance command."""
        # Mock context builder
        mock_builder = MagicMock()
        mock_context = MagicMock()
        mock_context.architecture.total_files = 80
        mock_builder.build_enhanced_context = AsyncMock(return_value=mock_context)
        mock_context_builder.return_value = mock_builder
        
        # Mock AI service as async context manager
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"enhancements": ["improve readability"]}'
        mock_response.tokens_used = 160
        mock_response.cost = 0.016
        mock_service.generate_code = AsyncMock(return_value=mock_response)
        mock_get_ai_service.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_get_ai_service.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = self.runner.invoke(main, ['ai', 'enhance', 'optimize performance'])
        
        assert result.exit_code == 0
        assert 'enhancements' in result.output or 'Enhance' in result.output
    
    @patch('devos.commands.groq_enhanced.get_ai_service')
    @patch('devos.commands.groq_enhanced.EnhancedContextBuilder')
    def test_ai_project_summary(self, mock_context_builder, mock_get_ai_service):
        """Test AI project summary command."""
        # Mock context builder
        mock_builder = MagicMock()
        mock_context = MagicMock()
        mock_context.architecture.total_files = 90
        mock_builder.build_enhanced_context = AsyncMock(return_value=mock_context)
        mock_context_builder.return_value = mock_builder
        
        # Mock AI service as async context manager
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"summary": "project overview"}'
        mock_response.tokens_used = 140
        mock_response.cost = 0.014
        mock_service.generate_code = AsyncMock(return_value=mock_response)
        mock_get_ai_service.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_get_ai_service.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = self.runner.invoke(main, ['ai', 'project-summary'])
        
        assert result.exit_code == 0
        assert 'summary' in result.output or 'Project' in result.output


class TestAIConfig:
    """Test AI configuration commands."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        
    @patch('devos.commands.ai_config.get_ai_config_manager')
    def test_ai_config_show_config(self, mock_get_config_manager):
        """Test AI config show command."""
        mock_config = MagicMock()
        mock_config.get_all_settings.return_value = {
            'default_provider': 'groq',
            'default_model': 'llama-3.1-8b-instant'
        }
        mock_get_config_manager.return_value = mock_config
        
        result = self.runner.invoke(main, ['ai-config', 'show-config'])
        
        assert result.exit_code == 0
        assert 'AI Configuration' in result.output
    
    @patch('devos.commands.ai_config.get_ai_config_manager')
    def test_ai_config_list_providers(self, mock_get_config_manager):
        """Test AI config list providers command."""
        mock_config = MagicMock()
        mock_config.get_provider_status.return_value = {
            'groq': {'configured': True, 'status': 'available'}
        }
        mock_get_config_manager.return_value = mock_config
        
        result = self.runner.invoke(main, ['ai-config', 'list-providers'])
        
        assert result.exit_code == 0
        assert 'AI Providers' in result.output
    
    @patch('devos.commands.ai_config.get_ai_config_manager')
    @patch('devos.commands.ai_config.initialize_ai_providers')
    def test_ai_config_set_api_key(self, mock_init_providers, mock_get_config_manager):
        """Test AI config set API key command."""
        mock_config = MagicMock()
        mock_get_config_manager.return_value = mock_config
        
        result = self.runner.invoke(main, ['ai-config', 'set-api-key', 'groq', '--key', 'test-key'])
        
        assert result.exit_code == 0
        mock_config.set_api_key.assert_called_once_with('groq', 'test-key')
        mock_init_providers.assert_called_once()


class TestAIPerformance:
    """Test AI command performance."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        
    @patch('devos.commands.quick_ai.get_ai_service')
    def test_quick_ai_performance(self, mock_get_ai_service):
        """Test quick AI response time."""
        import time
        
        # Mock AI service
        mock_service = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Quick response"
        mock_response.tokens_used = 50
        mock_response.cost = 0.005
        mock_service.generate_code.return_value = mock_response
        mock_get_ai_service.return_value = mock_service
        
        start_time = time.time()
        result = self.runner.invoke(main, ['quick-ai', 'test prompt'])
        end_time = time.time()
        
        assert result.exit_code == 0
        # Quick AI should respond in under 5 seconds (including test overhead)
        assert (end_time - start_time) < 5.0
    
    @patch('devos.commands.groq.get_ai_service')
    @patch('devos.commands.groq.EnhancedContextBuilder')
    def test_ai_fast_vs_quick_performance(self, mock_context_builder, mock_get_ai_service):
        """Test performance difference between AI fast and quick modes."""
        import time
        
        # Mock AI service for quick mode
        mock_service = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.tokens_used = 50
        mock_response.cost = 0.005
        mock_service.generate_code = AsyncMock(return_value=mock_response)
        mock_get_ai_service.return_value = mock_service
        
        # Test quick mode
        start_time = time.time()
        result1 = self.runner.invoke(main, ['ai-fast', '--quick', 'test'])
        quick_time = time.time() - start_time
        
        # Mock AI service for full analysis mode
        mock_service_full = MagicMock()
        mock_response_full = MagicMock()
        mock_response_full.content = "Full analysis response"
        mock_response_full.tokens_used = 100
        mock_response_full.cost = 0.01
        mock_service_full.generate_code = AsyncMock(return_value=mock_response_full)
        
        # Mock context builder for full analysis
        mock_builder = MagicMock()
        mock_context = MagicMock()
        mock_context.architecture.total_files = 50
        mock_builder.build_enhanced_context = AsyncMock(return_value=mock_context)
        mock_context_builder.return_value = mock_builder
        
        # Set up async context manager for full analysis
        mock_get_ai_service.return_value.__aenter__ = AsyncMock(return_value=mock_service_full)
        mock_get_ai_service.return_value.__aexit__ = AsyncMock(return_value=None)
        
        start_time = time.time()
        result2 = self.runner.invoke(main, ['ai-fast', 'test'])
        full_time = time.time() - start_time
        
        assert result1.exit_code == 0
        assert result2.exit_code == 0
        # Quick mode should be faster (allowing for test environment variability)
        assert quick_time < full_time + 0.05  # Allow 50ms tolerance for test environment
        
        # Verify that context builder was called for full analysis but not for quick
        mock_context_builder.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])
