"""
Theme and styling for Anika.

Provides QSS stylesheets and color definitions.
"""

# Color palette
COLORS = {
    # Primary colors
    'primary': '#8ab4f8',
    'primary_hover': '#aecbfa',
    'secondary': '#ae89ee',
    'secondary_hover': '#c4a7f5',
    
    # Background colors
    'bg_dark': '#1a1a2e',
    'bg_medium': '#1e1e2e',
    'bg_light': '#2a2a3e',
    'bg_glass': 'rgba(255, 255, 255, 0.08)',
    
    # Text colors
    'text_primary': '#ffffff',
    'text_secondary': 'rgba(255, 255, 255, 0.7)',
    'text_muted': 'rgba(255, 255, 255, 0.5)',
    
    # Status colors
    'success': '#81c995',
    'warning': '#fdd663',
    'error': '#f28b82',
    'overdue': '#ff6b6b',
    
    # Border colors
    'border_light': 'rgba(255, 255, 255, 0.1)',
    'border_medium': 'rgba(255, 255, 255, 0.2)',
}


def get_stylesheet() -> str:
    """Get the main application stylesheet."""
    return """
        /* Main Window */
        QMainWindow {
            background-color: transparent;
        }
        
        QWidget#mainContent {
            background-color: transparent;
        }
        
        /* Glass Panel */
        QFrame#glassPanel {
            background-color: rgba(30, 30, 46, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
        }
        
        /* Section Titles */
        QLabel#sectionTitle {
            color: white;
            font-size: 20px;
            font-weight: bold;
        }
        
        QLabel#dateLabel {
            color: rgba(255, 255, 255, 0.6);
            font-size: 14px;
        }
        
        /* Clock Widget */
        QLabel#clockTime {
            color: white;
            font-size: 42px;
            font-weight: bold;
            letter-spacing: 2px;
        }
        
        QLabel#clockDate {
            color: rgba(255, 255, 255, 0.7);
            font-size: 15px;
        }
        
        QLabel#clockGreeting {
            color: #8ab4f8;
            font-size: 16px;
            font-weight: 500;
            margin-top: 5px;
        }
        
        /* Task List */
        QScrollArea#taskScroll {
            background-color: transparent;
            border: none;
        }
        
        QWidget#taskContainer {
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            background-color: rgba(255, 255, 255, 0.05);
            width: 8px;
            border-radius: 4px;
        }
        
        QScrollBar::handle:vertical {
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: rgba(255, 255, 255, 0.3);
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* Task Item */
        QFrame#taskItem {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
        }
        
        QFrame#taskItem:hover {
            background-color: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.12);
        }
        
        QFrame#taskItem[state="completed"] {
            opacity: 0.6;
        }
        
        QFrame#taskItem[state="overdue"] {
            border-color: rgba(255, 107, 107, 0.5);
            background-color: rgba(255, 107, 107, 0.1);
        }
        
        QLabel#taskTitle {
            color: white;
            font-size: 15px;
            font-weight: 500;
        }
        
        QLabel#taskDescription {
            color: rgba(255, 255, 255, 0.6);
            font-size: 13px;
        }
        
        QLabel#taskTime {
            color: rgba(255, 255, 255, 0.5);
            font-size: 12px;
        }
        
        QLabel#taskOverdue {
            color: #ff6b6b;
            font-size: 12px;
            font-weight: bold;
        }
        
        /* Task Checkbox */
        QCheckBox#taskCheckbox {
            spacing: 0px;
        }
        
        QCheckBox#taskCheckbox::indicator {
            width: 22px;
            height: 22px;
            border-radius: 11px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            background-color: transparent;
        }
        
        QCheckBox#taskCheckbox::indicator:hover {
            border-color: #8ab4f8;
        }
        
        QCheckBox#taskCheckbox::indicator:checked {
            background-color: #81c995;
            border-color: #81c995;
        }
        
        /* Task Action Buttons */
        QPushButton#taskActionBtn {
            background-color: transparent;
            border: none;
            border-radius: 6px;
            font-size: 14px;
        }
        
        QPushButton#taskActionBtn:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        
        /* Add Task Button */
        QPushButton#addTaskBtn {
            background-color: #8ab4f8;
            border: none;
            border-radius: 10px;
            padding: 14px 20px;
            color: #1a1a2e;
            font-size: 15px;
            font-weight: bold;
        }
        
        QPushButton#addTaskBtn:hover {
            background-color: #aecbfa;
        }
        
        QPushButton#addTaskBtn:pressed {
            background-color: #7aa8f2;
        }
        
        /* Empty State */
        QLabel#emptyState {
            color: rgba(255, 255, 255, 0.4);
            font-size: 14px;
            padding: 40px;
        }
        
        /* Tooltips */
        QToolTip {
            background-color: #2a2a3e;
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }
    """
