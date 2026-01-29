"""Environment variable management command."""

import click
import os
import sys
from pathlib import Path
from typing import Optional

from devos.core.database import Database
from devos.core.crypto import Crypto


@click.command()
@click.argument('key')
@click.option('--project', '-p', help='Project name or path')
@click.option('--global', 'global_', is_flag=True, help='Set global environment variable')
@click.option('--value', prompt='Enter value', hide_input=True, help='Environment variable value')
@click.pass_context
def set(ctx, key: str, project: Optional[str], global_: bool, value: str):
    """Set an environment variable."""
    
    config = ctx.obj['config']
    db = ctx.obj['db']
    
    # Determine project scope
    project_id = None
    if not global_:
        project_id = _find_project(db, project)
        if not project_id:
            click.echo("No project found. Use --global to set a global variable.", err=True)
            return
    
    # Encrypt value
    crypto = Crypto(config.config_dir)
    encrypted_value = crypto.encrypt(value)
    
    # Store in database
    env_id = f"env_{int(datetime.now().timestamp())}"
    db.set_env_var(env_id, project_id, key, encrypted_value)
    
    scope = "global" if global_ else f"project {project}"
    click.echo(f"✓ Set environment variable '{key}' for {scope}")


@click.command()
@click.argument('key')
@click.option('--project', '-p', help='Project name or path')
@click.option('--global', 'global_', is_flag=True, help='Get global environment variable')
@click.option('--show', is_flag=True, help='Show the value (default: hide for security)')
@click.pass_context
def get(ctx, key: str, project: Optional[str], global_: bool, show: bool):
    """Get an environment variable."""
    
    config = ctx.obj['config']
    db = ctx.obj['db']
    
    # Determine project scope
    project_id = None
    if not global_:
        project_id = _find_project(db, project)
        if not project_id:
            click.echo("No project found.", err=True)
            return
    
    # Get from database
    env_var = db.get_env_var(project_id, key)
    if not env_var:
        click.echo(f"Environment variable '{key}' not found.")
        return
    
    # Decrypt value
    crypto = Crypto(config.config_dir)
    try:
        value = crypto.decrypt(env_var['encrypted_value'])
    except Exception:
        click.echo("Error decrypting environment variable.", err=True)
        return
    
    if show:
        click.echo(value)
    else:
        # For security, don't show the value by default
        click.echo(f"Environment variable '{key}' exists (use --show to display value)")


@click.command()
@click.option('--project', '-p', help='Project name or path')
@click.option('--global', 'global_', is_flag=True, help='List global environment variables')
@click.option('--show-values', is_flag=True, help='Show decrypted values')
@click.pass_context
def list(ctx, project: Optional[str], global_: bool, show_values: bool):
    """List environment variables."""
    
    config = ctx.obj['config']
    db = ctx.obj['db']
    
    # Determine project scope
    project_id = None
    if not global_:
        project_id = _find_project(db, project)
        if not project_id:
            click.echo("No project found.", err=True)
            return
    
    # Get variables
    env_vars = db.list_env_vars(project_id)
    
    if not env_vars:
        scope = "global" if global_ else f"project {project}"
        click.echo(f"No environment variables found for {scope}.")
        return
    
    crypto = Crypto(config.config_dir)
    
    click.echo(f"Environment variables ({'global' if global_ else f'project {project}'}):")
    click.echo("-" * 40)
    
    for env_var in env_vars:
        key = env_var['key']
        
        if show_values:
            try:
                value = crypto.decrypt(env_var['encrypted_value'])
                click.echo(f"{key} = {value}")
            except Exception:
                click.echo(f"{key} = [DECRYPT ERROR]")
        else:
            click.echo(key)


@click.command()
@click.argument('key')
@click.option('--project', '-p', help='Project name or path')
@click.option('--global', 'global_', is_flag=True, help='Delete global environment variable')
@click.pass_context
def delete(ctx, key: str, project: Optional[str], global_: bool):
    """Delete an environment variable."""
    
    db = ctx.obj['db']
    
    # Determine project scope
    project_id = None
    if not global_:
        project_id = _find_project(db, project)
        if not project_id:
            click.echo("No project found.", err=True)
            return
    
    # Check if variable exists
    env_var = db.get_env_var(project_id, key)
    if not env_var:
        click.echo(f"Environment variable '{key}' not found.")
        return
    
    # Confirm deletion
    if not click.confirm(f"Delete environment variable '{key}'?"):
        click.echo("Deletion cancelled.")
        return
    
    # Delete from database
    success = db.delete_env_var(project_id, key)
    
    if success:
        scope = "global" if global_ else f"project {project}"
        click.echo(f"✓ Deleted environment variable '{key}' from {scope}")
    else:
        click.echo("Error deleting environment variable.", err=True)


@click.command()
@click.option('--project', '-p', help='Project name or path')
@click.option('--output', '-o', help='Output file path (default: .env.example)')
@click.pass_context
def generate_example(ctx, project: Optional[str], output: Optional[str]):
    """Generate .env.example file."""
    
    db = ctx.obj['db']
    
    # Determine project scope
    project_id = None
    project_name = None
    if project:
        project_id = _find_project(db, project)
        if not project_id:
            click.echo("Project '{project}' not found.", err=True)
            return
        
        project_info = db.get_project_by_id(project_id)
        project_name = project_info['name'] if project_info else 'Unknown'
    
    # Get variables (both global and project-specific)
    global_vars = db.list_env_vars(None)
    project_vars = db.list_env_vars(project_id) if project_id else []
    
    # Combine variables, project vars take precedence
    all_vars = {var['key']: var for var in global_vars}
    for var in project_vars:
        all_vars[var['key']] = var
    
    if not all_vars:
        click.echo("No environment variables found.")
        return
    
    # Determine output path
    if output:
        output_path = Path(output)
    elif project_id:
        # Try to find project directory
        project_info = db.get_project_by_id(project_id)
        if project_info:
            output_path = Path(project_info['path']) / '.env.example'
        else:
            output_path = Path.cwd() / '.env.example'
    else:
        output_path = Path.cwd() / '.env.example'
    
    # Generate .env.example content
    lines = ["# Environment variables"]
    lines.append("# Generated by DevOS")
    lines.append("")
    
    for key in sorted(all_vars.keys()):
        lines.append(f"{key}=")
    
    content = "\n".join(lines)
    
    # Write file
    output_path.write_text(content)
    
    click.echo(f"✓ Generated .env.example at {output_path}")
    click.echo(f"  Found {len(all_vars)} environment variables")


@click.command()
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish', 'powershell']))
@click.option('--project', '-p', help='Project name or path')
@click.pass_context
def export(ctx, shell: str, project: Optional[str]):
    """Export environment variables for shell."""
    
    config = ctx.obj['config']
    db = ctx.obj['db']
    
    # Determine project scope
    project_id = None
    if project:
        project_id = _find_project(db, project)
        if not project_id:
            click.echo("Project '{project}' not found.", err=True)
            return
    
    # Get variables (both global and project-specific)
    global_vars = db.list_env_vars(None)
    project_vars = db.list_env_vars(project_id) if project_id else []
    
    # Combine variables, project vars take precedence
    all_vars = {var['key']: var for var in global_vars}
    for var in project_vars:
        all_vars[var['key']] = var
    
    if not all_vars:
        click.echo("No environment variables found.")
        return
    
    crypto = Crypto(config.config_dir)
    
    # Export in shell format
    click.echo(f"# Environment variables for {shell}")
    click.echo("# Generated by DevOS")
    click.echo("# Run with: eval \"$(devos env export {shell})\"")
    click.echo("")
    
    for key in sorted(all_vars.keys()):
        try:
            value = crypto.decrypt(all_vars[key]['encrypted_value'])
            
            if shell == 'bash' or shell == 'zsh':
                click.echo(f"export {key}=\"{value}\"")
            elif shell == 'fish':
                click.echo(f"set -gx {key} \"{value}\"")
            elif shell == 'powershell':
                click.echo(f"$env:{key} = \"{value}\"")
                
        except Exception:
            click.echo(f"# Error decrypting {key}")


def _find_project(db: Database, project_identifier: Optional[str]) -> Optional[str]:
    """Find project by name or path."""
    if not project_identifier:
        # Try to find project by current directory
        current_dir = Path.cwd().resolve()
        project = db.get_project_by_path(str(current_dir))
        return project['id'] if project else None
    
    # Try to find by path first
    path = Path(project_identifier).resolve()
    project = db.get_project_by_path(str(path))
    if project:
        return project['id']
    
    # Try to find by name
    projects = db.list_projects()
    for proj in projects:
        if proj['name'] == project_identifier:
            return proj['id']
    
    return None


# Import datetime for env_id generation
from datetime import datetime
