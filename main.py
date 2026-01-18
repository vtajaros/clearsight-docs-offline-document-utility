"""
PDF Toolkit - Offline Document Utility Application
Main entry point for the application.
"""
import sys
import os
import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
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


def set_windows_appusermodelid():
    """Set the AppUserModelID for Windows taskbar icon support."""
    if sys.platform == 'win32':
        try:
            import ctypes
            # Set a unique AppUserModelID so Windows shows our icon instead of Python's
            app_id = 'ClearSightDocs.PDFToolkit.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass  # Fail silently on non-Windows or if ctypes fails


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


def main():
    """Initialize and run the application."""
    # Hide console windows for subprocess calls (prevents flashing on Windows)
    hide_console_windows()
    
    # Set AppUserModelID BEFORE creating QApplication (required for taskbar icon)
    set_windows_appusermodelid()
    
    # Enable high DPI scaling for modern displays
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("ClearSight Docs")
    app.setOrganizationName("ClearSight Docs")
    
    # Set application icon for taskbar and Alt+Tab
    icon_path = resource_path("app_icon.ico")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    
    # Create and show the main window
    window = MainWindow(icon_path if os.path.exists(icon_path) else None)
    window.showMaximized()  # Start maximized for better layout
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
