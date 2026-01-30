"""
Main entry point for Anika application.

Handles command-line arguments and launches the appropriate mode.
"""
import sys
import os


def get_app_data_dir() -> str:
    """Get the application data directory based on the operating system."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "Anika")
    elif sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Anika")
    else:  # Linux and other Unix-like
        xdg_data = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return os.path.join(xdg_data, "Anika")


def get_resources_dir() -> str:
    """Get the resources directory path."""
    package_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for resources/images in installed package
    resources_images = os.path.join(package_dir, "resources", "images")
    if os.path.exists(resources_images):
        return resources_images
    
    # Check for resources folder itself
    resources_dir = os.path.join(package_dir, "resources")
    if os.path.exists(resources_dir):
        return resources_dir
    
    # Fallback to development path - check images folder at project root
    dev_images = os.path.abspath(os.path.join(package_dir, "..", "..", "images"))
    if os.path.exists(dev_images):
        return dev_images
    
    return resources_dir


def get_audio_dir() -> str:
    """Get the audio resources directory path."""
    package_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for resources/audio in installed package
    resources_audio = os.path.join(package_dir, "resources", "audio")
    if os.path.exists(resources_audio):
        return resources_audio
    
    # Fallback to development path
    dev_audio = os.path.abspath(os.path.join(package_dir, "..", "..", "audio"))
    if os.path.exists(dev_audio):
        return dev_audio
    
    return resources_audio


def ensure_directories():
    """Ensure all required directories exist."""
    app_data = get_app_data_dir()
    os.makedirs(app_data, exist_ok=True)
    return app_data


def main():
    """Main entry point for the Anika application."""
    # Ensure app data directory exists
    ensure_directories()
    
    # Check for special birthday command
    if len(sys.argv) > 1 and sys.argv[1].lower() == "aaryan":
        from anika.birthday import launch_birthday_mode
        launch_birthday_mode()
        return
    
    # Launch normal application
    from anika.app import launch_app
    launch_app()


if __name__ == "__main__":
    main()
