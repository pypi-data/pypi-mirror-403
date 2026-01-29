"""
Command History and Suggestions - Smart CLI Experience
Provides intelligent command suggestions, history, and auto-completion.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import click
from collections import defaultdict, Counter


@dataclass
class CommandRecord:
    """Record of a executed command."""
    command: str
    timestamp: datetime
    duration: float
    exit_code: int
    working_directory: str
    args: Dict[str, Any]
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'command': self.command,
            'timestamp': self.timestamp.isoformat(),
            'duration': self.duration,
            'exit_code': self.exit_code,
            'working_directory': self.working_directory,
            'args': self.args,
            'success': self.success
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandRecord':
        """Create from dictionary."""
        return cls(
            command=data['command'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            duration=data['duration'],
            exit_code=data['exit_code'],
            working_directory=data['working_directory'],
            args=data['args'],
            success=data['success']
        )


class CommandHistory:
    """Manages command history and analytics."""
    
    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or Path.home() / ".devos" / "command_history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history: List[CommandRecord] = []
        self.max_history = 1000
        self.load_history()
    
    def load_history(self):
        """Load command history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = [CommandRecord.from_dict(record) for record in data]
        except Exception as e:
            click.echo(f"⚠️  Failed to load command history: {e}")
            self.history = []
    
    def save_history(self):
        """Save command history to file."""
        try:
            # Keep only recent history
            recent_history = self.history[-self.max_history:]
            data = [record.to_dict() for record in recent_history]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            click.echo(f"⚠️  Failed to save command history: {e}")
    
    def add_command(self, command: str, duration: float, exit_code: int, 
                   working_directory: str, args: Dict[str, Any]):
        """Add a command to history."""
        record = CommandRecord(
            command=command,
            timestamp=datetime.now(),
            duration=duration,
            exit_code=exit_code,
            working_directory=working_directory,
            args=args,
            success=exit_code == 0
        )
        
        self.history.append(record)
        self.save_history()
    
    def get_recent_commands(self, limit: int = 10) -> List[CommandRecord]:
        """Get recent commands."""
        return self.history[-limit:]
    
    def get_frequent_commands(self, limit: int = 10, days: int = 30) -> List[Tuple[str, int]]:
        """Get most frequent commands."""
        cutoff = datetime.now() - timedelta(days=days)
        recent_commands = [r.command for r in self.history if r.timestamp > cutoff]
        
        counter = Counter(recent_commands)
        return counter.most_common(limit)
    
    def get_command_stats(self) -> Dict[str, Any]:
        """Get command usage statistics."""
        if not self.history:
            return {}
        
        total_commands = len(self.history)
        successful_commands = sum(1 for r in self.history if r.success)
        failed_commands = total_commands - successful_commands
        
        # Average duration
        durations = [r.duration for r in self.history if r.duration > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Most used commands
        command_counts = Counter(r.command for r in self.history)
        most_used = command_counts.most_common(5)
        
        # Commands by time of day
        hour_counts = defaultdict(int)
        for record in self.history:
            hour_counts[record.timestamp.hour] += 1
        
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 0
        
        return {
            'total_commands': total_commands,
            'successful_commands': successful_commands,
            'failed_commands': failed_commands,
            'success_rate': (successful_commands / total_commands * 100) if total_commands > 0 else 0,
            'average_duration': avg_duration,
            'most_used_commands': most_used,
            'peak_hour': peak_hour,
            'last_command': self.history[-1].timestamp if self.history else None
        }


class CommandSuggester:
    """Intelligent command suggestions based on context and history."""
    
    def __init__(self, command_history: CommandHistory):
        self.history = command_history
        self.command_patterns = {
            'ai_commands': [
                'groq', 'groq-analyze', 'groq-chat', 'groq-enhance', 
                'groq-security-scan', 'groq-architecture-map', 'groq-project-summary',
                'ai-review', 'ai-explain', 'ai-refactor', 'ai-chat'
            ],
            'project_commands': [
                'project-add', 'project-list', 'project-status', 'projects'
            ],
            'task_commands': [
                'now', 'done', 'status', 'today', 'recent'
            ],
            'deploy_commands': [
                'deploy', 'rollback', 'deploy-status', 'deploy-setup'
            ],
            'test_commands': [
                'test', 'coverage', 'test-generate'
            ],
            'docs_commands': [
                'docs-generate', 'docs-serve', 'docs-api', 'docs-readme'
            ]
        }
    
    def get_suggestions(self, partial_command: str = "", context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get intelligent command suggestions."""
        suggestions = []
        
        # If no partial command, suggest based on context
        if not partial_command:
            suggestions.extend(self._get_context_suggestions(context))
            suggestions.extend(self._get_frequent_command_suggestions())
            suggestions.extend(self._get_workflow_suggestions())
        else:
            # Filter commands based on partial input
            suggestions.extend(self._get_matching_commands(partial_command))
        
        # Sort by relevance
        suggestions.sort(key=lambda x: x['relevance'], reverse=True)
        
        return suggestions[:10]  # Return top 10
    
    def _get_context_suggestions(self, context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get suggestions based on current context."""
        suggestions = []
        
        if not context:
            return suggestions
        
        # Suggest based on current directory
        current_dir = context.get('current_directory', '')
        if 'test' in current_dir.lower():
            suggestions.append({
                'command': 'test',
                'description': 'Run tests in current directory',
                'relevance': 0.9,
                'category': 'context'
            })
        
        # Suggest based on recent files
        recent_files = context.get('recent_files', [])
        python_files = [f for f in recent_files if f.endswith('.py')]
        if python_files:
            suggestions.append({
                'command': 'groq-analyze "Analyze this Python code"',
                'description': 'Analyze Python files with AI',
                'relevance': 0.8,
                'category': 'context'
            })
        
        # Suggest based on git status
        git_status = context.get('git_status', '')
        if 'modified' in git_status:
            suggestions.append({
                'command': 'groq-review',
                'description': 'Review modified files with AI',
                'relevance': 0.85,
                'category': 'context'
            })
        
        return suggestions
    
    def _get_frequent_command_suggestions(self) -> List[Dict[str, Any]]:
        """Get suggestions based on frequently used commands."""
        suggestions = []
        frequent_commands = self.history.get_frequent_commands(limit=5)
        
        for command, count in frequent_commands:
            suggestions.append({
                'command': command,
                'description': f'Used {count} times recently',
                'relevance': 0.7,
                'category': 'frequent'
            })
        
        return suggestions
    
    def _get_workflow_suggestions(self) -> List[Dict[str, Any]]:
        """Get workflow-based suggestions."""
        suggestions = []
        
        # Time-based suggestions
        hour = datetime.now().hour
        
        if 9 <= hour <= 11:  # Morning
            suggestions.append({
                'command': 'status',
                'description': 'Check daily status',
                'relevance': 0.6,
                'category': 'workflow'
            })
            suggestions.append({
                'command': 'groq-project-summary',
                'description': 'Review project overview',
                'relevance': 0.6,
                'category': 'workflow'
            })
        
        elif 17 <= hour <= 19:  # Evening
            suggestions.append({
                'command': 'done',
                'description': 'Mark daily tasks complete',
                'relevance': 0.6,
                'category': 'workflow'
            })
        
        return suggestions
    
    def _get_matching_commands(self, partial: str) -> List[Dict[str, Any]]:
        """Get commands that match partial input."""
        suggestions = []
        partial_lower = partial.lower()
        
        # Check all command patterns
        for category, commands in self.command_patterns.items():
            for command in commands:
                if partial_lower in command.lower():
                    relevance = self._calculate_relevance(partial_lower, command)
                    suggestions.append({
                        'command': command,
                        'description': self._get_command_description(command),
                        'relevance': relevance,
                        'category': 'match'
                    })
        
        return suggestions
    
    def _calculate_relevance(self, partial: str, command: str) -> float:
        """Calculate relevance score for a command match."""
        if command.startswith(partial):
            return 0.9
        elif partial in command:
            return 0.7
        else:
            return 0.5
    
    def _get_command_description(self, command: str) -> str:
        """Get description for a command."""
        descriptions = {
            'groq': 'Fast AI chat and analysis',
            'groq-analyze': 'Deep project analysis with AI',
            'groq-chat': 'Interactive AI conversation',
            'groq-enhance': 'AI-driven code improvements',
            'groq-security-scan': 'Security vulnerability scan',
            'groq-architecture-map': 'Project architecture mapping',
            'groq-project-summary': 'Comprehensive project overview',
            'status': 'Show current status',
            'test': 'Run tests',
            'deploy': 'Deploy application',
            'docs-generate': 'Generate documentation'
        }
        return descriptions.get(command, f'Execute {command}')


# Global instances
_command_history = CommandHistory()
_command_suggester = CommandSuggester(_command_history)


def get_command_history() -> CommandHistory:
    """Get the global command history instance."""
    return _command_history


def get_command_suggester() -> CommandSuggester:
    """Get the global command suggester instance."""
    return _command_suggester


def record_command(command: str, duration: float, exit_code: int, 
                  working_directory: str, args: Dict[str, Any]):
    """Record a command execution."""
    _command_history.add_command(command, duration, exit_code, working_directory, args)


def get_command_suggestions(partial_command: str = "", 
                           context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Get command suggestions."""
    return _command_suggester.get_suggestions(partial_command, context)
