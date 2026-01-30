"""
Main application window for Anika.

A beautiful productivity app with To-Do, Calendar, and Clock.
"""
import sys
import os
import random
from datetime import datetime, date, time as dt_time
from typing import Optional, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStackedWidget, QSystemTrayIcon, QMenu,
    QGraphicsOpacityEffect, QSizePolicy, QScrollArea, QSplitter
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, Signal, QThread
)
from PySide6.QtGui import (
    QPixmap, QFont, QColor, QPainter, QBrush, QPalette, QAction, QIcon,
    QLinearGradient, QPainterPath, QImage
)

from anika.widgets.clock import ClockWidget
from anika.widgets.calendar import CalendarWidget
from anika.widgets.task_list import TaskListWidget
from anika.widgets.task_dialog import TaskDialog
from anika.data.database import Database
from anika.models.task import Task
from anika.styles.theme import get_stylesheet, COLORS


class BackgroundWidget(QWidget):
    """Widget that displays rotating background images."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pixmap = None
        self.next_pixmap = None
        self.opacity = 1.0
        self.images: List[str] = []
        self.current_index = 0
        
        # Load images
        self.load_images()
        
        # Transition timer
        self.transition_timer = QTimer(self)
        self.transition_timer.timeout.connect(self.start_transition)
        self.transition_timer.start(60000)  # Change every 60 seconds
        
        # Animation timer for smooth transition
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate_transition)
        
        self.transitioning = False
        self.transition_progress = 0.0
        
        # Load first image
        if self.images:
            self.load_image(0)
    
    def load_images(self):
        """Load all available background images."""
        from anika.main import get_resources_dir
        
        images_dir = get_resources_dir()
        
        # Also try the images folder
        if not os.path.exists(images_dir):
            package_dir = os.path.dirname(os.path.abspath(__file__))
            images_dir = os.path.join(package_dir, "..", "images")
            images_dir = os.path.abspath(images_dir)
        
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    self.images.append(os.path.join(images_dir, filename))
        
        # Shuffle for variety
        random.shuffle(self.images)
    
    def load_image(self, index: int):
        """Load image at the given index."""
        if not self.images:
            self.create_gradient_background()
            return
            
        index = index % len(self.images)
        path = self.images[index]
        
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.current_pixmap = pixmap
            self.update()
    
    def create_gradient_background(self):
        """Create a fallback gradient background."""
        pixmap = QPixmap(self.width() or 1200, self.height() or 800)
        painter = QPainter(pixmap)
        
        gradient = QLinearGradient(0, 0, pixmap.width(), pixmap.height())
        gradient.setColorAt(0, QColor(30, 30, 60))
        gradient.setColorAt(0.5, QColor(50, 30, 70))
        gradient.setColorAt(1, QColor(30, 50, 80))
        
        painter.fillRect(pixmap.rect(), gradient)
        painter.end()
        
        self.current_pixmap = pixmap
        self.update()
    
    def start_transition(self):
        """Start transitioning to the next image."""
        if self.transitioning or not self.images:
            return
            
        self.current_index = (self.current_index + 1) % len(self.images)
        
        # Load next image
        path = self.images[self.current_index]
        self.next_pixmap = QPixmap(path)
        
        if self.next_pixmap.isNull():
            return
        
        self.transitioning = True
        self.transition_progress = 0.0
        self.animation_timer.start(16)  # ~60 FPS
    
    def animate_transition(self):
        """Animate the background transition."""
        self.transition_progress += 0.02  # 50 frames for full transition
        
        if self.transition_progress >= 1.0:
            self.transition_progress = 1.0
            self.current_pixmap = self.next_pixmap
            self.next_pixmap = None
            self.transitioning = False
            self.animation_timer.stop()
        
        self.update()
    
    def paintEvent(self, event):
        """Paint the background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Draw current image
        if self.current_pixmap:
            scaled = self.current_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Center the image
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            
            if self.transitioning and self.next_pixmap:
                # Draw current with decreasing opacity
                painter.setOpacity(1.0 - self.transition_progress)
                painter.drawPixmap(x, y, scaled)
                
                # Draw next with increasing opacity
                next_scaled = self.next_pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                nx = (self.width() - next_scaled.width()) // 2
                ny = (self.height() - next_scaled.height()) // 2
                
                painter.setOpacity(self.transition_progress)
                painter.drawPixmap(nx, ny, next_scaled)
            else:
                painter.setOpacity(1.0)
                painter.drawPixmap(x, y, scaled)
        
        # Draw semi-transparent overlay for better text readability
        painter.setOpacity(0.4)
        painter.fillRect(self.rect(), QColor(15, 15, 25))


class GlassPanel(QFrame):
    """A glassmorphism-style panel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Glass effect background
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(0, 0, 0, 0), 16, 16)
        
        painter.fillPath(path, QColor(255, 255, 255, 15))
        
        # Border
        painter.setPen(QColor(255, 255, 255, 30))
        painter.drawPath(path)


class AnikaWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Anika")
        self.setMinimumSize(1000, 650)
        
        # Normal resizable window
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinMaxButtonsHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # Set window icon
        self.app_icon = self.load_app_icon()
        if self.app_icon:
            self.setWindowIcon(self.app_icon)
        
        # Initialize database
        self.db = Database()
        
        # Selected date for filtering
        self.selected_date = date.today()
        
        # Setup UI
        self.setup_ui()
        
        # Setup system tray
        self.setup_system_tray()
        
        # Apply stylesheet
        self.setStyleSheet(get_stylesheet())
        
        # Center on screen
        self.center_on_screen()
        
        # Load initial tasks
        self.refresh_tasks()
    
    def load_app_icon(self) -> QIcon:
        """Load the application icon."""
        package_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try ICO file first (for Windows)
        ico_path = os.path.join(package_dir, "resources", "anika.ico")
        if os.path.exists(ico_path):
            return QIcon(ico_path)
        
        # Try JPG icon
        jpg_path = os.path.join(package_dir, "resources", "anika_icon.jpg")
        if os.path.exists(jpg_path):
            pixmap = QPixmap(jpg_path)
            if not pixmap.isNull():
                # Scale to icon size
                scaled = pixmap.scaled(256, 256, 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                return QIcon(scaled)
        
        # Fallback: create default icon
        return self.create_default_icon()
    
    def center_on_screen(self):
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen().geometry()
        self.resize(int(screen.width() * 0.7), int(screen.height() * 0.75))
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
    
    def setup_ui(self):
        """Setup the main UI."""
        # Central widget
        self.central = QWidget()
        self.setCentralWidget(self.central)
        
        # Background
        self.background = BackgroundWidget(self.central)
        
        # Main content layout
        self.content = QWidget(self.central)
        self.content.setObjectName("mainContent")
        
        main_layout = QHBoxLayout(self.content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Left panel: Clock + Calendar
        left_panel = GlassPanel()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(20)
        
        # Clock widget
        self.clock = ClockWidget()
        left_layout.addWidget(self.clock)
        
        # Separator
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        left_layout.addWidget(separator)
        
        # Calendar widget
        self.calendar = CalendarWidget()
        self.calendar.date_selected.connect(self.on_date_selected)
        left_layout.addWidget(self.calendar)
        
        left_layout.addStretch()
        
        # Right panel: Tasks
        right_panel = GlassPanel()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        tasks_title = QLabel("Tasks")
        tasks_title.setObjectName("sectionTitle")
        header_layout.addWidget(tasks_title)
        
        header_layout.addStretch()
        
        # Date display
        self.date_label = QLabel()
        self.date_label.setObjectName("dateLabel")
        self.update_date_label()
        header_layout.addWidget(self.date_label)
        
        right_layout.addLayout(header_layout)
        
        # Task list widget
        self.task_list = TaskListWidget()
        self.task_list.task_completed.connect(self.on_task_completed)
        self.task_list.task_deleted.connect(self.on_task_deleted)
        self.task_list.task_edited.connect(self.on_task_edited)
        self.task_list.add_task_requested.connect(self.on_add_task)
        right_layout.addWidget(self.task_list, 1)
        
        # Add panels to main layout using splitter for resizing
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 600])
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        main_layout.addWidget(splitter)
    
    def create_default_icon(self) -> QIcon:
        """Create a default icon if no custom icon is found."""
        icon_pixmap = QPixmap(64, 64)
        icon_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(icon_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a gradient circle
        gradient = QLinearGradient(0, 0, 64, 64)
        gradient.setColorAt(0, QColor(138, 180, 248))
        gradient.setColorAt(1, QColor(174, 137, 238))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        
        # Draw "A" letter
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(icon_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "A")
        painter.end()
        
        return QIcon(icon_pixmap)
    
    def setup_system_tray(self):
        """Setup system tray icon."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use the app icon for system tray
        if self.app_icon:
            self.tray_icon.setIcon(self.app_icon)
        else:
            self.tray_icon.setIcon(self.create_default_icon())
        
        self.tray_icon.setToolTip("Anika - Productivity App")
        
        # Tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def show_window(self):
        """Show and activate the window."""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def quit_app(self):
        """Quit the application."""
        QApplication.quit()
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
    
    def closeEvent(self, event):
        """Handle window close."""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Anika",
                "Application minimized to system tray. Double-click to restore.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()
    
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        if hasattr(self, 'background'):
            self.background.setGeometry(self.central.rect())
        if hasattr(self, 'content'):
            self.content.setGeometry(self.central.rect())
    
    def update_date_label(self):
        """Update the date label display."""
        date_str = self.selected_date.strftime("%A, %B %d")
        if self.selected_date == date.today():
            date_str = f"Today • {date_str}"
        self.date_label.setText(date_str)
    
    def on_date_selected(self, selected_date: date):
        """Handle date selection from calendar."""
        self.selected_date = selected_date
        self.update_date_label()
        self.refresh_tasks()
    
    def refresh_tasks(self):
        """Refresh the task list."""
        tasks = self.db.get_tasks_by_date(self.selected_date)
        self.task_list.set_tasks(tasks)
        
        # Update calendar highlights
        all_tasks = self.db.get_all_tasks()
        dates_with_tasks = set(task.due_date for task in all_tasks if not task.completed)
        self.calendar.highlight_dates(dates_with_tasks)
    
    def on_add_task(self):
        """Handle add task request."""
        dialog = TaskDialog(self, default_date=self.selected_date)
        if dialog.exec():
            task_data = dialog.get_task_data()
            self.db.create_task(
                title=task_data['title'],
                description=task_data['description'],
                due_date=task_data['due_date'],
                due_time=task_data['due_time']
            )
            self.refresh_tasks()
    
    def on_task_completed(self, task_id: int, completed: bool):
        """Handle task completion toggle."""
        self.db.update_task(task_id, completed=completed)
        self.refresh_tasks()
    
    def on_task_deleted(self, task_id: int):
        """Handle task deletion."""
        self.db.delete_task(task_id)
        self.refresh_tasks()
    
    def on_task_edited(self, task_id: int):
        """Handle task edit request."""
        task = self.db.get_task(task_id)
        if task:
            dialog = TaskDialog(self, task=task)
            if dialog.exec():
                task_data = dialog.get_task_data()
                self.db.update_task(
                    task_id,
                    title=task_data['title'],
                    description=task_data['description'],
                    due_date=task_data['due_date'],
                    due_time=task_data['due_time']
                )
                self.refresh_tasks()


def launch_app():
    """Launch the main Anika application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Anika")
    app.setOrganizationName("AaryanChoudhary")
    
    # Set app-wide font based on OS
    font = QFont()
    if sys.platform == "win32":
        font.setFamily("Segoe UI")
    elif sys.platform == "darwin":
        font.setFamily("SF Pro Display")
    else:
        font.setFamily("Ubuntu")
    font.setPointSize(10)
    app.setFont(font)
    
    # Prevent quit on last window close (for system tray)
    app.setQuitOnLastWindowClosed(False)
    
    window = AnikaWindow()
    window.show()
    
    sys.exit(app.exec())
