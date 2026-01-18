"""
PDF to Images conversion page.
Converts PDF pages to images and saves them as a ZIP file.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFileDialog, QProgressBar, QMessageBox,
    QComboBox, QFrame
)
from PySide6.QtCore import Qt

from services.pdf_to_images_service import PdfToImagesService


class PdfToImagesPage(QWidget):
    """Page for converting PDF files to images."""
    
    def __init__(self):
        super().__init__()
        self.selected_pdf = None
        self.total_pages = 0
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Page title
        title_label = QLabel("PDF to Images")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        description_label = QLabel("Convert each page of a PDF to an image. Output is saved as a ZIP file.")
        description_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        layout.addWidget(description_label)
        
        # File selection group
        file_group = self._create_file_selection_group()
        layout.addWidget(file_group)
        
        # Settings group
        settings_group = self._create_settings_group()
        layout.addWidget(settings_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # Convert button
        self.convert_button = QPushButton("Convert to Images")
        self.convert_button.setEnabled(False)
        self.convert_button.setMinimumHeight(45)
        self.convert_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #5d6d7e;
                color: #aeb6bf;
            }
        """)
        self.convert_button.clicked.connect(self._convert_to_images)
        layout.addWidget(self.convert_button)
        
        layout.addStretch()
        
    def _create_file_selection_group(self):
        """Create the file selection group with drop zone."""
        group = QGroupBox("Select PDF File")
        group_layout = QVBoxLayout(group)
        
        # Drop zone frame
        self.drop_zone = QFrame()
        self.drop_zone.setAcceptDrops(True)
        self.drop_zone.setMinimumHeight(100)
        self.drop_zone.setStyleSheet("""
            QFrame {
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                background-color: #ecf0f1;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #e8f4f8;
            }
        """)
        
        # Drop zone layout
        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.file_label = QLabel("Drag and drop a PDF file here\nor click Browse...")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #2c3e50; font-style: italic; font-weight: bold; border: none; background: transparent;")
        drop_layout.addWidget(self.file_label)
        
        # Set up drop events
        self.drop_zone.dragEnterEvent = self._drag_enter_event
        self.drop_zone.dragMoveEvent = self._drag_move_event
        self.drop_zone.dropEvent = self._drop_event
        
        group_layout.addWidget(self.drop_zone)
        
        # Browse button row
        button_row = QHBoxLayout()
        button_row.addStretch()
        
        select_button = QPushButton("Browse...")
        select_button.clicked.connect(self._select_pdf)
        button_row.addWidget(select_button)
        
        group_layout.addLayout(button_row)
        
        # Page info label
        self.page_info_label = QLabel("")
        self.page_info_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        self.page_info_label.setVisible(False)
        group_layout.addWidget(self.page_info_label)
        
        return group
    
    def _create_settings_group(self):
        """Create the settings group."""
        group = QGroupBox("Output Settings")
        group_layout = QHBoxLayout(group)
        
        # Image format
        format_label = QLabel("Image Format:")
        group_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG"])
        self.format_combo.setCurrentText("PNG")
        self.format_combo.setToolTip("PNG is lossless (larger files), JPG is compressed (smaller files)")
        group_layout.addWidget(self.format_combo)
        
        group_layout.addSpacing(20)
        
        # Quality dropdown
        quality_label = QLabel("Quality:")
        group_layout.addWidget(quality_label)
        
        self.quality_combo = QComboBox()
        self.quality_combo.setMinimumWidth(140)
        # Quality presets: (label, dpi)
        self.quality_options = {
            "Screen / Web (72 DPI)": 72,
            "Low (100 DPI)": 100,
            "Medium (150 DPI)": 150,
            "High (300 DPI)": 300
        }
        self.quality_combo.addItems(self.quality_options.keys())
        self.quality_combo.setCurrentText("Medium (150 DPI)")
        self.quality_combo.setToolTip(
            "Screen/Web: Quick previews, emails, websites\n"
            "Low: Small file size, basic viewing\n"
            "Medium: Readable text, sharing\n"
            "High: Print-quality, archiving"
        )
        group_layout.addWidget(self.quality_combo)
        
        group_layout.addStretch()
        
        # Help text
        help_label = QLabel("📁 Output: ZIP file containing one image per page")
        help_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        group_layout.addWidget(help_label)
        
        return group
    
    def _drag_enter_event(self, event):
        """Handle drag enter event for file drops."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def _drag_move_event(self, event):
        """Handle drag move event for file drops."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def _drop_event(self, event):
        """Handle drop event for file drops."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    self._load_pdf(file_path)
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def _select_pdf(self):
        """Open file dialog to select a PDF."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF File",
            "",
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            self._load_pdf(file_path)
    
    def _load_pdf(self, file_path: str):
        """Load a PDF file and update the UI."""
        self.selected_pdf = file_path
        self.file_label.setText(f"📄 {Path(file_path).name}")
        self.file_label.setStyleSheet("color: #2c3e50; font-style: normal; font-weight: bold; border: none; background: transparent;")
        
        # Get page count
        try:
            service = PdfToImagesService()
            self.total_pages = service.get_page_count(file_path)
            
            self.page_info_label.setText(f"📄 Total pages: {self.total_pages}")
            self.page_info_label.setVisible(True)
            
            self.convert_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not read PDF:\n{str(e)}")
            self.selected_pdf = None
    
    def _convert_to_images(self):
        """Convert the PDF to images and save as ZIP."""
        if not self.selected_pdf:
            return
        
        # Get settings
        image_format = self.format_combo.currentText()
        quality_text = self.quality_combo.currentText()
        dpi = self.quality_options[quality_text]
        
        # Suggest output filename
        base_name = Path(self.selected_pdf).stem
        suggested_name = f"{base_name}_images.zip"
        
        # Ask user where to save the ZIP
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save ZIP As",
            suggested_name,
            "ZIP Files (*.zip)"
        )
        
        if not output_file:
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(False)
        self.convert_button.setEnabled(False)
        
        try:
            service = PdfToImagesService()
            service.convert_pdf_to_images_zip(
                self.selected_pdf,
                output_file,
                image_format=image_format,
                dpi=dpi
            )
            
            self.progress_bar.setValue(100)
            
            self.status_label.setText(f"✅ ZIP created successfully: {Path(output_file).name}")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.status_label.setVisible(True)
            
            # Ask if user wants to open the ZIP file
            reply = QMessageBox.question(
                self,
                "Success",
                f"PDF converted to {self.total_pages} images!\n\nOpen the ZIP file now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import os
                os.startfile(output_file)
                
        except Exception as e:
            self.progress_bar.setValue(0)
            
            error_msg = str(e)
            
            self.status_label.setText(f"❌ Error: Conversion failed")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.status_label.setVisible(True)
            
            QMessageBox.critical(
                self,
                "Conversion Failed",
                f"Failed to convert PDF to images:\n\n{error_msg}\n\nPlease check the console for detailed error information."
            )
        
        finally:
            self.convert_button.setEnabled(True)
