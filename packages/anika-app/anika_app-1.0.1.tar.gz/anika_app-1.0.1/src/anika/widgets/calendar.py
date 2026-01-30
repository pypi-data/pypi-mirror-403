"""
Calendar widget for Anika.
"""
from datetime import date
from typing import Set
from PySide6.QtWidgets import QWidget, QVBoxLayout, QCalendarWidget
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QTextCharFormat, QColor, QBrush, QPalette


class CalendarWidget(QWidget):
    """A styled calendar widget."""
    
    date_selected = Signal(date)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighted_dates: Set[date] = set()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the calendar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.calendar = QCalendarWidget()
        self.calendar.setObjectName("mainCalendar")
        
        # Configure calendar
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.calendar.setGridVisible(False)
        self.calendar.setNavigationBarVisible(True)
        
        # Connect signals
        self.calendar.clicked.connect(self.on_date_clicked)
        self.calendar.currentPageChanged.connect(self.on_page_changed)
        
        layout.addWidget(self.calendar)
        
        # Apply custom styling
        self.apply_styling()
    
    def apply_styling(self):
        """Apply custom styling to the calendar."""
        # Style the calendar
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: transparent;
            }
            
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                min-height: 40px;
            }
            
            QCalendarWidget QToolButton {
                color: white;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 14px;
                font-weight: bold;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            QCalendarWidget QToolButton::menu-indicator {
                image: none;
            }
            
            QCalendarWidget QMenu {
                background-color: #2a2a3e;
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            QCalendarWidget QMenu::item:selected {
                background-color: #4a4a6e;
            }
            
            QCalendarWidget QSpinBox {
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
                padding: 3px;
            }
            
            QCalendarWidget QAbstractItemView {
                background-color: transparent;
                selection-background-color: rgba(138, 180, 248, 0.3);
                selection-color: white;
                outline: none;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                color: white;
            }
            
            QCalendarWidget QAbstractItemView:disabled {
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        
        # Today format
        today_format = QTextCharFormat()
        today_format.setBackground(QBrush(QColor(138, 180, 248, 80)))
        today_format.setForeground(QBrush(QColor(255, 255, 255)))
        self.calendar.setDateTextFormat(QDate.currentDate(), today_format)
        
        # Weekend format
        weekend_format = QTextCharFormat()
        weekend_format.setForeground(QBrush(QColor(255, 182, 193)))
        self.calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
        self.calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)
    
    def on_date_clicked(self, qdate: QDate):
        """Handle date click."""
        selected = date(qdate.year(), qdate.month(), qdate.day())
        self.date_selected.emit(selected)
    
    def on_page_changed(self, year: int, month: int):
        """Handle month/year navigation."""
        self.apply_styling()
        self.update_highlights()
    
    def highlight_dates(self, dates: Set[date]):
        """Highlight dates that have tasks."""
        self.highlighted_dates = dates
        self.update_highlights()
    
    def update_highlights(self):
        """Update all date highlighting."""
        # Clear previous formatting (except today and weekends)
        self.apply_styling()
        
        # Highlight format for dates with tasks
        task_format = QTextCharFormat()
        task_format.setBackground(QBrush(QColor(174, 137, 238, 60)))
        task_format.setForeground(QBrush(QColor(255, 255, 255)))
        
        for d in self.highlighted_dates:
            qdate = QDate(d.year, d.month, d.day)
            self.calendar.setDateTextFormat(qdate, task_format)
        
        # Make sure today is still highlighted differently
        today_format = QTextCharFormat()
        today_format.setBackground(QBrush(QColor(138, 180, 248, 120)))
        today_format.setForeground(QBrush(QColor(255, 255, 255)))
        self.calendar.setDateTextFormat(QDate.currentDate(), today_format)
    
    def get_selected_date(self) -> date:
        """Get the currently selected date."""
        qdate = self.calendar.selectedDate()
        return date(qdate.year(), qdate.month(), qdate.day())
