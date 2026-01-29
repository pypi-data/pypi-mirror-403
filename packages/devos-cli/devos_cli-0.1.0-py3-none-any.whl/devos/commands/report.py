"""Productivity reporting command."""

import click
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

from devos.core.database import Database


@click.command()
@click.option('--project', '-p', help='Filter by project name or path')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'markdown']), default='table', help='Output format')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def weekly(ctx, project: Optional[str], format: str, output: Optional[str]):
    """Generate weekly productivity report."""
    
    config = ctx.obj['config']
    db = ctx.obj['db']
    
    # Find project if specified
    project_id = None
    project_name = None
    if project:
        project_id = _find_project(db, project)
        if not project_id:
            click.echo(f"Project '{project}' not found.", err=True)
            return
        
        project_info = db.get_project_by_id(project_id)
        project_name = project_info['name'] if project_info else 'Unknown'
    
    # Calculate week range
    week_start = _get_week_start(config.week_start).replace(tzinfo=datetime.now().astimezone().tzinfo)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    # Get sessions for the week
    sessions = db.list_sessions(project_id, limit=1000)
    week_sessions = []
    
    for session in sessions:
        session_date = datetime.fromisoformat(session['start_time'])
        if week_start <= session_date <= week_end:
            week_sessions.append(session)
    
    if not week_sessions:
        click.echo("No sessions found for this week.")
        return
    
    # Generate report
    report_data = _generate_weekly_report(week_sessions, week_start, project_name)
    
    # Output report
    if format == 'json':
        _output_json_report(report_data, output)
    elif format == 'markdown':
        _output_markdown_report(report_data, output, 'weekly')
    else:
        _output_table_report(report_data, output, 'weekly')


@click.command()
@click.option('--project', '-p', help='Filter by project name or path')
@click.option('--days', '-d', default=30, help='Number of days to include')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'markdown']), default='table', help='Output format')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def summary(ctx, project: Optional[str], days: int, format: str, output: Optional[str]):
    """Generate summary report for a time period."""
    
    config = ctx.obj['config']
    db = ctx.obj['db']
    
    # Find project if specified
    project_id = None
    project_name = None
    if project:
        project_id = _find_project(db, project)
        if not project_id:
            click.echo(f"Project '{project}' not found.", err=True)
            return
        
        project_info = db.get_project_by_id(project_id)
        project_name = project_info['name'] if project_info else 'Unknown'
    
    # Calculate date range
    end_date = datetime.now().astimezone()
    start_date = end_date - timedelta(days=days)
    
    # Get sessions for the period
    sessions = db.list_sessions(project_id, limit=1000)
    period_sessions = []
    
    for session in sessions:
        session_date = datetime.fromisoformat(session['start_time'])
        if start_date <= session_date <= end_date:
            period_sessions.append(session)
    
    if not period_sessions:
        click.echo(f"No sessions found in the last {days} days.")
        return
    
    # Generate report
    report_data = _generate_summary_report(period_sessions, start_date, end_date, project_name)
    
    # Output report
    if format == 'json':
        _output_json_report(report_data, output)
    elif format == 'markdown':
        _output_markdown_report(report_data, output, 'summary')
    else:
        _output_table_report(report_data, output, 'summary')


@click.command()
@click.option('--project', '-p', help='Filter by project name or path')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'markdown']), default='table', help='Output format')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def projects(ctx, project: Optional[str], format: str, output: Optional[str]):
    """Generate project breakdown report."""
    
    db = ctx.obj['db']
    
    # Get all projects
    projects = db.list_projects()
    
    if not projects:
        click.echo("No projects found.")
        return
    
    # Generate report data
    report_data = _generate_projects_report(projects, db)
    
    # Output report
    if format == 'json':
        _output_json_report(report_data, output)
    elif format == 'markdown':
        _output_markdown_report(report_data, output, 'projects')
    else:
        _output_table_report(report_data, output, 'projects')


def _get_week_start(week_start_day: str) -> datetime:
    """Get the start of the current week."""
    today = datetime.now().date()
    
    # Map day names to weekday numbers (Monday=0, Sunday=6)
    day_map = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    
    target_weekday = day_map.get(week_start_day.lower(), 0)
    current_weekday = today.weekday()
    
    # Calculate days to go back
    days_back = (current_weekday - target_weekday) % 7
    week_start_date = today - timedelta(days=days_back)
    
    return datetime.combine(week_start_date, datetime.min.time()).replace(tzinfo=datetime.now().astimezone().tzinfo)


def _generate_weekly_report(sessions: List[Dict], week_start: datetime, project_name: Optional[str]) -> Dict[str, Any]:
    """Generate weekly report data."""
    
    # Group sessions by day
    daily_stats = {}
    total_seconds = 0
    
    for session in sessions:
        session_date = datetime.fromisoformat(session['start_time']).date()
        day_key = session_date.strftime('%Y-%m-%d')
        
        if day_key not in daily_stats:
            daily_stats[day_key] = {
                'date': session_date,
                'sessions': 0,
                'seconds': 0,
                'project_names': set()
            }
        
        daily_stats[day_key]['sessions'] += 1
        
        if session['duration']:
            daily_stats[day_key]['seconds'] += session['duration']
            total_seconds += session['duration']
        
        daily_stats[day_key]['project_names'].add(session.get('project_name', 'Unknown'))
    
    # Calculate totals
    total_sessions = len(sessions)
    total_hours = total_seconds / 3600
    
    # Format daily stats
    daily_data = []
    for day_key in sorted(daily_stats.keys()):
        stats = daily_stats[day_key]
        hours = stats['seconds'] / 3600
        daily_data.append({
            'date': stats['date'].strftime('%Y-%m-%d (%A)'),
            'sessions': stats['sessions'],
            'hours': round(hours, 2),
            'projects': len(stats['project_names'])
        })
    
    return {
        'type': 'weekly',
        'period': f"{week_start.strftime('%Y-%m-%d')} to {(week_start + timedelta(days=6)).strftime('%Y-%m-%d')}",
        'project': project_name,
        'total_sessions': total_sessions,
        'total_hours': round(total_hours, 2),
        'daily_breakdown': daily_data,
        'generated_at': datetime.now().isoformat()
    }


def _generate_summary_report(sessions: List[Dict], start_date: datetime, end_date: datetime, project_name: Optional[str]) -> Dict[str, Any]:
    """Generate summary report data."""
    
    # Calculate totals
    total_sessions = len(sessions)
    total_seconds = sum(s.get('duration', 0) for s in sessions if s['duration'])
    total_hours = total_seconds / 3600
    
    # Group by project
    project_stats = {}
    for session in sessions:
        project_name_key = session.get('project_name', 'Unknown')
        if project_name_key not in project_stats:
            project_stats[project_name_key] = {
                'sessions': 0,
                'seconds': 0
            }
        
        project_stats[project_name_key]['sessions'] += 1
        if session['duration']:
            project_stats[project_name_key]['seconds'] += session['duration']
    
    # Format project breakdown
    project_breakdown = []
    for proj_name, stats in project_stats.items():
        hours = stats['seconds'] / 3600
        project_breakdown.append({
            'project': proj_name,
            'sessions': stats['sessions'],
            'hours': round(hours, 2),
            'percentage': round((stats['seconds'] / total_seconds * 100) if total_seconds > 0 else 0, 1)
        })
    
    # Sort by hours
    project_breakdown.sort(key=lambda x: x['hours'], reverse=True)
    
    return {
        'type': 'summary',
        'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        'project': project_name,
        'total_sessions': total_sessions,
        'total_hours': round(total_hours, 2),
        'project_breakdown': project_breakdown,
        'generated_at': datetime.now().isoformat()
    }


def _generate_projects_report(projects: List[Dict], db: Database) -> Dict[str, Any]:
    """Generate projects report data."""
    
    project_data = []
    
    for project in projects:
        # Get sessions for this project
        sessions = db.list_sessions(project['id'], limit=1000)
        
        # Calculate stats
        total_sessions = len(sessions)
        total_seconds = sum(s.get('duration', 0) for s in sessions if s['duration'])
        total_hours = total_seconds / 3600
        
        # Get last activity
        last_activity = None
        if sessions:
            last_session = max(sessions, key=lambda x: x['start_time'])
            last_activity = last_session['start_time']
        
        project_data.append({
            'name': project['name'],
            'language': project['language'],
            'path': project['path'],
            'created_at': project['created_at'],
            'total_sessions': total_sessions,
            'total_hours': round(total_hours, 2),
            'last_activity': last_activity
        })
    
    # Sort by total hours
    project_data.sort(key=lambda x: x['total_hours'], reverse=True)
    
    return {
        'type': 'projects',
        'total_projects': len(projects),
        'projects': project_data,
        'generated_at': datetime.now().isoformat()
    }


def _output_table_report(report_data: Dict[str, Any], output: Optional[str], report_type: str):
    """Output report in table format."""
    
    lines = []
    
    if report_type == 'weekly':
        lines.append(f"Weekly Report: {report_data['period']}")
        if report_data['project']:
            lines.append(f"Project: {report_data['project']}")
        lines.append(f"Total Sessions: {report_data['total_sessions']}")
        lines.append(f"Total Hours: {report_data['total_hours']}")
        lines.append("")
        lines.append("Daily Breakdown:")
        lines.append("-" * 50)
        lines.append(f"{'Date':<20} {'Sessions':<10} {'Hours':<10} {'Projects':<10}")
        
        for day in report_data['daily_breakdown']:
            lines.append(f"{day['date']:<20} {day['sessions']:<10} {day['hours']:<10} {day['projects']:<10}")
    
    elif report_type == 'summary':
        lines.append(f"Summary Report: {report_data['period']}")
        if report_data['project']:
            lines.append(f"Project: {report_data['project']}")
        lines.append(f"Total Sessions: {report_data['total_sessions']}")
        lines.append(f"Total Hours: {report_data['total_hours']}")
        lines.append("")
        lines.append("Project Breakdown:")
        lines.append("-" * 60)
        lines.append(f"{'Project':<20} {'Sessions':<10} {'Hours':<10} {'Percentage':<10}")
        
        for proj in report_data['project_breakdown']:
            lines.append(f"{proj['project']:<20} {proj['sessions']:<10} {proj['hours']:<10} {proj['percentage']}%")
    
    elif report_type == 'projects':
        lines.append(f"Projects Report ({report_data['total_projects']} projects)")
        lines.append("")
        lines.append("-" * 80)
        lines.append(f"{'Project':<20} {'Language':<10} {'Sessions':<10} {'Hours':<10} {'Last Activity':<20}")
        
        for proj in report_data['projects']:
            last_activity = proj['last_activity']
            if last_activity:
                last_activity = datetime.fromisoformat(last_activity).strftime('%Y-%m-%d')
            else:
                last_activity = 'Never'
            
            lines.append(f"{proj['name']:<20} {proj['language']:<10} {proj['total_sessions']:<10} {proj['total_hours']:<10} {last_activity:<20}")
    
    content = "\n".join(lines)
    
    if output:
        Path(output).write_text(content)
        click.echo(f"Report saved to {output}")
    else:
        click.echo(content)


def _output_json_report(report_data: Dict[str, Any], output: Optional[str]):
    """Output report in JSON format."""
    
    content = json.dumps(report_data, indent=2, default=str)
    
    if output:
        Path(output).write_text(content)
        click.echo(f"Report saved to {output}")
    else:
        click.echo(content)


def _output_markdown_report(report_data: Dict[str, Any], output: Optional[str], report_type: str):
    """Output report in Markdown format."""
    
    lines = []
    
    if report_type == 'weekly':
        lines.append(f"# Weekly Report")
        lines.append(f"**Period:** {report_data['period']}")
        if report_data['project']:
            lines.append(f"**Project:** {report_data['project']}")
        lines.append(f"**Total Sessions:** {report_data['total_sessions']}")
        lines.append(f"**Total Hours:** {report_data['total_hours']}")
        lines.append("")
        lines.append("## Daily Breakdown")
        lines.append("")
        lines.append("| Date | Sessions | Hours | Projects |")
        lines.append("|------|----------|-------|----------|")
        
        for day in report_data['daily_breakdown']:
            lines.append(f"| {day['date']} | {day['sessions']} | {day['hours']} | {day['projects']} |")
    
    elif report_type == 'summary':
        lines.append(f"# Summary Report")
        lines.append(f"**Period:** {report_data['period']}")
        if report_data['project']:
            lines.append(f"**Project:** {report_data['project']}")
        lines.append(f"**Total Sessions:** {report_data['total_sessions']}")
        lines.append(f"**Total Hours:** {report_data['total_hours']}")
        lines.append("")
        lines.append("## Project Breakdown")
        lines.append("")
        lines.append("| Project | Sessions | Hours | Percentage |")
        lines.append("|---------|----------|-------|------------|")
        
        for proj in report_data['project_breakdown']:
            lines.append(f"| {proj['project']} | {proj['sessions']} | {proj['hours']} | {proj['percentage']}% |")
    
    elif report_type == 'projects':
        lines.append(f"# Projects Report")
        lines.append(f"**Total Projects:** {report_data['total_projects']}")
        lines.append("")
        lines.append("| Project | Language | Sessions | Hours | Last Activity |")
        lines.append("|---------|----------|----------|-------|---------------|")
        
        for proj in report_data['projects']:
            last_activity = proj['last_activity']
            if last_activity:
                last_activity = datetime.fromisoformat(last_activity).strftime('%Y-%m-%d')
            else:
                last_activity = 'Never'
            
            lines.append(f"| {proj['name']} | {proj['language']} | {proj['total_sessions']} | {proj['total_hours']} | {last_activity} |")
    
    content = "\n".join(lines)
    
    if output:
        Path(output).write_text(content)
        click.echo(f"Report saved to {output}")
    else:
        click.echo(content)


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
