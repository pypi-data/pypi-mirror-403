"""Database layer for DevOS using SQLite."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from devos.core.config import Config


class Database:
    """SQLite database manager for DevOS."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize database connection."""
        self.config = config or Config()
        self.db_path = self.config.data_dir / "devos.db"
        self._ensure_database()
        self._init_schema()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def close(self):
        """Close database resources."""
        # SQLite connections are managed by context managers in individual methods
        # This method is for explicit cleanup and future connection pooling
        pass
    
    def _ensure_database(self):
        """Ensure database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_schema(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL UNIQUE,
                    language TEXT NOT NULL,
                    type TEXT DEFAULT 'web',
                    description TEXT,
                    tags TEXT, -- JSON array
                    status TEXT DEFAULT 'active',
                    metadata TEXT, -- JSON for tasks, issues, notes
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add new columns to existing projects table if they don't exist
            try:
                conn.execute("ALTER TABLE projects ADD COLUMN type TEXT DEFAULT 'web'")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                conn.execute("ALTER TABLE projects ADD COLUMN description TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                conn.execute("ALTER TABLE projects ADD COLUMN tags TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                conn.execute("ALTER TABLE projects ADD COLUMN status TEXT DEFAULT 'active'")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                conn.execute("ALTER TABLE projects ADD COLUMN metadata TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS env_vars (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    key TEXT NOT NULL,
                    encrypted_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    UNIQUE(project_id, key)
                )
            """)
            
            conn.commit()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a query and return results."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an update query and return affected rows."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = ()) -> str:
        """Execute an insert query and return the last row ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return str(cursor.lastrowid)
    
    # Project methods
    def create_project(self, project_id: str, name: str, path: str, language: str) -> str:
        """Create a new project."""
        self.execute_insert(
            "INSERT INTO projects (id, name, path, language) VALUES (?, ?, ?, ?)",
            (project_id, name, path, language)
        )
        return project_id
    
    def get_project_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get project by path."""
        rows = self.execute_query(
            "SELECT * FROM projects WHERE path = ?",
            (path,)
        )
        return dict(rows[0]) if rows else None
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        rows = self.execute_query(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        return dict(rows[0]) if rows else None
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        rows = self.execute_query("SELECT * FROM projects ORDER BY created_at DESC")
        return [dict(row) for row in rows]
    
    # Session methods
    def create_session(self, session_id: str, project_id: str, start_time: datetime) -> str:
        """Create a new session."""
        self.execute_insert(
            "INSERT INTO sessions (id, project_id, start_time) VALUES (?, ?, ?)",
            (session_id, project_id, start_time.isoformat())
        )
        return session_id
    
    def end_session(self, session_id: str, end_time: datetime, notes: str = "") -> bool:
        """End a session and calculate duration."""
        start_rows = self.execute_query(
            "SELECT start_time FROM sessions WHERE id = ? AND end_time IS NULL",
            (session_id,)
        )
        
        if not start_rows:
            return False
        
        start_time = datetime.fromisoformat(start_rows[0]['start_time'])
        duration = int((end_time - start_time).total_seconds())
        
        self.execute_update(
            "UPDATE sessions SET end_time = ?, duration = ?, notes = ? WHERE id = ?",
            (end_time.isoformat(), duration, notes, session_id)
        )
        return True
    
    def get_active_session(self, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get currently active session."""
        query = "SELECT * FROM sessions WHERE end_time IS NULL"
        params = ()
        
        if project_id:
            query += " AND project_id = ?"
            params = (project_id,)
        
        rows = self.execute_query(query, params)
        return dict(rows[0]) if rows else None
    
    def list_sessions(self, project_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List sessions."""
        query = """
            SELECT s.*, p.name as project_name 
            FROM sessions s 
            LEFT JOIN projects p ON s.project_id = p.id
        """
        params = []
        
        if project_id:
            query += " WHERE s.project_id = ?"
            params.append(project_id)
        
        query += " ORDER BY s.start_time DESC LIMIT ?"
        params.append(limit)
        
        rows = self.execute_query(query, tuple(params))
        return [dict(row) for row in rows]
    
    # Environment variable methods
    def set_env_var(self, env_id: str, project_id: Optional[str], key: str, encrypted_value: str) -> str:
        """Set an environment variable."""
        # Use INSERT OR REPLACE to handle uniqueness constraint
        self.execute_insert(
            """
            INSERT OR REPLACE INTO env_vars (id, project_id, key, encrypted_value, updated_at) 
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (env_id, project_id, key, encrypted_value)
        )
        return env_id
    
    def get_env_var(self, project_id: Optional[str], key: str) -> Optional[Dict[str, Any]]:
        """Get an environment variable."""
        query = "SELECT * FROM env_vars WHERE key = ?"
        params = [key]
        
        if project_id:
            query += " AND (project_id = ? OR project_id IS NULL)"
            params.append(project_id)
        else:
            query += " AND project_id IS NULL"
        
        rows = self.execute_query(query, tuple(params))
        return dict(rows[0]) if rows else None
    
    def list_env_vars(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List environment variables."""
        query = "SELECT * FROM env_vars"
        params = []
        
        if project_id:
            query += " WHERE project_id = ? OR project_id IS NULL"
            params.append(project_id)
        else:
            query += " WHERE project_id IS NULL"
        
        query += " ORDER BY key"
        
        rows = self.execute_query(query, tuple(params))
        return [dict(row) for row in rows]
    
    def delete_env_var(self, project_id: Optional[str], key: str) -> bool:
        """Delete an environment variable."""
        query = "DELETE FROM env_vars WHERE key = ?"
        params = [key]
        
        if project_id:
            query += " AND (project_id = ? OR project_id IS NULL)"
            params.append(project_id)
        else:
            query += " AND project_id IS NULL"
        
        affected = self.execute_update(query, tuple(params))
        return affected > 0
    
    # Enhanced project management methods
    def add_project(self, project_data: Dict[str, Any]) -> str:
        """Add a new project with full metadata."""
        import uuid
        
        project_id = str(uuid.uuid4())
        metadata = {
            'tasks': project_data.get('tasks', []),
            'issues': project_data.get('issues', []),
            'notes': project_data.get('notes', [])
        }
        
        self.execute_insert(
            """
            INSERT INTO projects (id, name, path, language, type, description, tags, status, metadata) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                project_data['name'],
                project_data.get('path', ''),
                project_data.get('language', 'unknown'),
                project_data.get('type', 'web'),
                project_data.get('description', ''),
                json.dumps(project_data.get('tags', [])),
                project_data.get('status', 'active'),
                json.dumps(metadata)
            )
        )
        return project_id
    
    def get_project(self, name: str) -> Optional[Dict[str, Any]]:
        """Get project by name."""
        rows = self.execute_query(
            "SELECT * FROM projects WHERE name = ?",
            (name,)
        )
        
        if not rows:
            return None
        
        project = dict(rows[0])
        
        # Parse JSON fields
        if project.get('tags'):
            project['tags'] = json.loads(project['tags'])
        else:
            project['tags'] = []
            
        if project.get('metadata'):
            metadata = json.loads(project['metadata'])
            project['tasks'] = metadata.get('tasks', [])
            project['issues'] = metadata.get('issues', [])
            project['notes'] = metadata.get('notes', [])
        else:
            project['tasks'] = []
            project['issues'] = []
            project['notes'] = []
        
        return project
    
    def get_projects(self, type_filter: Optional[str] = None, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get projects with optional filters."""
        query = "SELECT * FROM projects"
        params = []
        
        conditions = []
        if type_filter:
            conditions.append("type = ?")
            params.append(type_filter)
        
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        rows = self.execute_query(query, tuple(params))
        projects = []
        
        for row in rows:
            project = dict(row)
            
            # Parse JSON fields
            if project.get('tags'):
                project['tags'] = json.loads(project['tags'])
            else:
                project['tags'] = []
                
            if project.get('metadata'):
                metadata = json.loads(project['metadata'])
                project['tasks'] = metadata.get('tasks', [])
                project['issues'] = metadata.get('issues', [])
                project['notes'] = metadata.get('notes', [])
            else:
                project['tasks'] = []
                project['issues'] = []
                project['notes'] = []
            
            projects.append(project)
        
        return projects
    
    def add_project_task(self, project_name: str, task_data: Dict[str, Any]) -> bool:
        """Add a task to a project."""
        project = self.get_project(project_name)
        if not project:
            return False
        
        project['tasks'].append(task_data)
        return self._update_project_metadata(project_name, project)
    
    def complete_project_task(self, project_name: str, task_title: str) -> bool:
        """Mark a task as complete."""
        project = self.get_project(project_name)
        if not project:
            return False
        
        for task in project['tasks']:
            if task['title'] == task_title:
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
                return self._update_project_metadata(project_name, project)
        
        return False
    
    def add_project_issue(self, project_name: str, issue_data: Dict[str, Any]) -> bool:
        """Add an issue to a project."""
        project = self.get_project(project_name)
        if not project:
            return False
        
        project['issues'].append(issue_data)
        return self._update_project_metadata(project_name, project)
    
    def resolve_project_issue(self, project_name: str, issue_title: str) -> bool:
        """Mark an issue as resolved."""
        project = self.get_project(project_name)
        if not project:
            return False
        
        for issue in project['issues']:
            if issue['title'] == issue_title:
                issue['status'] = 'resolved'
                issue['resolved_at'] = datetime.now().isoformat()
                return self._update_project_metadata(project_name, project)
        
        return False
    
    def add_project_note(self, project_name: str, note_data: Dict[str, Any]) -> bool:
        """Add a note to a project."""
        project = self.get_project(project_name)
        if not project:
            return False
        
        project['notes'].append(note_data)
        return self._update_project_metadata(project_name, project)
    
    def delete_project_note(self, project_name: str, note_content: str) -> bool:
        """Delete a note from a project."""
        project = self.get_project(project_name)
        if not project:
            return False
        
        project['notes'] = [note for note in project['notes'] if note['content'] != note_content]
        return self._update_project_metadata(project_name, project)
    
    def _update_project_metadata(self, project_name: str, project: Dict[str, Any]) -> bool:
        """Update project metadata."""
        metadata = {
            'tasks': project['tasks'],
            'issues': project['issues'],
            'notes': project['notes']
        }
        
        affected = self.execute_update(
            "UPDATE projects SET metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE name = ?",
            (json.dumps(metadata), project_name)
        )
        
        return affected > 0
