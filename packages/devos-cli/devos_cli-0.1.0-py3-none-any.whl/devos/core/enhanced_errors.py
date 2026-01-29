"""
Enhanced Error Handling and User Feedback
Provides comprehensive error handling, recovery suggestions, and user feedback.
"""

import traceback
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import click
import json


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better handling."""
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    AI_SERVICE = "ai_service"
    DEPENDENCY = "dependency"
    USER_INPUT = "user_input"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for errors."""
    command: str
    working_directory: str
    user_input: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    recent_commands: Optional[List[str]] = None


@dataclass
class ErrorSuggestion:
    """Suggestion for resolving an error."""
    action: str
    description: str
    command: Optional[str] = None
    confidence: float = 0.8  # 0.0 to 1.0


@dataclass
class EnhancedError:
    """Enhanced error information with context and suggestions."""
    original_error: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    context: ErrorContext
    suggestions: List[ErrorSuggestion]
    recovery_possible: bool
    user_friendly_message: str


class ErrorHandler:
    """Enhanced error handler with intelligent suggestions."""
    
    def __init__(self):
        self.error_patterns = {
            ErrorCategory.NETWORK: [
                "connection", "timeout", "network", "dns", "internet", "offline",
                "host", "port", "socket", "http", "https", "url"
            ],
            ErrorCategory.FILESYSTEM: [
                "file", "directory", "path", "not found", "exists", "permission denied",
                "disk", "space", "read", "write", "delete", "create"
            ],
            ErrorCategory.PERMISSION: [
                "permission", "access denied", "unauthorized", "forbidden",
                "admin", "root", "sudo", "privileges"
            ],
            ErrorCategory.CONFIGURATION: [
                "config", "setting", "missing", "invalid", "malformed",
                "api key", "token", "credential", "environment"
            ],
            ErrorCategory.AI_SERVICE: [
                "ai", "model", "groq", "openai", "api", "rate limit",
                "context length", "tokens", "generation"
            ],
            ErrorCategory.DEPENDENCY: [
                "module", "package", "import", "dependency", "version",
                "install", "pip", "npm", "requirement"
            ],
            ErrorCategory.USER_INPUT: [
                "argument", "option", "parameter", "invalid", "required",
                "missing", "format", "type"
            ],
            ErrorCategory.SYSTEM: [
                "memory", "cpu", "process", "system", "os", "platform",
                "python", "version", "architecture"
            ]
        }
        
        self.suggestion_templates = {
            ErrorCategory.NETWORK: [
                ErrorSuggestion(
                    "Check internet connection",
                    "Verify you're connected to the internet",
                    "ping google.com",
                    0.9
                ),
                ErrorSuggestion(
                    "Try again later",
                    "Network issues are often temporary",
                    None,
                    0.7
                ),
                ErrorSuggestion(
                    "Check firewall settings",
                    "Firewall might be blocking the connection",
                    None,
                    0.6
                )
            ],
            ErrorCategory.FILESYSTEM: [
                ErrorSuggestion(
                    "Check file permissions",
                    "Ensure you have read/write permissions",
                    "ls -la",
                    0.8
                ),
                ErrorSuggestion(
                    "Verify file path",
                    "Check if the file/directory exists",
                    "ls path/to/file",
                    0.9
                ),
                ErrorSuggestion(
                    "Check disk space",
                    "Ensure sufficient disk space is available",
                    "df -h",
                    0.7
                )
            ],
            ErrorCategory.PERMISSION: [
                ErrorSuggestion(
                    "Run with elevated privileges",
                    "Try running with sudo/admin rights",
                    "sudo devos command",
                    0.8
                ),
                ErrorSuggestion(
                    "Check user permissions",
                    "Verify your user has the required permissions",
                    "whoami",
                    0.7
                )
            ],
            ErrorCategory.CONFIGURATION: [
                ErrorSuggestion(
                    "Check configuration file",
                    "Verify your config file is valid",
                    "devos config show",
                    0.9
                ),
                ErrorSuggestion(
                    "Set missing API keys",
                    "Configure required API keys",
                    "devos ai-config set",
                    0.8
                ),
                ErrorSuggestion(
                    "Reset configuration",
                    "Reset to default configuration",
                    "devos config reset",
                    0.6
                )
            ],
            ErrorCategory.AI_SERVICE: [
                ErrorSuggestion(
                    "Check API key validity",
                    "Verify your API key is valid and active",
                    "devos groq-status",
                    0.9
                ),
                ErrorSuggestion(
                    "Try different model",
                    "Switch to a different AI model",
                    "devos groq --model llama-3.1-8b-instant",
                    0.8
                ),
                ErrorSuggestion(
                    "Reduce context size",
                    "Large projects may exceed context limits",
                    "devos groq-analyze --scope current",
                    0.7
                ),
                ErrorSuggestion(
                    "Check rate limits",
                    "Wait for rate limits to reset",
                    None,
                    0.6
                )
            ],
            ErrorCategory.DEPENDENCY: [
                ErrorSuggestion(
                    "Install missing dependencies",
                    "Install the required package",
                    "pip install package-name",
                    0.9
                ),
                ErrorSuggestion(
                    "Update dependencies",
                    "Update to latest compatible versions",
                    "pip install --upgrade",
                    0.7
                ),
                ErrorSuggestion(
                    "Check Python version",
                    "Verify Python version compatibility",
                    "python --version",
                    0.8
                )
            ],
            ErrorCategory.USER_INPUT: [
                ErrorSuggestion(
                    "Check command syntax",
                    "Verify correct command usage",
                    "devos --help",
                    0.9
                ),
                ErrorSuggestion(
                    "Review required arguments",
                    "Ensure all required arguments are provided",
                    "devos command --help",
                    0.8
                )
            ],
            ErrorCategory.SYSTEM: [
                ErrorSuggestion(
                    "Check system resources",
                    "Verify sufficient memory and CPU",
                    "free -h",
                    0.8
                ),
                ErrorSuggestion(
                    "Restart application",
                    "Sometimes a simple restart fixes issues",
                    None,
                    0.7
                )
            ]
        }
    
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error based on its message and type."""
        error_message = str(error).lower()
        error_type = type(error).__name__.lower()
        
        combined_text = f"{error_message} {error_type}"
        
        # Check each category
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern in combined_text:
                    return category
        
        return ErrorCategory.UNKNOWN
    
    def determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity."""
        error_message = str(error).lower()
        
        # Critical errors
        critical_indicators = ["critical", "fatal", "crash", "corruption", "security"]
        if any(indicator in error_message for indicator in critical_indicators):
            return ErrorSeverity.CRITICAL
        
        # High severity
        high_indicators = ["failed", "error", "exception", "unauthorized", "forbidden"]
        if category in [ErrorCategory.PERMISSION, ErrorCategory.AI_SERVICE]:
            return ErrorSeverity.HIGH
        if any(indicator in error_message for indicator in high_indicators):
            return ErrorSeverity.HIGH
        
        # Medium severity
        medium_indicators = ["warning", "timeout", "limit", "deprecated"]
        if category in [ErrorCategory.NETWORK, ErrorCategory.AI_SERVICE]:
            return ErrorSeverity.MEDIUM
        if any(indicator in error_message for indicator in medium_indicators):
            return ErrorSeverity.MEDIUM
        
        # Low severity
        return ErrorSeverity.LOW
    
    def get_suggestions(self, category: ErrorCategory, error: Exception) -> List[ErrorSuggestion]:
        """Get suggestions for resolving an error."""
        suggestions = self.suggestion_templates.get(category, []).copy()
        
        # Add specific suggestions based on error message
        error_message = str(error).lower()
        
        if "api key" in error_message:
            suggestions.append(ErrorSuggestion(
                "Configure API key",
                "Set up your API key in the configuration",
                "devos ai-config set groq_api_key YOUR_KEY",
                0.95
            ))
        
        if "context length" in error_message:
            suggestions.append(ErrorSuggestion(
                "Use smaller scope",
                "Limit analysis to specific files or directories",
                "devos groq-analyze --scope src/",
                0.9
            ))
        
        if "permission denied" in error_message:
            suggestions.append(ErrorSuggestion(
                "Change file permissions",
                "Modify file permissions to allow access",
                "chmod 644 filename",
                0.8
            ))
        
        return suggestions
    
    def create_user_friendly_message(self, error: Exception, category: ErrorCategory) -> str:
        """Create a user-friendly error message."""
        error_message = str(error)
        
        # Make common errors more user-friendly
        user_friendly_messages = {
            ErrorCategory.NETWORK: "Network connection issue detected",
            ErrorCategory.FILESYSTEM: "File or directory access problem",
            ErrorCategory.PERMISSION: "Permission or access rights issue",
            ErrorCategory.CONFIGURATION: "Configuration or settings problem",
            ErrorCategory.AI_SERVICE: "AI service or API issue",
            ErrorCategory.DEPENDENCY: "Missing or incompatible dependency",
            ErrorCategory.USER_INPUT: "Invalid command or argument",
            ErrorCategory.SYSTEM: "System resource or environment issue"
        }
        
        base_message = user_friendly_messages.get(category, "An unexpected error occurred")
        
        # Add specific details if available
        if error_message and len(error_message) < 100:
            return f"{base_message}: {error_message}"
        else:
            return base_message
    
    def enhance_error(self, error: Exception, context: ErrorContext) -> EnhancedError:
        """Create an enhanced error with context and suggestions."""
        category = self.categorize_error(error)
        severity = self.determine_severity(error, category)
        suggestions = self.get_suggestions(category, error)
        user_friendly_message = self.create_user_friendly_message(error, category)
        
        # Determine if recovery is possible
        recovery_possible = severity != ErrorSeverity.CRITICAL and len(suggestions) > 0
        
        return EnhancedError(
            original_error=error,
            severity=severity,
            category=category,
            message=str(error),
            context=context,
            suggestions=suggestions,
            recovery_possible=recovery_possible,
            user_friendly_message=user_friendly_message
        )
    
    def handle_error(self, error: Exception, context: ErrorContext) -> EnhancedError:
        """Handle an error and provide enhanced feedback."""
        enhanced_error = self.enhance_error(error, context)
        
        # Display error information
        self._display_error(enhanced_error)
        
        # Log error for debugging
        self._log_error(enhanced_error)
        
        return enhanced_error
    
    def _display_error(self, enhanced_error: EnhancedError):
        """Display enhanced error information to user."""
        severity_emoji = {
            ErrorSeverity.LOW: "🟡",
            ErrorSeverity.MEDIUM: "🟠", 
            ErrorSeverity.HIGH: "🔴",
            ErrorSeverity.CRITICAL: "🚨"
        }
        
        category_emoji = {
            ErrorCategory.NETWORK: "🌐",
            ErrorCategory.FILESYSTEM: "📁",
            ErrorCategory.PERMISSION: "🔐",
            ErrorCategory.CONFIGURATION: "⚙️",
            ErrorCategory.AI_SERVICE: "🤖",
            ErrorCategory.DEPENDENCY: "📦",
            ErrorCategory.USER_INPUT: "💬",
            ErrorCategory.SYSTEM: "💻",
            ErrorCategory.UNKNOWN: "❓"
        }
        
        # Main error message
        emoji = severity_emoji[enhanced_error.severity]
        click.echo(f"\n{emoji} {enhanced_error.user_friendly_message}")
        
        # Category and context
        cat_emoji = category_emoji[enhanced_error.category]
        click.echo(f"   {cat_emoji} Category: {enhanced_error.category.value}")
        click.echo(f"   📁 Location: {enhanced_error.context.working_directory}")
        click.echo(f"   💻 Command: {enhanced_error.context.command}")
        
        # Suggestions
        if enhanced_error.suggestions:
            click.echo(f"\n💡 Suggestions to resolve:")
            for i, suggestion in enumerate(enhanced_error.suggestions[:3], 1):  # Show top 3
                confidence_emoji = "🎯" if suggestion.confidence > 0.8 else "💭"
                click.echo(f"   {i}. {confidence_emoji} {suggestion.description}")
                if suggestion.command:
                    click.echo(f"      💻 {suggestion.command}")
        
        # Recovery info
        if enhanced_error.recovery_possible:
            click.echo(f"\n✅ Recovery is possible - try the suggestions above")
        else:
            click.echo(f"\n⚠️  This error may require manual intervention")
        
        # Debug info (for high severity)
        if enhanced_error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            click.echo(f"\n🔍 Debug info: {enhanced_error.message}")
    
    def _log_error(self, enhanced_error: EnhancedError):
        """Log error for debugging and analysis."""
        log_file = Path.home() / ".devos" / "error_log.json"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "severity": enhanced_error.severity.value,
                "category": enhanced_error.category.value,
                "message": enhanced_error.message,
                "command": enhanced_error.context.command,
                "working_directory": enhanced_error.context.working_directory,
                "suggestions_provided": len(enhanced_error.suggestions),
                "recovery_possible": enhanced_error.recovery_possible
            }
            
            # Load existing logs
            logs = []
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            
            # Add new entry
            logs.append(log_entry)
            
            # Keep only last 100 entries
            logs = logs[-100:]
            
            # Save logs
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception:
            # If logging fails, don't let it break the error handling
            pass


# Global error handler instance
_error_handler = ErrorHandler()


def handle_error(error: Exception, command: str, working_directory: str = None, 
                user_input: str = None) -> EnhancedError:
    """Handle an error with enhanced feedback."""
    if working_directory is None:
        working_directory = str(Path.cwd())
    
    context = ErrorContext(
        command=command,
        working_directory=working_directory,
        user_input=user_input
    )
    
    return _error_handler.handle_error(error, context)


def create_error_context(command: str, working_directory: str = None, 
                        user_input: str = None) -> ErrorContext:
    """Create error context for error handling."""
    if working_directory is None:
        working_directory = str(Path.cwd())
    
    return ErrorContext(
        command=command,
        working_directory=working_directory,
        user_input=user_input
    )


# Decorator for automatic error handling
def handle_errors(command_name: str = None):
    """Decorator to automatically handle errors in functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                cmd_name = command_name or func.__name__
                handle_error(e, cmd_name)
                sys.exit(1)
        return wrapper
    return decorator
