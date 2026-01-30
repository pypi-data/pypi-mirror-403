"""
Desktop integration for Anika.

Creates desktop shortcuts and start menu entries.
"""
import sys
import os
import shutil


def get_python_executable():
    """Get the path to the Python executable."""
    return sys.executable


def get_scripts_dir():
    """Get the scripts directory where anika command is installed."""
    if sys.platform == "win32":
        # Check user scripts first
        user_scripts = os.path.join(os.path.dirname(sys.executable), "Scripts")
        if os.path.exists(os.path.join(user_scripts, "anika.exe")):
            return user_scripts
        
        # Check site-packages scripts
        import site
        for path in site.getsitepackages() + [site.getusersitepackages()]:
            scripts = os.path.join(os.path.dirname(path), "Scripts")
            if os.path.exists(os.path.join(scripts, "anika.exe")):
                return scripts
    
    return os.path.dirname(sys.executable)


def get_anika_executable():
    """Get the path to the anika executable."""
    if sys.platform == "win32":
        scripts_dir = get_scripts_dir()
        exe_path = os.path.join(scripts_dir, "anika.exe")
        if os.path.exists(exe_path):
            return exe_path
        
        # Fallback: look in PATH
        import shutil
        return shutil.which("anika") or "anika"
    else:
        import shutil
        return shutil.which("anika") or "anika"


def create_windows_shortcut(target_path, shortcut_path, description="", icon_path=None):
    """Create a Windows shortcut (.lnk file)."""
    try:
        import winreg
        from pathlib import Path
        
        # Use PowerShell to create shortcut
        ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target_path}"
$Shortcut.Description = "{description}"
$Shortcut.WorkingDirectory = "{os.path.dirname(target_path)}"
'''
        if icon_path and os.path.exists(icon_path):
            ps_script += f'$Shortcut.IconLocation = "{icon_path}"\n'
        
        ps_script += '$Shortcut.Save()'
        
        import subprocess
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"Failed to create shortcut: {e}")
        return False


def create_desktop_shortcut():
    """Create a desktop shortcut for Anika."""
    if sys.platform != "win32":
        print("Desktop shortcut creation is only supported on Windows.")
        return False
    
    anika_exe = get_anika_executable()
    if not anika_exe or not os.path.exists(anika_exe):
        print(f"Could not find anika executable at: {anika_exe}")
        return False
    
    # Get desktop path
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "Anika.lnk")
    
    # Get icon path
    package_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(package_dir, "resources", "anika.ico")
    
    success = create_windows_shortcut(
        target_path=anika_exe,
        shortcut_path=shortcut_path,
        description="Anika - Productivity App by Aaryan",
        icon_path=icon_path if os.path.exists(icon_path) else None
    )
    
    if success:
        print(f"✓ Desktop shortcut created: {shortcut_path}")
    
    return success


def create_start_menu_shortcut():
    """Create a Start Menu shortcut for Anika."""
    if sys.platform != "win32":
        print("Start menu shortcut creation is only supported on Windows.")
        return False
    
    anika_exe = get_anika_executable()
    if not anika_exe or not os.path.exists(anika_exe):
        print(f"Could not find anika executable")
        return False
    
    # Get Start Menu path
    start_menu = os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")),
        "Microsoft", "Windows", "Start Menu", "Programs"
    )
    
    # Create Anika folder
    anika_folder = os.path.join(start_menu, "Anika")
    os.makedirs(anika_folder, exist_ok=True)
    
    shortcut_path = os.path.join(anika_folder, "Anika.lnk")
    
    # Get icon path
    package_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(package_dir, "resources", "anika.ico")
    
    success = create_windows_shortcut(
        target_path=anika_exe,
        shortcut_path=shortcut_path,
        description="Anika - Productivity App by Aaryan",
        icon_path=icon_path if os.path.exists(icon_path) else None
    )
    
    if success:
        print(f"✓ Start Menu shortcut created: {shortcut_path}")
    
    return success


def install_desktop_integration():
    """Install desktop integration (shortcuts)."""
    print("\n🎨 Installing Anika Desktop Integration...")
    print("=" * 50)
    
    desktop_success = create_desktop_shortcut()
    start_menu_success = create_start_menu_shortcut()
    
    if desktop_success or start_menu_success:
        print("\n✅ Desktop integration complete!")
        print("   You can now find Anika in your Start Menu and Desktop.")
    else:
        print("\n⚠️  Could not create shortcuts automatically.")
        print("   You can still run the app using: anika")
    
    return desktop_success or start_menu_success


def uninstall_desktop_integration():
    """Remove desktop integration (shortcuts)."""
    print("\n🗑️  Removing Anika Desktop Integration...")
    
    # Remove desktop shortcut
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    desktop_shortcut = os.path.join(desktop, "Anika.lnk")
    if os.path.exists(desktop_shortcut):
        os.remove(desktop_shortcut)
        print(f"✓ Removed: {desktop_shortcut}")
    
    # Remove Start Menu folder
    start_menu = os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")),
        "Microsoft", "Windows", "Start Menu", "Programs", "Anika"
    )
    if os.path.exists(start_menu):
        shutil.rmtree(start_menu)
        print(f"✓ Removed: {start_menu}")
    
    print("✅ Desktop integration removed.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall_desktop_integration()
    else:
        install_desktop_integration()
