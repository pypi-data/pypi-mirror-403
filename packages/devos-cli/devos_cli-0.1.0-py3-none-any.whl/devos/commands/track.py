"""Work session tracking command."""

import click
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from devos.core.database import Database


@click.command()
@click.option('--project', '-p', help='Project name or path')
@click.option('--notes', '-n', help='Session notes')
@click.pass_context
def start(ctx, project: Optional[str], notes: Optional[str]):
    """Start a new work session."""
    
    config = ctx.obj['config']
    db = ctx.obj['db']
    
    # Check if there's already an active session
    active_session = db.get_active_session()
    if active_session:
        project_info = db.get_project_by_id(active_session['project_id'])
        project_name = project_info['name'] if project_info else 'Unknown'
        click.echo(f"⚠️  Already tracking session for project '{project_name}' (started at {active_session['start_time']})")
        if not click.confirm("Stop current session and start a new one?"):
            click.echo("Session start cancelled.")
            return
    
    # Find project
    project_id = _find_project(db, project)
    if not project_id:
        click.echo("No project found. Use 'devos init' to create a project first.", err=True)
        return
    
    # Create session
    session_id = f"session_{int(datetime.now(timezone.utc).timestamp())}"
    start_time = datetime.now(timezone.utc)
    
    db.create_session(session_id, project_id, start_time)
    
    project_info = db.get_project_by_id(project_id)
    project_name = project_info['name'] if project_info else 'Unknown'
    
    click.echo(f"✓ Started tracking session for '{project_name}'")
    click.echo(f"  Session ID: {session_id}")
    click.echo(f"  Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if notes:
        # Store notes (will be saved when session ends)
        click.echo(f"  Notes: {notes}")
    
    # Show how to stop
    click.echo("\nTo stop tracking:")
    click.echo("  devos track stop")


@click.command()
@click.option('--notes', '-n', help='Session notes')
@click.pass_context
def stop(ctx, notes: Optional[str]):
    """Stop the current work session."""
    
    db = ctx.obj['db']
    
    # Find active session
    active_session = db.get_active_session()
    if not active_session:
        click.echo("No active session found.")
        return
    
    # End session
    end_time = datetime.now(timezone.utc)
    session_notes = notes or ""
    
    success = db.end_session(active_session['id'], end_time, session_notes)
    
    if success:
        project_info = db.get_project_by_id(active_session['project_id'])
        project_name = project_info['name'] if project_info else 'Unknown'
        
        # Get updated session data with duration
        updated_session = db.execute_query(
            "SELECT * FROM sessions WHERE id = ?",
            (active_session['id'],)
        )
        
        if updated_session:
            duration = updated_session[0]['duration'] or 0
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
        else:
            hours = minutes = seconds = 0
        
        click.echo(f"✓ Stopped tracking session for '{project_name}'")
        click.echo(f"  Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
        click.echo(f"  Ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if session_notes:
            click.echo(f"  Notes: {session_notes}")
    else:
        click.echo("Error stopping session.", err=True)


@click.command()
@click.option('--project', '-p', help='Filter by project name or path')
@click.option('--limit', '-l', default=20, help='Number of sessions to show')
@click.pass_context
def status(ctx, project: Optional[str], limit: int):
    """Show current tracking status."""
    
    db = ctx.obj['db']
    
    # Check for active session
    active_session = db.get_active_session()
    
    if active_session:
        project_info = db.get_project_by_id(active_session['project_id'])
        project_name = project_info['name'] if project_info else 'Unknown'
        
        # Calculate current duration
        start_time = datetime.fromisoformat(active_session['start_time'])
        current_time = datetime.now(timezone.utc)
        duration = int((current_time - start_time).total_seconds())
        
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        click.echo("🟢 Currently tracking:")
        click.echo(f"  Project: {project_name}")
        click.echo(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"  Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
        click.echo(f"  Session ID: {active_session['id']}")
    else:
        click.echo("🔴 No active session")
    
    # Show recent sessions
    click.echo("\nRecent sessions:")
    sessions = db.list_sessions(limit=limit)
    
    if not sessions:
        click.echo("  No sessions found.")
        return
    
    for session in sessions:
        project_name = session.get('project_name', 'Unknown')
        start_time = datetime.fromisoformat(session['start_time'])
        
        if session['end_time']:
            end_time = datetime.fromisoformat(session['end_time'])
            duration = session.get('duration', 0)
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            status_emoji = "✅"
            time_info = f"{hours:02d}:{minutes:02d}"
        else:
            end_time = None
            status_emoji = "🟢"
            # Calculate current duration
            current_time = datetime.now(timezone.utc)
            duration = int((current_time - start_time).total_seconds())
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            time_info = f"{hours:02d}:{minutes:02d} (active)"
        
        click.echo(f"  {status_emoji} {project_name} - {start_time.strftime('%m/%d %H:%M')} ({time_info})")


@click.command()
@click.option('--project', '-p', help='Filter by project name or path')
@click.option('--limit', '-l', default=50, help='Number of sessions to show')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def list(ctx, project: Optional[str], limit: int, format: str):
    """List tracking sessions."""
    
    db = ctx.obj['db']
    
    # Find project if specified
    project_id = None
    if project:
        project_id = _find_project(db, project)
        if not project_id:
            click.echo(f"Project '{project}' not found.", err=True)
            return
    
    # Get sessions
    sessions = db.list_sessions(project_id=project_id, limit=limit)
    
    if not sessions:
        click.echo("No sessions found.")
        return
    
    if format == 'json':
        import json
        click.echo(json.dumps(sessions, indent=2, default=str))
    else:
        # Table format
        click.echo(f"{'Project':<20} {'Start':<17} {'Duration':<10} {'Status':<8}")
        click.echo("-" * 60)
        
        for session in sessions:
            project_name = session.get('project_name', 'Unknown')[:18]
            start_time = datetime.fromisoformat(session['start_time'])
            start_str = start_time.strftime('%m/%d %H:%M')
            
            if session['end_time']:
                duration = session.get('duration', 0)
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                duration_str = f"{hours:02d}:{minutes:02d}"
                status = "Completed"
            else:
                # Calculate current duration
                current_time = datetime.now(timezone.utc)
                duration = int((current_time - start_time).total_seconds())
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                duration_str = f"{hours:02d}:{minutes:02d}"
                status = "Active"
            
            click.echo(f"{project_name:<20} {start_str:<17} {duration_str:<10} {status:<8}")


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
