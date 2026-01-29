"""Project management commands."""

import click
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from devos.core.database import Database
from devos.core.progress import show_success, show_info, show_warning, show_operation_status, ProgressBar


@click.command()
@click.argument('name')
@click.option('--type', type=click.Choice(['web', 'api', 'mobile', 'desktop', 'cli', 'library']), default='web', help='Project type')
@click.option('--description', help='Project description')
@click.option('--tags', help='Project tags (comma-separated)')
@click.pass_context
def add(ctx, name: str, type: str, description: Optional[str], tags: Optional[str]):
    """Add a new project to track."""
    
    db = ctx.obj['db']
    
    project_data = {
        'name': name,
        'type': type,
        'description': description or '',
        'tags': tags.split(',') if tags else [],
        'created_at': datetime.now().isoformat(),
        'status': 'active',
        'tasks': [],
        'issues': [],
        'notes': []
    }
    
    try:
        db.add_project(project_data)
        show_success(f"Project '{name}' added successfully!")
        
        # Show project summary
        click.echo(f"\n📋 Project Summary:")
        click.echo(f"   Name: {name}")
        click.echo(f"   Type: {type}")
        if description:
            click.echo(f"   Description: {description}")
        if tags:
            click.echo(f"   Tags: {', '.join(tags.split(','))}")
        
    except Exception as e:
        show_operation_status(f"Failed to add project: {e}", False)


@click.command()
@click.option('--type', help='Filter by project type')
@click.option('--status', type=click.Choice(['active', 'completed', 'archived']), help='Filter by status')
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def list(ctx, type: Optional[str], status: Optional[str], format: str):
    """List all projects."""
    
    db = ctx.obj['db']
    
    try:
        projects = db.get_projects(type_filter=type, status_filter=status)
        
        if not projects:
            show_info("No projects found")
            return
        
        if format == 'json':
            click.echo(json.dumps(projects, indent=2, default=str))
        else:
            _display_projects_table(projects)
            
    except Exception as e:
        show_operation_status(f"Failed to list projects: {e}", False)


@click.command()
@click.argument('name')
@click.pass_context
def status(ctx, name: str):
    """Show detailed project status."""
    
    db = ctx.obj['db']
    
    try:
        project = db.get_project(name)
        
        if not project:
            show_warning(f"Project '{name}' not found")
            return
        
        _display_project_status(project)
        
    except Exception as e:
        show_operation_status(f"Failed to get project status: {e}", False)


@click.command()
@click.argument('project_name')
@click.option('--add', help='Add a new task')
@click.option('--list', 'list_tasks', is_flag=True, help='List all tasks')
@click.option('--complete', help='Mark task as complete')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high']), help='Task priority')
@click.pass_context
def tasks(ctx, project_name: str, add: Optional[str], list_tasks: bool, complete: Optional[str], priority: Optional[str]):
    """Manage project tasks."""
    
    db = ctx.obj['db']
    
    try:
        project = db.get_project(project_name)
        
        if not project:
            show_warning(f"Project '{project_name}' not found")
            return
        
        if add:
            task_data = {
                'title': add,
                'priority': priority or 'medium',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'completed_at': None
            }
            
            db.add_project_task(project_name, task_data)
            show_success(f"Task '{add}' added to project '{project_name}'")
            
        elif complete:
            db.complete_project_task(project_name, complete)
            show_success(f"Task '{complete}' marked as complete")
            
        elif list_tasks:
            _display_project_tasks(project)
            
        else:
            _display_project_tasks(project)
            
    except Exception as e:
        show_operation_status(f"Failed to manage tasks: {e}", False)


@click.command()
@click.argument('project_name')
@click.option('--add', help='Add a new issue')
@click.option('--list', 'list_issues', is_flag=True, help='List all issues')
@click.option('--resolve', help='Mark issue as resolved')
@click.option('--severity', type=click.Choice(['low', 'medium', 'high', 'critical']), help='Issue severity')
@click.pass_context
def issues(ctx, project_name: str, add: Optional[str], list_issues: bool, resolve: Optional[str], severity: Optional[str]):
    """Manage project issues."""
    
    db = ctx.obj['db']
    
    try:
        project = db.get_project(project_name)
        
        if not project:
            show_warning(f"Project '{project_name}' not found")
            return
        
        if add:
            issue_data = {
                'title': add,
                'severity': severity or 'medium',
                'status': 'open',
                'created_at': datetime.now().isoformat(),
                'resolved_at': None
            }
            
            db.add_project_issue(project_name, issue_data)
            show_success(f"Issue '{add}' added to project '{project_name}'")
            
        elif resolve:
            db.resolve_project_issue(project_name, resolve)
            show_success(f"Issue '{resolve}' marked as resolved")
            
        elif list_issues:
            _display_project_issues(project)
            
        else:
            _display_project_issues(project)
            
    except Exception as e:
        show_operation_status(f"Failed to manage issues: {e}", False)


@click.command()
@click.argument('project_name')
@click.option('--add', help='Add a new note')
@click.option('--list', 'list_notes', is_flag=True, help='List all notes')
@click.option('--delete', help='Delete a note')
@click.pass_context
def notes(ctx, project_name: str, add: Optional[str], list_notes: bool, delete: Optional[str]):
    """Manage project notes."""
    
    db = ctx.obj['db']
    
    try:
        project = db.get_project(project_name)
        
        if not project:
            show_warning(f"Project '{project_name}' not found")
            return
        
        if add:
            note_data = {
                'content': add,
                'created_at': datetime.now().isoformat()
            }
            
            db.add_project_note(project_name, note_data)
            show_success(f"Note added to project '{project_name}'")
            
        elif delete:
            db.delete_project_note(project_name, delete)
            show_success(f"Note deleted from project '{project_name}'")
            
        elif list_notes:
            _display_project_notes(project)
            
        else:
            _display_project_notes(project)
            
    except Exception as e:
        show_operation_status(f"Failed to manage notes: {e}", False)


def _display_projects_table(projects: List[Dict[str, Any]]) -> None:
    """Display projects in table format."""
    
    click.echo("\n📋 Projects")
    click.echo("-" * 80)
    click.echo(f"{'Name':<20} {'Type':<10} {'Status':<10} {'Tasks':<8} {'Issues':<8} {'Created':<12}")
    click.echo("-" * 80)
    
    for project in projects:
        name = project['name'][:18] + '..' if len(project['name']) > 20 else project['name']
        type_str = project['type'][:8] + '..' if len(project['type']) > 10 else project['type']
        status = project['status'][:8] + '..' if len(project['status']) > 10 else project['status']
        
        task_count = len(project.get('tasks', []))
        issue_count = len(project.get('issues', []))
        
        created = project['created_at'][:10] if project.get('created_at') else 'Unknown'
        
        click.echo(f"{name:<20} {type_str:<10} {status:<10} {task_count:<8} {issue_count:<8} {created:<12}")


def _display_project_status(project: Dict[str, Any]) -> None:
    """Display detailed project status."""
    
    click.echo(f"\n📊 Project Status: {project['name']}")
    click.echo("=" * 50)
    
    click.echo(f"Type: {project['type']}")
    click.echo(f"Status: {project['status']}")
    click.echo(f"Created: {project['created_at'][:10] if project.get('created_at') else 'Unknown'}")
    
    if project.get('description'):
        click.echo(f"\nDescription: {project['description']}")
    
    if project.get('tags'):
        click.echo(f"Tags: {', '.join(project['tags'])}")
    
    # Summary stats
    task_count = len(project.get('tasks', []))
    completed_tasks = len([t for t in project.get('tasks', []) if t.get('status') == 'completed'])
    issue_count = len(project.get('issues', []))
    open_issues = len([i for i in project.get('issues', []) if i.get('status') == 'open'])
    note_count = len(project.get('notes', []))
    
    click.echo(f"\n📈 Summary:")
    click.echo(f"   Tasks: {completed_tasks}/{task_count} completed")
    click.echo(f"   Issues: {open_issues}/{issue_count} open")
    click.echo(f"   Notes: {note_count}")
    
    # Recent activity
    click.echo(f"\n🕐 Recent Activity:")
    recent_items = []
    
    for task in project.get('tasks', [])[-3:]:
        recent_items.append(f"Task: {task['title']} ({task['status']})")
    
    for issue in project.get('issues', [])[-3:]:
        recent_items.append(f"Issue: {issue['title']} ({issue['status']})")
    
    for note in project.get('notes', [])[-3:]:
        recent_items.append(f"Note: {note['content'][:50]}...")
    
    if recent_items:
        for item in recent_items[-5:]:  # Show last 5 items
            click.echo(f"   • {item}")
    else:
        click.echo("   No recent activity")


def _display_project_tasks(project: Dict[str, Any]) -> None:
    """Display project tasks."""
    
    tasks = project.get('tasks', [])
    
    if not tasks:
        show_info("No tasks found")
        return
    
    click.echo(f"\n📝 Tasks for {project['name']}")
    click.echo("-" * 60)
    
    # Group by status
    pending_tasks = [t for t in tasks if t.get('status') == 'pending']
    completed_tasks = [t for t in tasks if t.get('status') == 'completed']
    
    if pending_tasks:
        click.echo(f"\n⏳ Pending ({len(pending_tasks)}):")
        for task in pending_tasks:
            priority_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(task.get('priority', 'medium'), '⚪')
            click.echo(f"  {priority_emoji} {task['title']}")
    
    if completed_tasks:
        click.echo(f"\n✅ Completed ({len(completed_tasks)}):")
        for task in completed_tasks:
            click.echo(f"  ✅ {task['title']}")


def _display_project_issues(project: Dict[str, Any]) -> None:
    """Display project issues."""
    
    issues = project.get('issues', [])
    
    if not issues:
        show_info("No issues found")
        return
    
    click.echo(f"\n🐛 Issues for {project['name']}")
    click.echo("-" * 60)
    
    # Group by status
    open_issues = [i for i in issues if i.get('status') == 'open']
    resolved_issues = [i for i in issues if i.get('status') == 'resolved']
    
    if open_issues:
        click.echo(f"\n🔴 Open ({len(open_issues)}):")
        for issue in open_issues:
            severity_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴', 'critical': '🚨'}.get(issue.get('severity', 'medium'), '⚪')
            click.echo(f"  {severity_emoji} {issue['title']}")
    
    if resolved_issues:
        click.echo(f"\n✅ Resolved ({len(resolved_issues)}):")
        for issue in resolved_issues:
            click.echo(f"  ✅ {issue['title']}")


def _display_project_notes(project: Dict[str, Any]) -> None:
    """Display project notes."""
    
    notes = project.get('notes', [])
    
    if not notes:
        show_info("No notes found")
        return
    
    click.echo(f"\n📝 Notes for {project['name']}")
    click.echo("-" * 60)
    
    for i, note in enumerate(notes, 1):
        created = note.get('created_at', 'Unknown')[:10]
        content = note.get('content', '')
        
        click.echo(f"\n{i}. {created}")
        click.echo(f"   {content}")
