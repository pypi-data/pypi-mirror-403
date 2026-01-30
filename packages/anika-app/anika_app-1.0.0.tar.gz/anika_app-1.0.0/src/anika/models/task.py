"""
Task data model for Anika.
"""
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import Optional


@dataclass
class Task:
    """Represents a task in the to-do system."""
    
    id: int
    title: str
    due_date: date
    description: Optional[str] = None
    due_time: Optional[time] = None
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_overdue(self) -> bool:
        """Check if the task is overdue."""
        if self.completed:
            return False
        
        now = datetime.now()
        task_datetime = datetime.combine(
            self.due_date, 
            self.due_time or time(23, 59, 59)
        )
        return now > task_datetime
    
    def __repr__(self) -> str:
        status = "✓" if self.completed else "○"
        return f"Task({status} {self.title}, due: {self.due_date})"
