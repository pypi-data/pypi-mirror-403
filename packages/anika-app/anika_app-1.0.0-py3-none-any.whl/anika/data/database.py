"""
Database operations for Anika.

Uses SQLite for local data persistence.
"""
import sqlite3
import os
from datetime import date, time, datetime
from typing import List, Optional
from contextlib import contextmanager

from anika.models.task import Task
from anika.main import get_app_data_dir


class Database:
    """SQLite database manager for Anika."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database.
        
        Args:
            db_path: Optional custom database path. If not provided,
                     uses the default app data directory.
        """
        if db_path:
            self.db_path = db_path
        else:
            app_data = get_app_data_dir()
            os.makedirs(app_data, exist_ok=True)
            self.db_path = os.path.join(app_data, "anika.db")
        
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT NOT NULL,
                    due_time TEXT,
                    completed INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert a database row to a Task object."""
        due_time = None
        if row['due_time']:
            time_parts = row['due_time'].split(':')
            due_time = time(int(time_parts[0]), int(time_parts[1]))
        
        return Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            due_date=date.fromisoformat(row['due_date']),
            due_time=due_time,
            completed=bool(row['completed']),
            created_at=datetime.fromisoformat(row['created_at'])
        )
    
    def create_task(
        self,
        title: str,
        due_date: date,
        description: Optional[str] = None,
        due_time: Optional[time] = None
    ) -> Task:
        """Create a new task.
        
        Args:
            title: Task title
            due_date: Due date
            description: Optional description
            due_time: Optional due time
        
        Returns:
            The created Task object
        """
        created_at = datetime.now()
        due_time_str = due_time.strftime("%H:%M") if due_time else None
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, description, due_date, due_time, completed, created_at)
                VALUES (?, ?, ?, ?, 0, ?)
                """,
                (title, description, due_date.isoformat(), due_time_str, created_at.isoformat())
            )
            conn.commit()
            task_id = cursor.lastrowid
        
        return Task(
            id=task_id,
            title=title,
            description=description,
            due_date=due_date,
            due_time=due_time,
            completed=False,
            created_at=created_at
        )
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID.
        
        Args:
            task_id: The task ID
        
        Returns:
            The Task object or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_task(row)
            return None
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks.
        
        Returns:
            List of all Task objects
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tasks ORDER BY due_date, due_time"
            )
            return [self._row_to_task(row) for row in cursor.fetchall()]
    
    def get_tasks_by_date(self, target_date: date) -> List[Task]:
        """Get tasks for a specific date.
        
        Args:
            target_date: The date to filter by
        
        Returns:
            List of Task objects for that date
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE due_date = ? ORDER BY due_time",
                (target_date.isoformat(),)
            )
            return [self._row_to_task(row) for row in cursor.fetchall()]
    
    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[date] = None,
        due_time: Optional[time] = None,
        completed: Optional[bool] = None
    ) -> bool:
        """Update a task.
        
        Args:
            task_id: The task ID to update
            title: New title (optional)
            description: New description (optional)
            due_date: New due date (optional)
            due_time: New due time (optional)
            completed: New completed status (optional)
        
        Returns:
            True if the task was updated, False otherwise
        """
        # Build update query dynamically
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date.isoformat())
        
        if due_time is not None:
            updates.append("due_time = ?")
            params.append(due_time.strftime("%H:%M"))
        
        if completed is not None:
            updates.append("completed = ?")
            params.append(1 if completed else 0)
        
        if not updates:
            return False
        
        params.append(task_id)
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task.
        
        Args:
            task_id: The task ID to delete
        
        Returns:
            True if the task was deleted, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM tasks WHERE id = ?",
                (task_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_incomplete_tasks(self) -> List[Task]:
        """Get all incomplete tasks.
        
        Returns:
            List of incomplete Task objects
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE completed = 0 ORDER BY due_date, due_time"
            )
            return [self._row_to_task(row) for row in cursor.fetchall()]
    
    def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks.
        
        Returns:
            List of overdue Task objects
        """
        tasks = self.get_incomplete_tasks()
        return [task for task in tasks if task.is_overdue()]
