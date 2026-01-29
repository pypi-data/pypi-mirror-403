"""Configuration management commands."""

import click
import yaml
from pathlib import Path
from typing import Dict, Any

from devos.core.config import Config
from devos.core.progress import show_success, show_info, show_operation_status


@click.command()
@click.option('--global', 'global_config', is_flag=True, help='Show global configuration')
@click.pass_context
def show(ctx, global_config: bool):
    """Show current configuration."""
    
    config = ctx.obj['config']
    
    if global_config:
        config_path = Path.home() / '.devos' / 'config.yml'
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            click.echo("Global Configuration:")
            click.echo(yaml.dump(config_data, default_flow_style=False))
        else:
            click.echo("No global configuration found.")
    else:
        click.echo("Current Configuration:")
        click.echo(f"  Default language: {config.default_language}")
        click.echo(f"  Auto git tracking: {config.auto_git}")
        click.echo(f"  Week start: {config.week_start}")


@click.command()
@click.argument('key')
@click.argument('value')
@click.option('--global', 'global_config', is_flag=True, help='Set global configuration')
@click.pass_context
def set(ctx, key: str, value: str, global_config: bool):
    """Set a configuration value."""
    
    config = ctx.obj['config']
    
    # Parse value based on key
    parsed_value = _parse_config_value(key, value)
    
    if global_config:
        config_path = Path.home() / '.devos' / 'config.yml'
        config_path.parent.mkdir(exist_ok=True)
        
        # Load existing config
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        else:
            config_data = {}
        
        # Update config
        _set_nested_value(config_data, key, parsed_value)
        
        # Save config
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        show_success(f"Global config '{key}' set to '{value}'")
    else:
        # Set in current config (would need to implement this)
        show_info(f"Local config setting not yet implemented. Use --global for now.")


@click.command()
@click.option('--global', 'global_config', is_flag=True, help='Reset global configuration')
@click.pass_context
def reset(ctx, global_config: bool):
    """Reset configuration to defaults."""
    
    if global_config:
        config_path = Path.home() / '.devos' / 'config.yml'
        if config_path.exists():
            if click.confirm("Reset global configuration to defaults?"):
                config_path.unlink()
                show_success("Global configuration reset to defaults")
        else:
            click.echo("No global configuration to reset.")
    else:
        click.echo("Local config reset not yet implemented.")


@click.command()
@click.pass_context
def init(ctx):
    """Initialize configuration file."""
    
    config_path = Path.home() / '.devos' / 'config.yml'
    
    if config_path.exists():
        if not click.confirm("Configuration file already exists. Overwrite?"):
            click.echo("Configuration initialization cancelled.")
            return
    
    # Create default config
    default_config = {
        'default_language': 'python',
        'tracking': {
            'auto_git': True,
            'default_notes': ''
        },
        'reports': {
            'week_start': 'monday',
            'default_format': 'table'
        },
        'ui': {
            'show_progress': True,
            'emoji': True,
            'color': True
        }
    }
    
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    show_success("Configuration initialized", f"Location: {config_path}")


def _parse_config_value(key: str, value: str) -> Any:
    """Parse configuration value based on key."""
    
    # Boolean values
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    
    # Numeric values
    try:
        if '.' in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass
    
    # String values
    return value


def _set_nested_value(data: Dict[str, Any], key: str, value: Any) -> None:
    """Set nested configuration value using dot notation."""
    
    keys = key.split('.')
    current = data
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value
