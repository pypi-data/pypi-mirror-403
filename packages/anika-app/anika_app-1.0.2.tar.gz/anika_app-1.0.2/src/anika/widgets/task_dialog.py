"""
Task dialog for creating and editing tasks.
"""
from datetime import date, time as dt_time, datetime
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QDateEdit, QTimeEdit, QPushButton, QCheckBox,
    QFrame, QWidget
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QFont, QCursor

from anika.models.task import Task


class TaskDialog(QDialog):
    """Dialog for creating or editing a task."""
    
    def __init__(self, parent=None, task: Optional[Task] = None, default_date: Optional[date] = None):
        super().__init__(parent)
        self.task = task
        self.default_date = default_date or date.today()
        self.setWindowTitle("Edit Task" if task else "New Task")
        self.setModal(True)
        self.setMinimumSize(450, 400)
        self.setup_ui()
        self.apply_style()
        
        if task:
            self.populate_fields()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Task Title *")
        title_label.setObjectName("fieldLabel")
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setObjectName("dialogInput")
        self.title_input.setPlaceholderText("Enter task title...")
        layout.addWidget(self.title_input)
        
        # Description
        desc_label = QLabel("Description")
        desc_label.setObjectName("fieldLabel")
        layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setObjectName("dialogTextArea")
        self.desc_input.setPlaceholderText("Add a description (optional)...")
        self.desc_input.setMaximumHeight(100)
        layout.addWidget(self.desc_input)
        
        # Date and Time row
        datetime_layout = QHBoxLayout()
        datetime_layout.setSpacing(20)
        
        # Due Date
        date_container = QVBoxLayout()
        date_label = QLabel("Due Date *")
        date_label.setObjectName("fieldLabel")
        date_container.addWidget(date_label)
        
        self.date_input = QDateEdit()
        self.date_input.setObjectName("dialogInput")
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate(
            self.default_date.year,
            self.default_date.month,
            self.default_date.day
        ))
        self.date_input.setDisplayFormat("MMM dd, yyyy")
        date_container.addWidget(self.date_input)
        datetime_layout.addLayout(date_container)
        
        # Due Time
        time_container = QVBoxLayout()
        time_label = QLabel("Due Time")
        time_label.setObjectName("fieldLabel")
        time_container.addWidget(time_label)
        
        time_row = QHBoxLayout()
        self.time_input = QTimeEdit()
        self.time_input.setObjectName("dialogInput")
        self.time_input.setDisplayFormat("hh:mm AP")
        self.time_input.setTime(QTime(12, 0))
        time_row.addWidget(self.time_input)
        
        self.no_time_check = QCheckBox("No specific time")
        self.no_time_check.setObjectName("dialogCheckbox")
        self.no_time_check.stateChanged.connect(self.on_no_time_changed)
        time_row.addWidget(self.no_time_check)
        
        time_container.addLayout(time_row)
        datetime_layout.addLayout(time_container)
        
        layout.addLayout(datetime_layout)
        
        # Spacer
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("dialogCancelBtn")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Save Task")
        save_btn.setObjectName("dialogSaveBtn")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.clicked.connect(self.on_save)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def apply_style(self):
        """Apply dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
            }
            
            QLabel#fieldLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
                font-weight: bold;
            }
            
            QLineEdit#dialogInput, QTextEdit#dialogTextArea,
            QDateEdit#dialogInput, QTimeEdit#dialogInput {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px 12px;
                color: white;
                font-size: 14px;
            }
            
            QLineEdit#dialogInput:focus, QTextEdit#dialogTextArea:focus,
            QDateEdit#dialogInput:focus, QTimeEdit#dialogInput:focus {
                border-color: #8ab4f8;
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            QCheckBox#dialogCheckbox {
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
            }
            
            QCheckBox#dialogCheckbox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                background-color: transparent;
            }
            
            QCheckBox#dialogCheckbox::indicator:checked {
                background-color: #8ab4f8;
                border-color: #8ab4f8;
            }
            
            QPushButton#dialogCancelBtn {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            
            QPushButton#dialogCancelBtn:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
            
            QPushButton#dialogSaveBtn {
                background-color: #8ab4f8;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: #1e1e2e;
                font-size: 14px;
                font-weight: bold;
            }
            
            QPushButton#dialogSaveBtn:hover {
                background-color: #aecbfa;
            }
            
            /* Calendar popup styling */
            QCalendarWidget {
                background-color: #2a2a3e;
            }
            
            QCalendarWidget QToolButton {
                color: white;
                background-color: transparent;
            }
            
            QCalendarWidget QMenu {
                background-color: #2a2a3e;
                color: white;
            }
            
            QCalendarWidget QSpinBox {
                color: white;
                background-color: #3a3a4e;
            }
            
            QCalendarWidget QAbstractItemView {
                color: white;
                background-color: #2a2a3e;
                selection-background-color: #8ab4f8;
                selection-color: #1e1e2e;
            }
        """)
    
    def populate_fields(self):
        """Populate fields with existing task data."""
        if not self.task:
            return
        
        self.title_input.setText(self.task.title)
        self.desc_input.setPlainText(self.task.description or "")
        
        self.date_input.setDate(QDate(
            self.task.due_date.year,
            self.task.due_date.month,
            self.task.due_date.day
        ))
        
        if self.task.due_time:
            self.time_input.setTime(QTime(
                self.task.due_time.hour,
                self.task.due_time.minute
            ))
            self.no_time_check.setChecked(False)
        else:
            self.no_time_check.setChecked(True)
    
    def on_no_time_changed(self, state):
        """Handle no time checkbox change."""
        self.time_input.setEnabled(state != Qt.CheckState.Checked.value)
    
    def on_save(self):
        """Handle save button click."""
        title = self.title_input.text().strip()
        
        if not title:
            self.title_input.setFocus()
            self.title_input.setStyleSheet(
                self.title_input.styleSheet() + 
                "border-color: #ff6b6b !important;"
            )
            return
        
        self.accept()
    
    def get_task_data(self) -> Dict[str, Any]:
        """Get the task data from the form."""
        qdate = self.date_input.date()
        due_date = date(qdate.year(), qdate.month(), qdate.day())
        
        due_time = None
        if not self.no_time_check.isChecked():
            qtime = self.time_input.time()
            due_time = dt_time(qtime.hour(), qtime.minute())
        
        return {
            'title': self.title_input.text().strip(),
            'description': self.desc_input.toPlainText().strip() or None,
            'due_date': due_date,
            'due_time': due_time
        }
