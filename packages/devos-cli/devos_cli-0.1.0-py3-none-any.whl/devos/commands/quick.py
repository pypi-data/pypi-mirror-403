"""Quick commands for common operations."""

import click
from datetime import datetime
from pathlib import Path

from devos.core.database import Database
from devos.core.progress import show_success, show_info, show_warning


@click.command()
@click.pass_context
def now(ctx):
    """Quick start tracking current project."""
    
    db = ctx.obj['db']
    
    # Check if already tracking
    active_session = db.get_active_session()
    if active_session:
        project_info = db.get_project_by_id(active_session['project_id'])
        project_name = project_info['name'] if project_info else 'Unknown'
        show_warning(f"Already tracking '{project_name}'", "Use 'devos t stop' to stop first")
        return
    
    # Find current project
    current_dir = Path.cwd().resolve()
    project = db.get_project_by_path(str(current_dir))
    
    if not project:
        show_warning("No project found in current directory", "Use 'devos init' or navigate to a project directory")
        return
    
    # Start session
    from devos.commands.track import start
    start(ctx, None, None)


@click.command()
@click.pass_context
def done(ctx):
    """Quick stop current tracking session."""
    
    db = ctx.obj['db']
    
    # Check if tracking
    active_session = db.get_active_session()
    if not active_session:
        show_warning("No active session", "Use 'devos now' to start tracking")
        return
    
    # Stop session
    from devos.commands.track import stop
    stop(ctx, None)


@click.command()
@click.pass_context
def status(ctx):
    """Quick status overview."""
    
    db = ctx.obj['db']
    
    # Active session
    active_session = db.get_active_session()
    
    if active_session:
        project_info = db.get_project_by_id(active_session['project_id'])
        project_name = project_info['name'] if project_info else 'Unknown'
        
        # Calculate duration
        from datetime import datetime, timezone
        start_time = datetime.fromisoformat(active_session['start_time'])
        current_time = datetime.now(timezone.utc)
        duration = int((current_time - start_time).total_seconds())
        
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        
        show_success(f"Tracking {project_name}", f"For {hours:02d}:{minutes:02d}")
    else:
        show_info("Not tracking any session")
    
    # Recent projects
    recent_projects = db.list_projects(limit=3)
    if recent_projects:
        click.echo("\n📁 Recent projects:")
        for project in recent_projects:
            click.echo(f"  • {project['name']} ({project['language']})")


@click.command()
@click.pass_context
def today(ctx):
    """Show today's tracking summary."""
    
    db = ctx.obj['db']
    
    # Get today's sessions
    from datetime import datetime, timezone
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    sessions = db.execute_query(
        """
        SELECT s.*, p.name as project_name 
        FROM sessions s 
        JOIN projects p ON s.project_id = p.id 
        WHERE s.start_time >= ? 
        ORDER BY s.start_time DESC
        """,
        (today_start.isoformat(),)
    )
    
    if not sessions:
        show_info("No sessions today")
        return
    
    # Calculate totals
    total_seconds = 0
    project_time = {}
    
    click.echo("📊 Today's Summary")
    click.echo("-" * 30)
    
    for session in sessions:
        project_name = session['project_name']
        start_time = datetime.fromisoformat(session['start_time'])
        
        if session['end_time']:
            end_time = datetime.fromisoformat(session['end_time'])
            duration = session.get('duration', 0)
        else:
            # Calculate current duration for active session
            current_time = datetime.now(timezone.utc)
            duration = int((current_time - start_time).total_seconds())
        
        total_seconds += duration
        project_time[project_name] = project_time.get(project_name, 0) + duration
        
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        
        status = "🟢" if not session['end_time'] else "✅"
        click.echo(f"{status} {project_name}: {hours:02d}:{minutes:02d}")
    
    # Total time
    total_hours = total_seconds // 3600
    total_minutes = (total_seconds % 3600) // 60
    
    click.echo(f"\n💪 Total: {total_hours:02d}:{total_minutes:02d}")
    
    # Project breakdown
    if len(project_time) > 1:
        click.echo("\n📈 By Project:")
        for project, seconds in project_time.items():
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            percentage = (seconds / total_seconds) * 100
            click.echo(f"  {project}: {hours:02d}:{minutes:02d} ({percentage:.1f}%)")


@click.command()
@click.pass_context
def projects(ctx):
    """Quick list of all projects."""
    
    db = ctx.obj['db']
    project_list = db.list_projects()
    
    if not project_list:
        show_warning("No projects found", "Use 'devos init' to create your first project")
        return
    
    click.echo("📁 Your Projects")
    click.echo("-" * 30)
    
    for project in project_list:
        # Check if currently in this project directory
        current_dir = Path.cwd().resolve()
        is_current = str(current_dir) == project['path']
        
        indicator = "👉" if is_current else "  "
        click.echo(f"{indicator} {project['name']} ({project['language']})")
        if is_current:
            click.echo("     (current directory)")


@click.command()
@click.argument('command_name', required=False)
@click.pass_context
def recent(ctx, command_name: str):
    """Show recent activity or run recent command."""
    
    if command_name:
        # This would integrate with command history
        show_info(f"Running recent command: {command_name}")
        show_info("Command history feature coming soon!")
        return
    
    # Show recent activity
    db = ctx.obj['db']
    
    # Recent sessions
    sessions = db.list_sessions(limit=5)
    
    if not sessions:
        show_info("No recent activity")
        return
    
    click.echo("🕐 Recent Activity")
    click.echo("-" * 30)
    
    for session in sessions:
        project_name = session.get('project_name', 'Unknown')
        start_time = datetime.fromisoformat(session['start_time'])
        
        if session['end_time']:
            duration = session.get('duration', 0)
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            status = "✅"
            time_info = f"{hours:02d}:{minutes:02d}"
        else:
            status = "🟢"
            time_info = "active"
        
        click.echo(f"{status} {project_name} - {start_time.strftime('%m/%d %H:%M')} ({time_info})")


@click.command()
@click.pass_context
def setup(ctx):
    """Quick setup wizard for new users."""
    
    click.echo("🚀 DevOS Quick Setup")
    click.echo("=" * 30)
    
    # Initialize config
    from devos.commands.config import init as config_init
    config_init(ctx)
    
    # Ask about default language
    default_lang = click.prompt(
        "Default programming language",
        type=click.Choice(['python', 'javascript', 'typescript', 'go', 'rust']),
        default='python'
    )
    
    from devos.commands.config import set as config_set
    config_set(ctx, 'default_language', default_lang, True)
    
    # Ask about auto git
    auto_git = click.confirm("Enable automatic git integration?", default=True)
    config_set(ctx, 'tracking.auto_git', str(auto_git), True)
    
    show_success("Setup complete!", "You're ready to start using DevOS")
    
    # Offer to create first project
    if click.confirm("Create your first project now?"):
        from devos.commands.interactive import _create_project_interactive
        _create_project_interactive(ctx)
