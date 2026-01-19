"""
PDF Toolkit - Offline Document Utility Application
Main entry point for the application.
"""
import sys
import os

# CRITICAL: Set AppUserModelID BEFORE any Qt imports to ensure taskbar icon works on first launch
# This must be done at module load time, before any windows or Qt objects are created
if sys.platform == 'win32':
    try:
        import ctypes
        from ctypes import wintypes
        
        # Set a unique AppUserModelID so Windows shows our icon instead of Python's
        # This MUST happen before any Qt imports or window creation
        _app_id = 'ClearSightDocs.PDFToolkit.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_app_id)
    except Exception:
        pass  # Fail silently on non-Windows or if ctypes fails

import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    if hasattr(sys, '_MEIPASS'):
        # Running as bundled executable
        base_path = sys._MEIPASS
    else:
        # Running in development
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def hide_console_windows():
    """
    Configure subprocess to hide console windows on Windows.
    This prevents console flashes when running external tools like Tesseract.
    """
    if sys.platform == 'win32':
        # Store the original Popen
        original_popen = subprocess.Popen
        
        def popen_no_console(*args, **kwargs):
            # Add startupinfo to hide console window
            if 'startupinfo' not in kwargs:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                kwargs['startupinfo'] = startupinfo
            # Also add CREATE_NO_WINDOW flag
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            return original_popen(*args, **kwargs)
        
        # Patch subprocess.Popen globally
        subprocess.Popen = popen_no_console


def refresh_taskbar_icon(window, app_icon):
    """
    Force Windows to refresh the taskbar icon.
    This helps ensure the icon appears correctly on first launch.
    """
    if sys.platform == 'win32' and app_icon and not app_icon.isNull():
        # Re-apply the window icon after a short delay
        # This forces Windows to update its internal icon cache for this window
        window.setWindowIcon(app_icon)
        
        # Briefly hide and show the window to force taskbar refresh
        # This is a workaround for Windows icon caching issues
        window.hide()
        window.showMaximized()


def main():
    """Initialize and run the application."""
    # Hide console windows for subprocess calls (prevents flashing on Windows)
    hide_console_windows()
    
    # Note: AppUserModelID is already set at module load time (before Qt imports)
    # This is critical for the taskbar icon to work correctly on first launch
    
    # Enable high DPI scaling for modern displays
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("ClearSight Docs")
    app.setOrganizationName("ClearSight Docs")
    
    # Set application icon for taskbar and Alt+Tab
    icon_path = resource_path("app_icon.ico")
    app_icon = None
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    
    # Create and show the main window
    window = MainWindow(icon_path if os.path.exists(icon_path) else None)
    
    # Set the window icon explicitly on the window as well
    if app_icon and not app_icon.isNull():
        window.setWindowIcon(app_icon)
    
    window.showMaximized()  # Start maximized for better layout
    
    # Use QTimer to refresh the taskbar icon after the event loop starts
    # This ensures the icon is properly registered with Windows on first launch
    if sys.platform == 'win32' and app_icon and not app_icon.isNull():
        QTimer.singleShot(100, lambda: window.setWindowIcon(app_icon))
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
