"""
Task list widget for Anika.
"""
from datetime import datetime, date, time as dt_time
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QCheckBox, QMenu, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor, QCursor

from anika.models.task import Task


class TaskItemWidget(QFrame):
    """Widget representing a single task item."""
    
    completed_changed = Signal(int, bool)  # task_id, completed
    delete_requested = Signal(int)  # task_id
    edit_requested = Signal(int)  # task_id
    
    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setObjectName("taskItem")
        self.setup_ui()
        self.update_style()
    
    def setup_ui(self):
        """Setup the task item UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(12)
        
        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task.completed)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        self.checkbox.setObjectName("taskCheckbox")
        layout.addWidget(self.checkbox)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Title
        self.title_label = QLabel(self.task.title)
        self.title_label.setObjectName("taskTitle")
        self.title_label.setWordWrap(True)
        content_layout.addWidget(self.title_label)
        
        # Description (if exists)
        if self.task.description:
            self.desc_label = QLabel(self.task.description)
            self.desc_label.setObjectName("taskDescription")
            self.desc_label.setWordWrap(True)
            content_layout.addWidget(self.desc_label)
        
        # Due time
        time_layout = QHBoxLayout()
        time_layout.setSpacing(8)
        
        if self.task.due_time:
            time_str = self.task.due_time.strftime("%I:%M %p")
            self.time_label = QLabel(f"⏰ {time_str}")
            self.time_label.setObjectName("taskTime")
            time_layout.addWidget(self.time_label)
        
        # Overdue indicator
        if self.is_overdue():
            overdue_label = QLabel("⚠️ Overdue")
            overdue_label.setObjectName("taskOverdue")
            time_layout.addWidget(overdue_label)
        
        time_layout.addStretch()
        content_layout.addLayout(time_layout)
        
        layout.addLayout(content_layout, 1)
        
        # Action buttons
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(5)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setObjectName("taskActionBtn")
        edit_btn.setFixedSize(32, 32)
        edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.task.id))
        edit_btn.setToolTip("Edit task")
        actions_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setObjectName("taskActionBtn")
        delete_btn.setFixedSize(32, 32)
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.task.id))
        delete_btn.setToolTip("Delete task")
        actions_layout.addWidget(delete_btn)
        
        layout.addLayout(actions_layout)
    
    def is_overdue(self) -> bool:
        """Check if the task is overdue."""
        if self.task.completed:
            return False
        
        now = datetime.now()
        task_datetime = datetime.combine(self.task.due_date, self.task.due_time or dt_time(23, 59, 59))
        return now > task_datetime
    
    def on_checkbox_changed(self, state):
        """Handle checkbox state change."""
        completed = state == Qt.CheckState.Checked.value
        self.completed_changed.emit(self.task.id, completed)
    
    def update_style(self):
        """Update the widget style based on task state."""
        if self.task.completed:
            self.setProperty("state", "completed")
        elif self.is_overdue():
            self.setProperty("state", "overdue")
        else:
            self.setProperty("state", "normal")
        
        self.style().unpolish(self)
        self.style().polish(self)


class TaskListWidget(QWidget):
    """Widget displaying a list of tasks."""
    
    task_completed = Signal(int, bool)  # task_id, completed
    task_deleted = Signal(int)  # task_id
    task_edited = Signal(int)  # task_id
    add_task_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks: List[Task] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the task list UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Scroll area for tasks
        scroll = QScrollArea()
        scroll.setObjectName("taskScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container for task items
        self.container = QWidget()
        self.container.setObjectName("taskContainer")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 10, 0)
        self.container_layout.setSpacing(10)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Empty state
        self.empty_label = QLabel("No tasks for this day\n\nClick + to add a task")
        self.empty_label.setObjectName("emptyState")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        self.container_layout.addWidget(self.empty_label)
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll, 1)
        
        # Add task button
        add_btn = QPushButton("+ Add Task")
        add_btn.setObjectName("addTaskBtn")
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.clicked.connect(self.add_task_requested.emit)
        layout.addWidget(add_btn)
    
    def set_tasks(self, tasks: List[Task]):
        """Set the task list."""
        self.tasks = tasks
        self.refresh_display()
    
    def refresh_display(self):
        """Refresh the task display."""
        # Clear existing items (except empty label)
        for i in reversed(range(self.container_layout.count())):
            item = self.container_layout.itemAt(i)
            if item.widget() and item.widget() != self.empty_label:
                item.widget().deleteLater()
        
        if not self.tasks:
            self.empty_label.show()
            return
        
        self.empty_label.hide()
        
        # Sort tasks: incomplete first, then by time
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (t.completed, t.due_time or dt_time(23, 59, 59))
        )
        
        for task in sorted_tasks:
            item = TaskItemWidget(task)
            item.completed_changed.connect(self.task_completed.emit)
            item.delete_requested.connect(self.task_deleted.emit)
            item.edit_requested.connect(self.task_edited.emit)
            self.container_layout.addWidget(item)
        
        # Add stretch at the end
        self.container_layout.addStretch()
