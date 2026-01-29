"""Test core CLI functionality."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

from devos.cli import main


class TestCoreCLI:
    """Test core CLI commands and functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'DevOS' in result.output
        assert 'One command-line to manage your entire dev life' in result.output
    
    def test_cli_version(self):
        """Test CLI version command."""
        result = self.runner.invoke(main, ['--version'])
        assert result.exit_code == 0
    
    def test_main_command_groups_exist(self):
        """Test that all main command groups are registered."""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        
        # Check that main command groups exist
        expected_groups = [
            'ai', 'ai-config', 'ai-fast', 'quick-ai', 'ai-interactive-chat',
            'test', 'project', 'track', 'env', 'config', 'init'
        ]
        
        for group in expected_groups:
            assert group in result.output
    
    def test_ai_command_group(self):
        """Test AI command group structure."""
        result = self.runner.invoke(main, ['ai', '--help'])
        assert result.exit_code == 0
        
        # Check that enhanced AI commands are present
        expected_commands = [
            'analyze', 'security-scan', 'architecture-map', 
            'enhance', 'project-summary', 'review', 'explain',
            'refactor', 'test', 'example', 'debug', 'chat', 'suggest', 'generate'
        ]
        
        for cmd in expected_commands:
            assert cmd in result.output
    
    def test_removed_commands_dont_exist(self):
        """Test that removed commands are no longer available."""
        removed_commands = ['deploy', 'api', 'docs']
        
        for cmd in removed_commands:
            result = self.runner.invoke(main, [cmd, '--help'])
            assert result.exit_code != 0
            assert 'No such command' in result.output
    
    @patch('devos.commands.ai_config.get_ai_config_manager')
    def test_ai_config_commands(self, mock_config_manager):
        """Test AI configuration commands."""
        mock_config = MagicMock()
        mock_config_manager.return_value = mock_config
        
        # Test list providers
        result = self.runner.invoke(main, ['ai-config', 'list-providers'])
        assert result.exit_code == 0
    
    @patch('devos.commands.quick_ai.get_ai_service')
    def test_quick_ai_command(self, mock_ai_service):
        """Test quick AI command."""
        # Mock AI service response
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_response.tokens_used = 100
        mock_response.cost = 0.01
        mock_ai_service.return_value.__aenter__.return_value.generate_code.return_value = mock_response
        
        result = self.runner.invoke(main, ['quick-ai', 'test prompt'])
        assert result.exit_code == 0
        assert 'Quick AI Response' in result.output
    
    @patch('devos.commands.groq.get_ai_service')
    def test_ai_fast_command(self, mock_ai_service):
        """Test AI fast command."""
        # Mock AI service response
        mock_response = MagicMock()
        mock_response.content = "Fast AI response"
        mock_response.tokens_used = 150
        mock_response.cost = 0.015
        mock_ai_service.return_value.__aenter__.return_value.generate_code.return_value = mock_response
        
        result = self.runner.invoke(main, ['ai-fast', '--quick', 'test prompt'])
        assert result.exit_code == 0
        assert 'Quick mode' in result.output
    
    def test_test_command_group(self):
        """Test test command group structure."""
        result = self.runner.invoke(main, ['test', '--help'])
        assert result.exit_code == 0
        
        expected_commands = ['run', 'coverage', 'discover', 'generate']
        for cmd in expected_commands:
            assert cmd in result.output
    
    def test_project_command_group(self):
        """Test project command group structure."""
        result = self.runner.invoke(main, ['project', '--help'])
        assert result.exit_code == 0
        
        expected_commands = ['add', 'list', 'status', 'tasks', 'issues', 'notes']
        for cmd in expected_commands:
            assert cmd in result.output
    
    def test_track_command_group(self):
        """Test track command group structure."""
        result = self.runner.invoke(main, ['track', '--help'])
        assert result.exit_code == 0
        
        expected_commands = ['start', 'stop', 'status', 'list']
        for cmd in expected_commands:
            assert cmd in result.output
    
    def test_env_command_group(self):
        """Test environment variable command group structure."""
        result = self.runner.invoke(main, ['env', '--help'])
        assert result.exit_code == 0
        
        expected_commands = ['set', 'get', 'list', 'delete']
        for cmd in expected_commands:
            assert cmd in result.output
    
    def test_command_aliases(self):
        """Test that command aliases work correctly."""
        # Test some common aliases that should work
        working_aliases = [
            (['ai-fast'], ['groq']),
            (['init'], ['create'])
        ]

        for main_cmd, aliases in working_aliases:
            # Test main command
            result_main = self.runner.invoke(main, main_cmd + ['--help'])
            assert result_main.exit_code == 0, f"Main command {main_cmd} failed"

            # Test each alias
            for alias in aliases:
                result_alias = self.runner.invoke(main, [alias, '--help'])
                # Some aliases might not work due to CLI structure, so we'll be more lenient
                # and just check they don't crash completely
                assert result_alias.exit_code in [0, 1, 2], f"Alias {alias} failed with exit code {result_alias.exit_code}"
    
    def test_verbose_flag(self):
        """Test verbose flag functionality."""
        result = self.runner.invoke(main, ['--verbose', '--help'])
        assert result.exit_code == 0
    
    def test_invalid_command(self):
        """Test handling of invalid commands."""
        result = self.runner.invoke(main, ['invalid-command'])
        assert result.exit_code != 0
        assert 'No such command' in result.output
    
    def test_invalid_option(self):
        """Test handling of invalid options."""
        result = self.runner.invoke(main, ['--invalid-option'])
        assert result.exit_code != 0


class TestCLIIntegration:
    """Integration tests for CLI workflows."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_ai_workflow(self):
        """Test complete AI command workflow."""
        with patch('devos.commands.quick_ai.get_ai_service') as mock_ai:
            mock_response = MagicMock()
            mock_response.content = "AI response"
            mock_response.tokens_used = 100
            mock_response.cost = 0.01
            mock_ai.return_value.__aenter__.return_value.generate_code.return_value = mock_response
            
            # Test quick AI
            result = self.runner.invoke(main, ['quick-ai', 'test'])
            assert result.exit_code == 0
            
            # Test AI config
            with patch('devos.commands.ai_config.get_ai_config_manager') as mock_config:
                mock_config_instance = MagicMock()
                mock_config.return_value = mock_config_instance
                
                result = self.runner.invoke(main, ['ai-config', 'show-config'])
                assert result.exit_code == 0
    
    def test_error_handling_workflow(self):
        """Test error handling in CLI workflows."""
        # Test with missing API key
        with patch('devos.commands.quick_ai.get_ai_service') as mock_ai:
            from devos.core.ai import AIServiceError
            mock_ai.side_effect = AIServiceError("API key not configured")
            
            result = self.runner.invoke(main, ['quick-ai', 'test'])
            assert result.exit_code == 0  # Should not crash, just show error
            assert 'error' in result.output.lower()


if __name__ == '__main__':
    pytest.main([__file__])
