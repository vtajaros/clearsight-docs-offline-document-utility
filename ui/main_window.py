"""
Main window for PDF Toolkit application.
Provides the main UI with sidebar navigation and stacked pages.
"""
import webbrowser
import json
import urllib.request
import urllib.error
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame,
    QMenuBar, QMenu, QMessageBox, QDialog, QDialogButtonBox,
    QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QTimer
from PySide6.QtGui import QIcon, QAction, QDesktopServices
from PySide6.QtCore import QUrl

from ui.pages.image_to_pdf_page import ImageToPdfPage
from ui.pages.pdf_merge_page import PdfMergePage
from ui.pages.pdf_split_page import PdfSplitPage
from ui.pages.pdf_to_images_page import PdfToImagesPage
from ui.pages.ocr_page import OCRPage
from ui.pages.pdf_to_word_page import PDFToWordPage
from ui.pages.pdf_delete_pages_page import PdfDeletePagesPage
from ui.pages.pdf_extract_pages_page import PdfExtractPagesPage
from ui.pages.pdf_compress_page import PdfCompressPage

# Application constants
APP_VERSION = "1.6.0"
APP_LAST_UPDATED = "January 19, 2026"
GITHUB_REPO_URL = "https://github.com/vtajaros/clearsight-docs-offline-document-utility"
GITHUB_PROFILE_URL = "https://github.com/vtajaros"
GITHUB_RELEASES_URL = "https://github.com/vtajaros/clearsight-docs-offline-document-utility/releases"
GITHUB_API_RELEASES_URL = "https://api.github.com/repos/vtajaros/clearsight-docs-offline-document-utility/releases/latest"


class UpdateCheckerThread(QThread):
    """Background thread to check for updates."""
    update_checked = Signal(bool, str, str, str)  # has_update, latest_version, download_url, release_notes
    error_occurred = Signal(str)  # error message
    
    def run(self):
        """Check GitHub API for the latest release."""
        try:
            request = urllib.request.Request(
                GITHUB_API_RELEASES_URL,
                headers={'User-Agent': 'ClearSight-Docs-Update-Checker'}
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                latest_version = data.get('tag_name', '').lstrip('v')
                release_notes = data.get('body', 'No release notes available.')
                
                # Find the download URL for the installer
                download_url = ""
                assets = data.get('assets', [])
                for asset in assets:
                    name = asset.get('name', '').lower()
                    if 'setup' in name or 'installer' in name or name.endswith('.exe'):
                        download_url = asset.get('browser_download_url', '')
                        break
                
                # If no installer found, use the release page
                if not download_url:
                    download_url = data.get('html_url', GITHUB_RELEASES_URL)
                
                # Compare versions
                has_update = self._compare_versions(APP_VERSION, latest_version)
                
                self.update_checked.emit(has_update, latest_version, download_url, release_notes)
                
        except urllib.error.URLError as e:
            self.error_occurred.emit(f"Network error: Could not connect to GitHub.\n{str(e)}")
        except json.JSONDecodeError:
            self.error_occurred.emit("Error parsing update information from GitHub.")
        except Exception as e:
            self.error_occurred.emit(f"Error checking for updates: {str(e)}")
    
    def _compare_versions(self, current: str, latest: str) -> bool:
        """Compare version strings. Returns True if latest > current."""
        try:
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            # Pad shorter version with zeros
            while len(current_parts) < len(latest_parts):
                current_parts.append(0)
            while len(latest_parts) < len(current_parts):
                latest_parts.append(0)
            
            return latest_parts > current_parts
        except ValueError:
            # If parsing fails, do string comparison
            return latest > current


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""
    
    def __init__(self, icon_path=None):
        super().__init__()
        self.setWindowTitle("ClearSight Docs - Offline Document Utility")
        self.setMinimumSize(1000, 700)
        
        # Store icon path for later use
        self._icon_path = icon_path
        
        # Update checker thread
        self._update_checker = None
        self._startup_update_check_done = False
        
        # Set window icon for title bar and taskbar
        # Setting it multiple times helps ensure Windows registers it properly
        if icon_path:
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.setWindowIcon(icon)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Initialize UI
        self._init_ui()
        
    def showEvent(self, event):
        """Override showEvent to ensure icon is set when window becomes visible."""
        super().showEvent(event)
        # Re-apply icon on show to help with first-launch taskbar icon issues
        if self._icon_path:
            icon = QIcon(self._icon_path)
            if not icon.isNull():
                self.setWindowIcon(icon)
        
        # Check for updates on first show (startup)
        if not self._startup_update_check_done:
            self._startup_update_check_done = True
            # Delay the check slightly to let the UI fully load
            QTimer.singleShot(2000, self._check_for_updates_background)
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1a252f;
                color: #ecf0f1;
                padding: 5px;
                font-size: 13px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #34495e;
            }
            QMenu {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
            QMenu::separator {
                height: 1px;
                background-color: #34495e;
                margin: 5px 10px;
            }
        """)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # About action
        about_action = QAction("About ClearSight Docs", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        
        help_menu.addSeparator()
        
        # Check for updates action
        check_updates_action = QAction("Check for Updates...", self)
        check_updates_action.triggered.connect(self._check_for_updates)
        help_menu.addAction(check_updates_action)
        
        help_menu.addSeparator()
        
        # View on GitHub (repository)
        view_github_action = QAction("View on GitHub", self)
        view_github_action.triggered.connect(self._open_github)
        help_menu.addAction(view_github_action)
        
        # Report a bug / Issues
        report_bug_action = QAction("Report a Bug", self)
        report_bug_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL + "/issues")))
        help_menu.addAction(report_bug_action)
        
        help_menu.addSeparator()
        
        # Developer profile
        profile_action = QAction("Developer: vtajaros", self)
        profile_action.triggered.connect(self._open_github_profile)
        help_menu.addAction(profile_action)
    
    def _show_about_dialog(self):
        """Show the About dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("About ClearSight Docs")
        dialog.setFixedSize(480, 350)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
            }
            QLabel#title {
                font-size: 22px;
                font-weight: bold;
                color: #3498db;
            }
            QLabel#version {
                font-size: 14px;
                color: #ecf0f1;
            }
            QLabel#info {
                font-size: 12px;
                color: #bdc3c7;
            }
            QLabel#link {
                font-size: 12px;
                color: #3498db;
            }
            QLabel#link:hover {
                color: #5dade2;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # App title
        title_label = QLabel("ClearSight Docs")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Version
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setObjectName("version")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        # Last updated
        updated_label = QLabel(f"Last Updated: {APP_LAST_UPDATED}")
        updated_label.setObjectName("info")
        updated_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(updated_label)
        
        layout.addSpacing(10)
        
        # Description
        desc_label = QLabel("A free, offline document utility for PDF conversion,\nmerging, splitting, OCR, and more.")
        desc_label.setObjectName("info")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addSpacing(10)
        
        # GitHub link
        github_label = QLabel(f'<a href="{GITHUB_REPO_URL}" style="color: #3498db;">GitHub: vtajaros/clearsight-docs</a>')
        github_label.setObjectName("link")
        github_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_label.setOpenExternalLinks(True)
        layout.addWidget(github_label)
        
        # Created by
        credit_label = QLabel("Created by vtajaros")
        credit_label.setObjectName("info")
        credit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credit_label)
        
        layout.addStretch()
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()
    
    def _check_for_updates(self):
        """Show check for updates dialog and check for updates."""
        self._show_update_check_dialog()
    
    def _check_for_updates_background(self):
        """Check for updates in the background on startup."""
        self._update_checker = UpdateCheckerThread()
        self._update_checker.update_checked.connect(self._on_background_update_checked)
        self._update_checker.error_occurred.connect(lambda e: None)  # Silently ignore errors on startup
        self._update_checker.start()
    
    def _on_background_update_checked(self, has_update, latest_version, download_url, release_notes):
        """Handle background update check result."""
        if has_update:
            self._show_update_available_notification(latest_version, download_url, release_notes)
    
    def _show_update_available_notification(self, latest_version, download_url, release_notes):
        """Show a notification that an update is available."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Update Available")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(f"A new version of ClearSight Docs is available!")
        msg.setInformativeText(
            f"Current version: {APP_VERSION}\n"
            f"Latest version: {latest_version}\n\n"
            "Would you like to download the update now?"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2c3e50;
            }
            QMessageBox QLabel {
                color: #ecf0f1;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl(download_url))
    
    def _show_update_check_dialog(self):
        """Show dialog for checking updates with progress."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Check for Updates")
        dialog.setFixedSize(480, 280)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #3498db;
            }
            QLabel#status {
                font-size: 13px;
                color: #ecf0f1;
            }
            QLabel#info {
                font-size: 12px;
                color: #bdc3c7;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton#download {
                background-color: #27ae60;
            }
            QPushButton#download:hover {
                background-color: #219a52;
            }
            QProgressBar {
                border: 1px solid #34495e;
                border-radius: 5px;
                background-color: #1a252f;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Checking for Updates")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Current version info
        current_version_label = QLabel(f"Current version: {APP_VERSION}")
        current_version_label.setObjectName("info")
        current_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(current_version_label)
        
        layout.addSpacing(10)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(progress_bar)
        
        # Status label
        status_label = QLabel("Connecting to GitHub...")
        status_label.setObjectName("status")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        layout.addStretch()
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        download_button = QPushButton("Download Update")
        download_button.setObjectName("download")
        download_button.setVisible(False)
        button_layout.addWidget(download_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Store download URL for the button
        dialog._download_url = None
        
        def on_update_checked(has_update, latest_version, download_url, release_notes):
            progress_bar.setRange(0, 100)
            progress_bar.setValue(100)
            
            if has_update:
                title_label.setText("Update Available! 🎉")
                title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
                status_label.setText(
                    f"A new version ({latest_version}) is available.\n"
                    f"You are currently running version {APP_VERSION}."
                )
                download_button.setVisible(True)
                dialog._download_url = download_url
            else:
                title_label.setText("You're Up to Date! ✓")
                title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
                status_label.setText(
                    f"You are running the latest version ({APP_VERSION}).\n"
                    "No updates are available at this time."
                )
        
        def on_error(error_message):
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            title_label.setText("Update Check Failed")
            title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c;")
            status_label.setText(f"{error_message}\n\nPlease check your internet connection and try again.")
        
        def on_download_clicked():
            if dialog._download_url:
                QDesktopServices.openUrl(QUrl(dialog._download_url))
                dialog.accept()
        
        download_button.clicked.connect(on_download_clicked)
        
        # Start update check
        checker = UpdateCheckerThread()
        checker.update_checked.connect(on_update_checked)
        checker.error_occurred.connect(on_error)
        checker.start()
        
        # Store reference to prevent garbage collection
        dialog._checker = checker
        
        dialog.exec()
    
    def _open_github(self):
        """Open the GitHub repository page."""
        QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL))
    
    def _open_github_profile(self):
        """Open the GitHub profile page."""
        QDesktopServices.openUrl(QUrl(GITHUB_PROFILE_URL))
        
    def _init_ui(self):
        """Initialize the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout (horizontal: sidebar + content)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Add pages
        self._add_pages()
        
    def _create_sidebar(self):
        """Create the sidebar with navigation buttons."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #2c3e50;
                border-right: 1px solid #34495e;
            }
            QPushButton {
                background-color: transparent;
                color: #ecf0f1;
                text-align: left;
                padding: 15px 20px;
                border: none;
                border-left: 3px solid transparent;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
                border-left: 3px solid #3498db;
            }
            QPushButton:checked {
                background-color: #34495e;
                border-left: 3px solid #3498db;
                font-weight: bold;
            }
            QLabel#title {
                color: #ecf0f1;
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
            }
            QLabel#subtitle {
                color: #95a5a6;
                font-size: 11px;
                padding: 0px 20px 20px 20px;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # App title
        title_label = QLabel("ClearSight Docs")
        title_label.setObjectName("title")
        sidebar_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Offline Document Utility")
        subtitle_label.setObjectName("subtitle")
        sidebar_layout.addWidget(subtitle_label)
        
        # Navigation buttons
        self.nav_buttons = []
        
        # Image to PDF button
        btn_image_to_pdf = QPushButton("📄 Image to PDF")
        btn_image_to_pdf.setCheckable(True)
        btn_image_to_pdf.setChecked(True)
        btn_image_to_pdf.clicked.connect(lambda: self._switch_page(0))
        self.nav_buttons.append(btn_image_to_pdf)
        sidebar_layout.addWidget(btn_image_to_pdf)
        
        # PDF to Images button
        btn_pdf_to_images = QPushButton("🖼️ PDF to Images")
        btn_pdf_to_images.setCheckable(True)
        btn_pdf_to_images.clicked.connect(lambda: self._switch_page(1))
        self.nav_buttons.append(btn_pdf_to_images)
        sidebar_layout.addWidget(btn_pdf_to_images)
        
        # PDF Merge button
        btn_pdf_merge = QPushButton("🔗 Merge PDFs")
        btn_pdf_merge.setCheckable(True)
        btn_pdf_merge.clicked.connect(lambda: self._switch_page(2))
        self.nav_buttons.append(btn_pdf_merge)
        sidebar_layout.addWidget(btn_pdf_merge)
        
        # PDF Split button
        btn_pdf_split = QPushButton("✂️ Split PDF")
        btn_pdf_split.setCheckable(True)
        btn_pdf_split.clicked.connect(lambda: self._switch_page(3))
        self.nav_buttons.append(btn_pdf_split)
        sidebar_layout.addWidget(btn_pdf_split)
        
        # PDF Delete Pages button
        btn_pdf_delete = QPushButton("🗑️ Delete PDF Pages")
        btn_pdf_delete.setCheckable(True)
        btn_pdf_delete.clicked.connect(lambda: self._switch_page(4))
        self.nav_buttons.append(btn_pdf_delete)
        sidebar_layout.addWidget(btn_pdf_delete)
        
        # PDF Extract Pages button
        btn_pdf_extract = QPushButton("📑 Extract PDF Pages")
        btn_pdf_extract.setCheckable(True)
        btn_pdf_extract.clicked.connect(lambda: self._switch_page(5))
        self.nav_buttons.append(btn_pdf_extract)
        sidebar_layout.addWidget(btn_pdf_extract)
        
        # PDF Compress button
        btn_pdf_compress = QPushButton("📦 Compress PDF")
        btn_pdf_compress.setCheckable(True)
        btn_pdf_compress.clicked.connect(lambda: self._switch_page(6))
        self.nav_buttons.append(btn_pdf_compress)
        sidebar_layout.addWidget(btn_pdf_compress)
        
        # OCR / PDF to Text button
        btn_ocr = QPushButton("🔍 OCR / PDF to Text")
        btn_ocr.setCheckable(True)
        btn_ocr.clicked.connect(lambda: self._switch_page(7))
        self.nav_buttons.append(btn_ocr)
        sidebar_layout.addWidget(btn_ocr)
        
        # PDF to Word button
        btn_pdf_to_word = QPushButton("📝 PDF to Word")
        btn_pdf_to_word.setCheckable(True)
        btn_pdf_to_word.clicked.connect(lambda: self._switch_page(8))
        self.nav_buttons.append(btn_pdf_to_word)
        sidebar_layout.addWidget(btn_pdf_to_word)
        
        # Add stretch to push buttons to top
        sidebar_layout.addStretch()
        
        # Version info at bottom
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setObjectName("subtitle")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(version_label)
        
        # Created by credit
        credit_label = QLabel("Created by vtajaros")
        credit_label.setObjectName("subtitle")
        credit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credit_label.setStyleSheet("color: #7f8c8d; font-size: 10px; padding: 5px 20px 15px 20px;")
        sidebar_layout.addWidget(credit_label)
        
        return sidebar
    
    def _add_pages(self):
        """Add tool pages to the stacked widget."""
        # Image to PDF page
        self.image_to_pdf_page = ImageToPdfPage()
        self.stacked_widget.addWidget(self.image_to_pdf_page)
        
        # PDF to Images page
        self.pdf_to_images_page = PdfToImagesPage()
        self.stacked_widget.addWidget(self.pdf_to_images_page)
        
        # PDF Merge page
        self.pdf_merge_page = PdfMergePage()
        self.stacked_widget.addWidget(self.pdf_merge_page)
        
        # PDF Split page
        self.pdf_split_page = PdfSplitPage()
        self.stacked_widget.addWidget(self.pdf_split_page)
        
        # PDF Delete Pages page
        self.pdf_delete_pages_page = PdfDeletePagesPage()
        self.stacked_widget.addWidget(self.pdf_delete_pages_page)
        
        # PDF Extract Pages page
        self.pdf_extract_pages_page = PdfExtractPagesPage()
        self.stacked_widget.addWidget(self.pdf_extract_pages_page)
        
        # PDF Compress page
        self.pdf_compress_page = PdfCompressPage()
        self.stacked_widget.addWidget(self.pdf_compress_page)
        
        # OCR page
        self.ocr_page = OCRPage()
        self.stacked_widget.addWidget(self.ocr_page)
        
        # PDF to Word page
        self.pdf_to_word_page = PDFToWordPage()
        self.stacked_widget.addWidget(self.pdf_to_word_page)
    
    def _switch_page(self, index):
        """Switch to the specified page and update button states."""
        self.stacked_widget.setCurrentIndex(index)
        
        # Update button checked states
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
