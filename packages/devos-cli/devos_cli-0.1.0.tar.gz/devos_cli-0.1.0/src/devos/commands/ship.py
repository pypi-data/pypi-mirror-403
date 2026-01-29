"""Release automation command."""

import click
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from devos.core.database import Database


@click.command()
@click.argument('version_type', type=click.Choice(['patch', 'minor', 'major']))
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.option('--no-changelog', is_flag=True, help='Skip changelog generation')
@click.option('--custom-message', help='Custom release message')
@click.pass_context
def release(ctx, version_type: str, dry_run: bool, no_changelog: bool, custom_message: Optional[str]):
    """Create a new release with semantic versioning."""
    
    config = ctx.obj['config']
    db = ctx.obj['db']
    
    # Check if we're in a git repository
    if not _is_git_repository():
        click.echo("Error: Not in a git repository.", err=True)
        return
    
    # Check for uncommitted changes
    if not _is_git_clean():
        click.echo("Error: Working directory has uncommitted changes.", err=True)
        click.echo("Please commit or stash changes before releasing.")
        return
    
    # Find current project
    project_id = _find_current_project(db)
    if not project_id:
        click.echo("Warning: No DevOS project found for current directory.", err=True)
        if not click.confirm("Continue anyway?"):
            return
    
    # Get current version
    current_version = _get_current_version()
    if not current_version:
        click.echo("Warning: No version tags found. Starting from 0.1.0")
        current_version = "0.1.0"
    
    # Calculate next version
    next_version = _calculate_next_version(current_version, version_type)
    
    # Show release plan
    click.echo(f"Release Plan:")
    click.echo(f"  Current version: {current_version}")
    click.echo(f"  Next version: {next_version}")
    click.echo(f"  Version type: {version_type}")
    
    if not dry_run:
        if not click.confirm("\nProceed with release?"):
            click.echo("Release cancelled.")
            return
    
    # Generate changelog
    changelog = ""
    if not no_changelog:
        click.echo("Generating changelog...")
        changelog = _generate_changelog(current_version)
        
        if not changelog:
            click.echo("No commits found since last release.")
            if not click.confirm("Continue anyway?"):
                return
        
        click.echo("Changelog:")
        click.echo("-" * 40)
        click.echo(changelog)
        click.echo("-" * 40)
        
        if not dry_run and not click.confirm("Use this changelog?"):
            changelog = click.prompt("Enter custom changelog", default="")
    
    # Set custom message if provided
    release_message = custom_message or f"Release {next_version}"
    
    # Execute release steps
    if dry_run:
        click.echo("\n[Dry run] Would execute:")
        click.echo(f"  1. Create tag: v{next_version}")
        click.echo(f"  2. Push tag to remote")
        if changelog:
            click.echo(f"  3. Update changelog")
    else:
        success = _execute_release(next_version, release_message, changelog)
        
        if success:
            click.echo(f"Released version {next_version}")
            
            # Track release in database
            if project_id:
                _track_release(db, project_id, next_version, version_type)
        else:
            click.echo("Release failed.", err=True)


@click.command()
@click.option('--since', help='Git reference (tag, commit, etc.)')
@click.option('--format', type=click.Choice(['markdown', 'json']), default='markdown', help='Output format')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def changelog(ctx, since: Optional[str], format: str, output: Optional[str]):
    """Generate changelog from git commits."""
    
    # Check if we're in a git repository
    if not _is_git_repository():
        click.echo("Error: Not in a git repository.", err=True)
        return
    
    # Get current version or use provided reference
    if not since:
        current_version = _get_current_version()
        since = current_version if current_version else None
    
    # Generate changelog
    changelog_content = _generate_changelog(since)
    
    if not changelog_content:
        click.echo("No commits found.")
        return
    
    # Output changelog
    if format == 'json':
        import json
        changelog_data = {
            'since': since,
            'generated_at': datetime.now().isoformat(),
            'entries': changelog_content.split('\n')
        }
        content = json.dumps(changelog_data, indent=2)
    else:
        content = f"# Changelog\n\n{changelog_content}"
    
    if output:
        Path(output).write_text(content)
        click.echo(f"Changelog saved to {output}")
    else:
        click.echo(content)


@click.command()
@click.pass_context
def version(ctx):
    """Show current version."""
    
    # Check if we're in a git repository
    if not _is_git_repository():
        click.echo("Error: Not in a git repository.", err=True)
        return
    
    current_version = _get_current_version()
    if current_version:
        click.echo(f"Current version: {current_version}")
    else:
        click.echo("No version tags found.")


def _is_git_repository() -> bool:
    """Check if current directory is a git repository."""
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _is_git_clean() -> bool:
    """Check if git working directory is clean."""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        return len(result.stdout.strip()) == 0
    except subprocess.CalledProcessError:
        return False


def _get_current_version() -> Optional[str]:
    """Get current version from git tags."""
    try:
        # Get latest version tag
        result = subprocess.run(['git', 'tag', '--sort=-version:refname'], 
                              capture_output=True, text=True, check=True)
        
        tags = result.stdout.strip().split('\n')
        version_tags = [tag for tag in tags if tag.startswith('v') and _is_semver(tag[1:])]
        
        return version_tags[0] if version_tags else None
    except subprocess.CalledProcessError:
        return None


def _is_semver(version: str) -> bool:
    """Check if string follows semantic versioning."""
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9\-\.]+)?(\+[a-zA-Z0-9\-\.]+)?$'
    return bool(re.match(pattern, version))


def _calculate_next_version(current: str, version_type: str) -> str:
    """Calculate next semantic version."""
    if not _is_semver(current):
        return "1.0.0"
    
    # Remove 'v' prefix if present
    if current.startswith('v'):
        current = current[1:]
    
    parts = current.split('.')
    major = int(parts[0])
    minor = int(parts[1])
    patch = int(parts[2].split('-')[0])  # Remove prerelease part
    
    if version_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif version_type == 'minor':
        minor += 1
        patch = 0
    elif version_type == 'patch':
        patch += 1
    
    return f"{major}.{minor}.{patch}"


def _generate_changelog(since: Optional[str]) -> str:
    """Generate changelog from git commits."""
    try:
        # Get commit range
        if since:
            commit_range = f"{since}..HEAD"
        else:
            commit_range = "HEAD"
        
        # Get commits
        result = subprocess.run([
            'git', 'log', 
            '--pretty=format:%h|%s|%an|%ad',
            '--date=short',
            commit_range
        ], capture_output=True, text=True, check=True)
        
        commits = result.stdout.strip().split('\n')
        if not commits or commits == ['']:
            return ""
        
        # Parse commits
        entries = []
        for commit in commits:
            if not commit.strip():
                continue
            
            parts = commit.split('|')
            if len(parts) >= 4:
                hash_, message, author, date = parts[:4]
                entries.append({
                    'hash': hash_,
                    'message': message,
                    'author': author,
                    'date': date
                })
        
        # Group by conventional commits
        grouped = {
            'feat': [],
            'fix': [],
            'docs': [],
            'style': [],
            'refactor': [],
            'test': [],
            'chore': [],
            'other': []
        }
        
        for entry in entries:
            message = entry['message']
            category = 'other'
            
            # Check for conventional commit
            if message.startswith('feat'):
                category = 'feat'
            elif message.startswith('fix'):
                category = 'fix'
            elif message.startswith('docs'):
                category = 'docs'
            elif message.startswith('style'):
                category = 'style'
            elif message.startswith('refactor'):
                category = 'refactor'
            elif message.startswith('test'):
                category = 'test'
            elif message.startswith('chore'):
                category = 'chore'
            
            grouped[category].append(entry)
        
        # Generate changelog content
        lines = []
        
        for category in ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'other']:
            entries = grouped[category]
            if not entries:
                continue
            
            category_title = {
                'feat': 'Features',
                'fix': 'Bug Fixes',
                'docs': 'Documentation',
                'style': 'Style',
                'refactor': 'Refactoring',
                'test': 'Tests',
                'chore': 'Chores',
                'other': 'Other'
            }[category]
            
            lines.append(f"### {category_title}")
            lines.append("")
            
            for entry in entries:
                hash_short = entry['hash'][:7]
                message = entry['message']
                lines.append(f"- {message} ({hash_short})")
            
            lines.append("")
        
        return "\n".join(lines).strip()
        
    except subprocess.CalledProcessError:
        return ""


def _execute_release(version: str, message: str, changelog: str) -> bool:
    """Execute release steps."""
    try:
        # Create tag
        tag_name = f"v{version}"
        subprocess.run(['git', 'tag', '-a', tag_name, '-m', message], 
                      check=True, capture_output=True)
        
        # Push tag
        try:
            subprocess.run(['git', 'push', 'origin', tag_name], 
                          check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # Remote push failed, but local tag was created
            click.echo("Warning: Failed to push tag to remote. Tag created locally.")
        
        # Update changelog file if it exists
        if changelog:
            changelog_file = Path.cwd() / 'CHANGELOG.md'
            if changelog_file.exists():
                content = changelog_file.read_text()
                new_entry = f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n{changelog}\n\n"
                updated_content = new_entry + content
                changelog_file.write_text(updated_content)
                
                # Commit changelog
                subprocess.run(['git', 'add', 'CHANGELOG.md'], 
                              check=True, capture_output=True)
                subprocess.run(['git', 'commit', '-m', f'Update changelog for {version}'], 
                              check=True, capture_output=True)
                subprocess.run(['git', 'push'], check=True, capture_output=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        click.echo(f"Error during release: {e}", err=True)
        return False


def _find_current_project(db: Database) -> Optional[str]:
    """Find DevOS project for current directory."""
    current_dir = Path.cwd().resolve()
    project = db.get_project_by_path(str(current_dir))
    return project['id'] if project else None


def _track_release(db: Database, project_id: str, version: str, version_type: str):
    """Track release in database."""
    # This could be extended to store releases in the database
    # For now, we'll just log it
    click.echo(f"Tracked release: {version} ({version_type}) for project {project_id}")
