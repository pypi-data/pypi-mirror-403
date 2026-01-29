"""Custom exceptions for DevOS CLI."""

import click
from typing import Optional


class DevOSError(Exception):
    """Base exception for DevOS errors."""
    
    def __init__(self, message: str, suggestion: Optional[str] = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


class ProjectNotFoundError(DevOSError):
    """Raised when a project is not found."""
    
    def __init__(self, project_name: str):
        message = f"Project '{project_name}' not found."
        suggestion = "Use 'devos init' to create a project or check the project name."
        super().__init__(message, suggestion)


class DatabaseError(DevOSError):
    """Raised when database operations fail."""
    
    def __init__(self, operation: str, details: str):
        message = f"Database error during {operation}: {details}"
        suggestion = "Check if DevOS is properly installed and permissions are correct."
        super().__init__(message, suggestion)


class ConfigurationError(DevOSError):
    """Raised when configuration is invalid."""
    
    def __init__(self, config_key: str, details: str):
        message = f"Configuration error for '{config_key}': {details}"
        suggestion = "Check your DevOS configuration in ~/.devos/config.yml"
        super().__init__(message, suggestion)


class SessionError(DevOSError):
    """Raised when session operations fail."""
    
    def __init__(self, operation: str, details: str):
        message = f"Session {operation} failed: {details}"
        suggestion = "Use 'devos track status' to check current session state."
        super().__init__(message, suggestion)


def handle_error(error: Exception) -> None:
    """Handle and display errors with helpful suggestions."""
    
    if isinstance(error, DevOSError):
        click.echo(f"❌ Error: {error.message}", err=True)
        if error.suggestion:
            click.echo(f"💡 Suggestion: {error.suggestion}", err=True)
    elif isinstance(error, click.ClickException):
        # Let Click handle its own exceptions
        raise error
    else:
        click.echo(f"❌ Unexpected error: {str(error)}", err=True)
        click.echo("💡 Suggestion: Try running with --verbose for more details", err=True)
