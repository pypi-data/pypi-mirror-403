"""Interactive mode with guided workflows."""

import click
from typing import List, Dict, Any
from devos.core.progress import show_info, show_success, show_warning


@click.command()
@click.pass_context
def interactive(ctx):
    """Start interactive mode with guided workflows."""
    
    click.echo("🚀 Welcome to DevOS Interactive Mode")
    click.echo("=" * 50)
    
    while True:
        choice = _show_main_menu()
        
        if choice == '1':
            _project_workflow(ctx)
        elif choice == '2':
            _tracking_workflow(ctx)
        elif choice == '3':
            _environment_workflow(ctx)
        elif choice == '4':
            _reports_workflow(ctx)
        elif choice == '5':
            _release_workflow(ctx)
        elif choice == '6':
            _config_workflow(ctx)
        elif choice == 'q':
            click.echo("👋 Goodbye!")
            break
        else:
            show_warning("Invalid choice", "Please select a valid option")
        
        if choice != 'q':
            click.echo()
            input("Press Enter to continue...")
            click.echo()


def _show_main_menu() -> str:
    """Show the main interactive menu."""
    
    click.echo("\nWhat would you like to do?")
    click.echo("1. 📁 Project Management")
    click.echo("2. ⏱️  Time Tracking")
    click.echo("3. 🔐 Environment Variables")
    click.echo("4. 📊 Reports & Analytics")
    click.echo("5. 🚀 Release Management")
    click.echo("6. ⚙️  Configuration")
    click.echo("q. Quit")
    
    return click.prompt("\nSelect an option", type=str, show_default=False)


def _project_workflow(ctx) -> None:
    """Guided project management workflow."""
    
    click.echo("\n📁 Project Management")
    click.echo("-" * 30)
    
    options = [
        "Create a new project",
        "List existing projects",
        "Switch to a project",
        "Delete a project"
    ]
    
    for i, option in enumerate(options, 1):
        click.echo(f"{i}. {option}")
    
    choice = click.prompt("Select an option", type=click.IntRange(1, len(options)))
    
    if choice == 1:
        _create_project_interactive(ctx)
    elif choice == 2:
        _list_projects_interactive(ctx)
    elif choice == 3:
        _switch_project_interactive(ctx)
    elif choice == 4:
        _delete_project_interactive(ctx)


def _tracking_workflow(ctx) -> None:
    """Guided time tracking workflow."""
    
    click.echo("\n⏱️  Time Tracking")
    click.echo("-" * 30)
    
    # Check current status
    from devos.core.database import Database
    db = ctx.obj['db']
    active_session = db.get_active_session()
    
    if active_session:
        project_info = db.get_project_by_id(active_session['project_id'])
        project_name = project_info['name'] if project_info else 'Unknown'
        
        click.echo(f"🟢 Currently tracking: {project_name}")
        click.echo("1. Stop current session")
        click.echo("2. Add notes to current session")
        click.echo("3. View session details")
    else:
        click.echo("🔴 No active session")
        click.echo("1. Start a new session")
        click.echo("2. View recent sessions")
        click.echo("3. View session history")
    
    choice = click.prompt("Select an option", type=click.IntRange(1, 3))
    
    # Implementation would call the appropriate track commands
    if active_session:
        if choice == 1:
            from devos.commands.track import stop
            stop(ctx, notes=click.prompt("Session notes (optional)", default="", show_default=False))
        elif choice == 2:
            # Add notes logic would go here
            show_info("Add notes feature coming soon!")
        elif choice == 3:
            from devos.commands.track import status
            status(ctx, None, 10)
    else:
        if choice == 1:
            from devos.commands.track import start
            start(ctx, None, click.prompt("Session notes (optional)", default="", show_default=False))
        elif choice == 2:
            from devos.commands.track import status
            status(ctx, None, 10)
        elif choice == 3:
            from devos.commands.track import list
            list(ctx, None, 20, 'table')


def _environment_workflow(ctx) -> None:
    """Guided environment variable workflow."""
    
    click.echo("\n🔐 Environment Variables")
    click.echo("-" * 30)
    
    options = [
        "Set a new environment variable",
        "View existing variables",
        "Export variables for shell",
        "Generate .env.example"
    ]
    
    for i, option in enumerate(options, 1):
        click.echo(f"{i}. {option}")
    
    choice = click.prompt("Select an option", type=click.IntRange(1, len(options)))
    
    # Implementation would call the appropriate env commands
    if choice == 1:
        from devos.commands.env import set as env_set
        var_name = click.prompt("Variable name")
        env_set(ctx, var_name, None, False, None)
    elif choice == 2:
        from devos.commands.env import list as env_list
        env_list(ctx, False, False, None)
    elif choice == 3:
        shell = click.prompt("Shell type", type=click.Choice(['bash', 'zsh', 'fish', 'powershell']), default='bash')
        from devos.commands.env import export
        export(ctx, shell, None)
    elif choice == 4:
        from devos.commands.env import generate_example
        generate_example(ctx, None, None)


def _reports_workflow(ctx) -> None:
    """Guided reports workflow."""
    
    click.echo("\n📊 Reports & Analytics")
    click.echo("-" * 30)
    
    options = [
        "Weekly productivity report",
        "Project summary",
        "Time analytics",
        "Export reports"
    ]
    
    for i, option in enumerate(options, 1):
        click.echo(f"{i}. {option}")
    
    choice = click.prompt("Select an option", type=click.IntRange(1, len(options)))
    
    # Implementation would call the appropriate report commands
    if choice == 1:
        from devos.commands.report import weekly
        weekly(ctx, None, 'table', None)
    elif choice == 2:
        from devos.commands.report import projects
        projects(ctx, 'table', None)
    elif choice == 3:
        from devos.commands.report import summary
        summary(ctx, None, 30, 'table', None)
    elif choice == 4:
        show_info("Export reports feature coming soon!")


def _release_workflow(ctx) -> None:
    """Guided release workflow."""
    
    click.echo("\n🚀 Release Management")
    click.echo("-" * 30)
    
    options = [
        "Create a new release",
        "View version history",
        "Generate changelog",
        "Preview release"
    ]
    
    for i, option in enumerate(options, 1):
        click.echo(f"{i}. {option}")
    
    choice = click.prompt("Select an option", type=click.IntRange(1, len(options)))
    
    # Implementation would call the appropriate ship commands
    if choice == 1:
        version_type = click.prompt("Release type", type=click.Choice(['patch', 'minor', 'major']), default='patch')
        from devos.commands.ship import release
        release(ctx, version_type, False, False, None)
    elif choice == 2:
        from devos.commands.ship import version
        version(ctx)
    elif choice == 3:
        from devos.commands.ship import changelog
        changelog(ctx, None, 'markdown', None)
    elif choice == 4:
        show_info("Preview release feature coming soon!")


def _config_workflow(ctx) -> None:
    """Guided configuration workflow."""
    
    click.echo("\n⚙️  Configuration")
    click.echo("-" * 30)
    
    options = [
        "View current configuration",
        "Set configuration value",
        "Reset configuration",
        "Initialize configuration"
    ]
    
    for i, option in enumerate(options, 1):
        click.echo(f"{i}. {option}")
    
    choice = click.prompt("Select an option", type=click.IntRange(1, len(options)))
    
    # Implementation would call the appropriate config commands
    if choice == 1:
        from devos.commands.config import show as config_show
        config_show(ctx, False)
    elif choice == 2:
        key = click.prompt("Configuration key")
        value = click.prompt("Configuration value")
        from devos.commands.config import set as config_set
        config_set(ctx, key, value, False)
    elif choice == 3:
        from devos.commands.config import reset as config_reset
        config_reset(ctx, False)
    elif choice == 4:
        from devos.commands.config import init as config_init
        config_init(ctx)


def _create_project_interactive(ctx) -> None:
    """Interactive project creation."""
    
    show_info("Creating a new project")
    
    name = click.prompt("Project name")
    language = click.prompt(
        "Programming language",
        type=click.Choice(['python', 'javascript', 'typescript', 'go', 'rust']),
        default='python'
    )
    
    project_types = {
        'python': ['basic', 'api', 'cli', 'web'],
        'javascript': ['basic', 'api', 'web', 'cli'],
        'typescript': ['basic', 'api', 'web', 'cli'],
        'go': ['basic', 'api', 'cli'],
        'rust': ['basic', 'cli', 'api']
    }
    
    project_type = click.prompt(
        "Project type",
        type=click.Choice(project_types.get(language, ['basic'])),
        default='basic'
    )
    
    path = click.prompt("Project path", default=f"./{name}")
    
    # Create the project
    from devos.commands.init import init
    init(ctx, f"{language}-{project_type}", name, path, language, False)
    
    show_success(f"Project '{name}' created successfully!")


def _list_projects_interactive(ctx) -> None:
    """List projects in interactive format."""
    
    from devos.core.database import Database
    db = ctx.obj['db']
    projects = db.list_projects()
    
    if not projects:
        show_warning("No projects found", "Create your first project with 'devos init'")
        return
    
    click.echo("\n📁 Your Projects:")
    click.echo("-" * 40)
    
    for i, project in enumerate(projects, 1):
        click.echo(f"{i}. {project['name']}")
        click.echo(f"   Language: {project['language']}")
        click.echo(f"   Path: {project['path']}")
        click.echo()


def _switch_project_interactive(ctx) -> None:
    """Switch to a different project."""
    
    show_info("Switch project feature coming soon!")
    show_info("For now, use 'cd' to navigate to your project directory")


def _delete_project_interactive(ctx) -> None:
    """Delete a project."""
    
    show_warning("Delete project feature coming soon!")
    show_info("This will be implemented with proper safety checks")
