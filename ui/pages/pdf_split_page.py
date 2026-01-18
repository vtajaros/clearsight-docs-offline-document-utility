"""
PDF Split page.
Allows users to split a PDF by specifying page ranges.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFileDialog, QProgressBar, QMessageBox, QLineEdit,
    QRadioButton, QButtonGroup, QSpinBox, QFrame
)
from PySide6.QtCore import Qt

from services.pdf_split_service import PdfSplitService


class PdfSplitPage(QWidget):
    """Page for splitting PDF files."""
    
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
        title_label = QLabel("Split PDF Document")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        description_label = QLabel("Extract specific pages from a PDF document")
        description_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        layout.addWidget(description_label)
        
        # File selection group
        file_group = self._create_file_selection_group()
        layout.addWidget(file_group)
        
        # Split options group
        options_group = self._create_split_options_group()
        layout.addWidget(options_group)
        
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
        
        # Split button
        self.split_button = QPushButton("Split PDF")
        self.split_button.setEnabled(False)
        self.split_button.setMinimumHeight(45)
        self.split_button.setStyleSheet("""
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
        self.split_button.clicked.connect(self._split_pdf)
        layout.addWidget(self.split_button)
        
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
    
    def _create_split_options_group(self):
        """Create the split options group."""
        group = QGroupBox("Split Options")
        group_layout = QVBoxLayout(group)
        
        # Radio button group for split mode
        self.split_mode_group = QButtonGroup()
        
        # Page range option
        self.range_radio = QRadioButton("Extract page range")
        self.range_radio.setChecked(True)
        self.range_radio.toggled.connect(self._update_split_options)
        self.split_mode_group.addButton(self.range_radio)
        group_layout.addWidget(self.range_radio)
        
        # Page range input
        range_layout = QHBoxLayout()
        range_layout.setContentsMargins(30, 5, 0, 10)
        
        range_layout.addWidget(QLabel("From page:"))
        self.start_page_spin = QSpinBox()
        self.start_page_spin.setMinimum(1)
        self.start_page_spin.setMaximum(1)
        self.start_page_spin.setValue(1)
        range_layout.addWidget(self.start_page_spin)
        
        range_layout.addWidget(QLabel("To page:"))
        self.end_page_spin = QSpinBox()
        self.end_page_spin.setMinimum(1)
        self.end_page_spin.setMaximum(1)
        self.end_page_spin.setValue(1)
        range_layout.addWidget(self.end_page_spin)
        
        range_layout.addStretch()
        group_layout.addLayout(range_layout)
        
        # Split all pages option
        self.split_all_radio = QRadioButton("Split into individual pages")
        self.split_mode_group.addButton(self.split_all_radio)
        group_layout.addWidget(self.split_all_radio)
        
        help_label = QLabel("(Creates a separate PDF for each page)")
        help_label.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        help_label.setContentsMargins(30, 0, 0, 0)
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
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            self.total_pages = len(reader.pages)
            
            self.page_info_label.setText(f"📄 Total pages: {self.total_pages}")
            self.page_info_label.setVisible(True)
            
            # Update spinbox ranges
            self.start_page_spin.setMaximum(self.total_pages)
            self.end_page_spin.setMaximum(self.total_pages)
            self.end_page_spin.setValue(self.total_pages)
            
            self.split_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not read PDF:\n{str(e)}")
            self.selected_pdf = None
    
    def _update_split_options(self):
        """Update the enabled state of split option controls."""
        is_range_mode = self.range_radio.isChecked()
        self.start_page_spin.setEnabled(is_range_mode)
        self.end_page_spin.setEnabled(is_range_mode)
    
    def _split_pdf(self):
        """Split the PDF based on selected options."""
        if not self.selected_pdf:
            return
        
        is_range_mode = self.range_radio.isChecked()
        
        if is_range_mode:
            # Split by range
            start_page = self.start_page_spin.value()
            end_page = self.end_page_spin.value()
            
            if start_page > end_page:
                QMessageBox.warning(self, "Invalid Range", "Start page must be less than or equal to end page.")
                return
            
            # Ask user where to save the output PDF
            output_file, _ = QFileDialog.getSaveFileName(
                self,
                "Save Split PDF As",
                f"pages_{start_page}-{end_page}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not output_file:
                return
            
            self._perform_range_split(start_page, end_page, output_file)
            
        else:
            # Split into individual pages
            # Ask user to select output directory
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Output Directory"
            )
            
            if not output_dir:
                return
            
            self._perform_individual_split(output_dir)
    
    def _perform_range_split(self, start_page: int, end_page: int, output_file: str):
        """Perform PDF split by page range."""
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(False)
        self.split_button.setEnabled(False)
        
        try:
            service = PdfSplitService()
            success = service.split_by_range(
                self.selected_pdf,
                output_file,
                start_page,
                end_page
            )
            
            self.progress_bar.setValue(100)
            
            if success:
                self.status_label.setText(f"✅ PDF split successfully: {Path(output_file).name}")
                self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.status_label.setVisible(True)
                
                # Ask if user wants to open the split PDF
                reply = QMessageBox.question(
                    self,
                    "Success",
                    f"PDF split successfully!\n\nOpen the PDF now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    import os
                    os.startfile(output_file)
            else:
                self.status_label.setText("❌ Failed to split PDF")
                self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                self.status_label.setVisible(True)
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.status_label.setVisible(True)
            QMessageBox.critical(self, "Error", f"Failed to split PDF:\n{str(e)}")
        
        finally:
            self.split_button.setEnabled(True)
    
    def _perform_individual_split(self, output_dir: str):
        """Split PDF into individual pages."""
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(False)
        self.split_button.setEnabled(False)
        
        try:
            service = PdfSplitService()
            success = service.split_into_pages(
                self.selected_pdf,
                output_dir
            )
            
            self.progress_bar.setValue(100)
            
            if success:
                self.status_label.setText(f"✅ PDF split into {self.total_pages} individual pages")
                self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.status_label.setVisible(True)
                
                # Ask if user wants to open the output folder
                reply = QMessageBox.question(
                    self,
                    "Success",
                    f"PDF split into {self.total_pages} individual pages!\n\nOpen output folder?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    import os
                    os.startfile(output_dir)
            else:
                self.status_label.setText("❌ Failed to split PDF")
                self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                self.status_label.setVisible(True)
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.status_label.setVisible(True)
            QMessageBox.critical(self, "Error", f"Failed to split PDF:\n{str(e)}")
        
        finally:
            self.split_button.setEnabled(True)
