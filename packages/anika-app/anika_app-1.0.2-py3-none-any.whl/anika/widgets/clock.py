"""
Live clock widget for Anika.
"""
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class ClockWidget(QWidget):
    """A beautiful live clock widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every second
        
        # Initial update
        self.update_time()
    
    def setup_ui(self):
        """Setup the clock UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Time label
        self.time_label = QLabel()
        self.time_label.setObjectName("clockTime")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)
        
        # Date label
        self.date_label = QLabel()
        self.date_label.setObjectName("clockDate")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.date_label)
        
        # Greeting label
        self.greeting_label = QLabel()
        self.greeting_label.setObjectName("clockGreeting")
        self.greeting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.greeting_label)
    
    def update_time(self):
        """Update the clock display."""
        now = datetime.now()
        
        # Time in 12-hour format
        time_str = now.strftime("%I:%M:%S %p")
        self.time_label.setText(time_str)
        
        # Full date
        date_str = now.strftime("%A, %B %d, %Y")
        self.date_label.setText(date_str)
        
        # Greeting based on time
        hour = now.hour
        if 5 <= hour < 12:
            greeting = "Good Morning ☀️"
        elif 12 <= hour < 17:
            greeting = "Good Afternoon 🌤️"
        elif 17 <= hour < 21:
            greeting = "Good Evening 🌅"
        else:
            greeting = "Good Night 🌙"
        
        self.greeting_label.setText(greeting)
