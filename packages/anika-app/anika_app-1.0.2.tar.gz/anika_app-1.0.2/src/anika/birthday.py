"""
Birthday celebration mode for Anika.

Special command: anika aaryan
"""
import sys
import os
import random
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize,
    Property, QParallelAnimationGroup, QSequentialAnimationGroup, Signal, QObject
)
from PySide6.QtGui import QPixmap, QFont, QColor, QPainter, QPen, QBrush, QLinearGradient

# Try to import pygame for audio, but don't fail if not available
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class Confetti(QWidget):
    """A single confetti particle."""
    
    def __init__(self, parent, color: QColor, size: int = 12):
        super().__init__(parent)
        self.color = color
        self.confetti_size = size
        self.rotation = random.randint(0, 360)
        self.rotation_speed = random.uniform(-10, 10)
        self.velocity_x = random.uniform(-3, 3)
        self.velocity_y = random.uniform(-15, -8)
        self.gravity = 0.3
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.confetti_size / 2, self.confetti_size / 2)
        painter.rotate(self.rotation)
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw different shapes
        shape = random.randint(0, 2) if not hasattr(self, '_shape') else self._shape
        self._shape = shape
        
        if shape == 0:  # Rectangle
            painter.drawRect(-self.confetti_size//3, -self.confetti_size//4, 
                           self.confetti_size//1.5, self.confetti_size//2)
        elif shape == 1:  # Circle
            painter.drawEllipse(-self.confetti_size//3, -self.confetti_size//3,
                              self.confetti_size//1.5, self.confetti_size//1.5)
        else:  # Triangle
            from PySide6.QtGui import QPolygon
            triangle = QPolygon([
                QPoint(0, -self.confetti_size//3),
                QPoint(-self.confetti_size//3, self.confetti_size//4),
                QPoint(self.confetti_size//3, self.confetti_size//4)
            ])
            painter.drawPolygon(triangle)
    
    def update_physics(self):
        """Update confetti position and rotation."""
        self.velocity_y += self.gravity
        new_x = self.x() + self.velocity_x
        new_y = self.y() + self.velocity_y
        self.rotation += self.rotation_speed
        self.move(int(new_x), int(new_y))
        self.update()
        
        # Return True if still on screen
        parent = self.parent()
        if parent:
            return new_y < parent.height() + 50
        return False


class ConfettiSystem(QObject):
    """Manages confetti particles."""
    
    def __init__(self, parent_widget: QWidget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.confetti_particles = []
        self.colors = [
            QColor(255, 107, 107),  # Red
            QColor(78, 205, 196),   # Teal
            QColor(255, 230, 109),  # Yellow
            QColor(170, 111, 255),  # Purple
            QColor(255, 154, 162),  # Pink
            QColor(107, 203, 119),  # Green
            QColor(255, 179, 71),   # Orange
            QColor(99, 179, 237),   # Blue
        ]
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_confetti)
        
        self.spawn_timer = QTimer(self)
        self.spawn_timer.timeout.connect(self.spawn_burst)
        
    def start(self):
        """Start the confetti effect."""
        self.spawn_burst()
        self.update_timer.start(16)  # ~60 FPS
        self.spawn_timer.start(500)  # Spawn burst every 500ms
        
        # Stop spawning after 5 seconds
        QTimer.singleShot(5000, self.spawn_timer.stop)
        
    def spawn_burst(self):
        """Spawn a burst of confetti."""
        parent_width = self.parent_widget.width()
        parent_height = self.parent_widget.height()
        
        for _ in range(30):
            color = random.choice(self.colors)
            size = random.randint(8, 16)
            confetti = Confetti(self.parent_widget, color, size)
            
            # Start from random positions at the top
            start_x = random.randint(0, parent_width)
            start_y = random.randint(-50, parent_height // 3)
            confetti.move(start_x, start_y)
            confetti.show()
            
            self.confetti_particles.append(confetti)
    
    def update_confetti(self):
        """Update all confetti particles."""
        alive_particles = []
        for confetti in self.confetti_particles:
            if confetti.update_physics():
                alive_particles.append(confetti)
            else:
                confetti.deleteLater()
        
        self.confetti_particles = alive_particles
        
        # Stop timer if no particles left and spawn timer stopped
        if not self.confetti_particles and not self.spawn_timer.isActive():
            self.update_timer.stop()


class BirthdayWindow(QMainWindow):
    """Special birthday celebration window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Happy Birthday Anni! 🎂")
        self.setMinimumSize(900, 700)
        
        # Get screen size and center
        screen = QApplication.primaryScreen().geometry()
        self.resize(int(screen.width() * 0.75), int(screen.height() * 0.8))
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        # Central widget
        self.central = QWidget()
        self.setCentralWidget(self.central)
        
        # Background label for image
        self.bg_label = QLabel(self.central)
        self.bg_label.setScaledContents(True)
        
        # Create a container for text with proper centering
        self.text_container = QWidget(self.central)
        self.text_container.setStyleSheet("background-color: transparent;")
        
        text_layout = QVBoxLayout(self.text_container)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_layout.setSpacing(15)
        
        # Main birthday message - Line 1
        self.title_label = QLabel("🎂 HAPPY BIRTHDAY ANNI! 🎂")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 52px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 180);
                border-radius: 15px;
                padding: 25px 40px;
            }
        """)
        text_layout.addWidget(self.title_label)
        
        # Take care message - Line 2
        self.care_label = QLabel("💖 TAKE CARE 💖")
        self.care_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.care_label.setStyleSheet("""
            QLabel {
                color: #ff9999;
                font-size: 36px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 180);
                border-radius: 12px;
                padding: 20px 35px;
            }
        """)
        text_layout.addWidget(self.care_label)
        
        # Secondary message - From Aaryan
        self.sub_label = QLabel("~ Aaryan ❤️")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 220);
                font-size: 24px;
                font-style: italic;
                background-color: rgba(0, 0, 0, 120);
                border-radius: 10px;
                padding: 15px 30px;
            }
        """)
        text_layout.addWidget(self.sub_label)
        
        # Setup confetti
        self.confetti_system = ConfettiSystem(self.central)
        
        # Load random image
        self.load_random_image()
        
        # Position elements
        self.resizeEvent(None)
        
        # Start effects after a short delay
        QTimer.singleShot(100, self.start_celebration)
        
        # Apply window styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
        """)
        
    def load_random_image(self):
        """Load a random image from the images directory."""
        from anika.main import get_resources_dir
        
        images_dir = get_resources_dir()
        
        # Also check the images folder in the project root
        if not os.path.exists(images_dir):
            # Try development path
            package_dir = os.path.dirname(os.path.abspath(__file__))
            images_dir = os.path.join(package_dir, "..", "..", "images")
            images_dir = os.path.abspath(images_dir)
        
        if os.path.exists(images_dir):
            images = [f for f in os.listdir(images_dir) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
            if images:
                random_image = random.choice(images)
                image_path = os.path.join(images_dir, random_image)
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    self.bg_label.setPixmap(pixmap)
                    return
        
        # Fallback: Create gradient background
        self.create_gradient_background()
    
    def create_gradient_background(self):
        """Create a beautiful gradient background."""
        pixmap = QPixmap(self.width() or 900, self.height() or 700)
        painter = QPainter(pixmap)
        
        gradient = QLinearGradient(0, 0, pixmap.width(), pixmap.height())
        gradient.setColorAt(0, QColor(102, 126, 234))
        gradient.setColorAt(0.5, QColor(118, 75, 162))
        gradient.setColorAt(1, QColor(255, 110, 127))
        
        painter.fillRect(pixmap.rect(), gradient)
        painter.end()
        
        self.bg_label.setPixmap(pixmap)
    
    def resizeEvent(self, event):
        """Handle window resize."""
        if self.central:
            # Background covers entire window
            self.bg_label.setGeometry(0, 0, self.central.width(), self.central.height())
            
            # Text container covers entire window (layout handles centering)
            self.text_container.setGeometry(0, 0, self.central.width(), self.central.height())
        
        if event:
            super().resizeEvent(event)
    
    def start_celebration(self):
        """Start the birthday celebration effects."""
        # Start confetti
        self.confetti_system.start()
        
        # Play music if available
        self.play_birthday_music()
        
        # Animate text
        self.animate_text()
    
    def play_birthday_music(self):
        """Play birthday music using pygame."""
        if not PYGAME_AVAILABLE:
            print("Pygame not available for music playback")
            return
            
        try:
            pygame.mixer.init()
            
            # Find audio directory - try multiple locations
            package_dir = os.path.dirname(os.path.abspath(__file__))
            
            possible_paths = [
                os.path.join(package_dir, "resources", "audio"),
                os.path.join(package_dir, "..", "..", "src", "anika", "resources", "audio"),
            ]
            
            # Also try get_audio_dir
            try:
                from anika.main import get_audio_dir
                possible_paths.insert(0, get_audio_dir())
            except:
                pass
            
            audio_dir = None
            for path in possible_paths:
                if os.path.exists(path):
                    audio_dir = os.path.abspath(path)
                    break
            
            if not audio_dir:
                print(f"Audio directory not found. Tried: {possible_paths}")
                return
            
            songs = [f for f in os.listdir(audio_dir) 
                    if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
            
            if songs:
                song_path = os.path.join(audio_dir, songs[0])
                print(f"Playing: {song_path}")
                pygame.mixer.music.load(song_path)
                pygame.mixer.music.set_volume(0.7)
                pygame.mixer.music.play(-1)  # Loop indefinitely
            else:
                print(f"No audio files found in: {audio_dir}")
                
        except Exception as e:
            print(f"Could not play music: {e}")
    
    def animate_text(self):
        """Animate the birthday text."""
        # Pulse effect using opacity on the title
        effect = QGraphicsOpacityEffect(self.title_label)
        self.title_label.setGraphicsEffect(effect)
        
        self.pulse_animation = QPropertyAnimation(effect, b"opacity")
        self.pulse_animation.setDuration(1500)
        self.pulse_animation.setStartValue(0.7)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop
        self.pulse_animation.start()
    
    def closeEvent(self, event):
        """Clean up on close."""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except:
                pass
        event.accept()


def launch_birthday_mode():
    """Launch the birthday celebration mode."""
    app = QApplication(sys.argv)
    app.setApplicationName("Anika - Happy Birthday!")
    
    # Set app-wide font
    font = QFont()
    font.setFamily("Segoe UI" if sys.platform == "win32" else "SF Pro Display" if sys.platform == "darwin" else "Ubuntu")
    font.setPointSize(11)
    app.setFont(font)
    
    window = BirthdayWindow()
    window.show()
    
    sys.exit(app.exec())
