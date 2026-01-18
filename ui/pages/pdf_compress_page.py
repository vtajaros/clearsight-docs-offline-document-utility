"""
PDF Compress page.
Allows users to compress PDF files to reduce file size.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFileDialog, QProgressBar, QMessageBox,
    QFrame, QRadioButton, QButtonGroup, QSlider
)
from PySide6.QtCore import Qt, QThread, Signal

from services.pdf_compress_service import PdfCompressService


class CompressionWorker(QThread):
    """Worker thread for PDF compression."""
    progress = Signal(int, int)  # current_page, total_pages
    finished = Signal(dict)  # result dictionary
    error = Signal(str)  # error message
    
    def __init__(self, pdf_path: str, output_path: str, compression_level: str):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.compression_level = compression_level
        
    def run(self):
        try:
            service = PdfCompressService()
            result = service.compress_pdf(
                self.pdf_path,
                self.output_path,
                self.compression_level,
                progress_callback=self._progress_callback
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def _progress_callback(self, current: int, total: int):
        self.progress.emit(current, total)


class PdfCompressPage(QWidget):
    """Page for compressing PDF files."""
    
    def __init__(self):
        super().__init__()
        self.selected_pdf = None
        self.total_pages = 0
        self.original_size = 0
        self.worker = None
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Page title
        title_label = QLabel("Compress PDF")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        description_label = QLabel("Reduce PDF file size while maintaining quality")
        description_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        layout.addWidget(description_label)
        
        # File selection group
        file_group = self._create_file_selection_group()
        layout.addWidget(file_group)
        
        # Compression options group
        options_group = self._create_compression_options_group()
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
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Compress button
        self.compress_button = QPushButton("Compress PDF")
        self.compress_button.setEnabled(False)
        self.compress_button.setMinimumHeight(45)
        self.compress_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
            QPushButton:disabled {
                background-color: #5d6d7e;
                color: #aeb6bf;
            }
        """)
        self.compress_button.clicked.connect(self._compress_pdf)
        layout.addWidget(self.compress_button)
        
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
                border-color: #27ae60;
                background-color: #eafaf1;
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
        
        # File info label
        self.file_info_label = QLabel("")
        self.file_info_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        self.file_info_label.setVisible(False)
        group_layout.addWidget(self.file_info_label)
        
        return group
    
    def _create_compression_options_group(self):
        """Create the compression options group."""
        group = QGroupBox("Compression Level")
        group_layout = QVBoxLayout(group)
        
        # Description
        description = QLabel(
            "Choose a compression level. Higher compression may slightly reduce quality."
        )
        description.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        description.setWordWrap(True)
        group_layout.addWidget(description)
        
        # Radio button group for compression level
        self.compression_group = QButtonGroup()
        
        # Low compression option
        low_row = QHBoxLayout()
        self.low_radio = QRadioButton("Low Compression")
        self.low_radio.setToolTip("Minimal compression - best quality, smallest size reduction")
        self.compression_group.addButton(self.low_radio)
        low_row.addWidget(self.low_radio)
        self.low_estimate_label = QLabel("")
        self.low_estimate_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px;")
        low_row.addWidget(self.low_estimate_label)
        low_row.addStretch()
        group_layout.addLayout(low_row)
        
        low_desc = QLabel("   Best quality, minimal size reduction. Removes duplicate objects.")
        low_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        group_layout.addWidget(low_desc)
        
        # Medium compression option (default)
        medium_row = QHBoxLayout()
        self.medium_radio = QRadioButton("Medium Compression (Recommended)")
        self.medium_radio.setChecked(True)
        self.medium_radio.setToolTip("Balanced compression - good quality with noticeable size reduction")
        self.compression_group.addButton(self.medium_radio)
        medium_row.addWidget(self.medium_radio)
        self.medium_estimate_label = QLabel("")
        self.medium_estimate_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px;")
        medium_row.addWidget(self.medium_estimate_label)
        medium_row.addStretch()
        group_layout.addLayout(medium_row)
        
        medium_desc = QLabel("   Good balance of quality and size. Compresses content streams.")
        medium_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        group_layout.addWidget(medium_desc)
        
        # High compression option
        high_row = QHBoxLayout()
        self.high_radio = QRadioButton("High Compression")
        self.high_radio.setToolTip("Maximum compression - may slightly affect quality")
        self.compression_group.addButton(self.high_radio)
        high_row.addWidget(self.high_radio)
        self.high_estimate_label = QLabel("")
        self.high_estimate_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px;")
        high_row.addWidget(self.high_estimate_label)
        high_row.addStretch()
        group_layout.addLayout(high_row)
        
        high_desc = QLabel("   Maximum size reduction. Best for documents with lots of text.")
        high_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        group_layout.addWidget(high_desc)
        
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
        
        # Get PDF info
        try:
            service = PdfCompressService()
            info = service.get_pdf_info(file_path)
            
            self.total_pages = info["page_count"]
            self.original_size = info["file_size"]
            
            size_str = service.format_file_size(self.original_size)
            self.file_info_label.setText(f"📄 {self.total_pages} pages  •  📦 Current size: {size_str}")
            self.file_info_label.setVisible(True)
            
            # Update estimated sizes for each compression level
            self._update_size_estimates(service)
            
            self.compress_button.setEnabled(True)
            self.status_label.setVisible(False)
            
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not read PDF:\n{str(e)}")
            self.selected_pdf = None
    
    def _update_size_estimates(self, service):
        """Update the estimated file sizes for each compression level."""
        # Estimate compression ratios based on typical PDF content
        # These are rough estimates - actual results will vary
        low_estimate = int(self.original_size * 0.85)  # ~15% reduction
        medium_estimate = int(self.original_size * 0.65)  # ~35% reduction
        high_estimate = int(self.original_size * 0.45)  # ~55% reduction
        
        self.low_estimate_label.setText(f"≈ {service.format_file_size(low_estimate)}")
        self.medium_estimate_label.setText(f"≈ {service.format_file_size(medium_estimate)}")
        self.high_estimate_label.setText(f"≈ {service.format_file_size(high_estimate)}")
    
    def _get_compression_level(self) -> str:
        """Get the selected compression level."""
        if self.low_radio.isChecked():
            return "low"
        elif self.high_radio.isChecked():
            return "high"
        else:
            return "medium"
    
    def _compress_pdf(self):
        """Compress the PDF."""
        if not self.selected_pdf:
            return
        
        # Ask user where to save the output PDF
        default_name = Path(self.selected_pdf).stem + "_compressed.pdf"
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Compressed PDF As",
            default_name,
            "PDF Files (*.pdf)"
        )
        
        if not output_file:
            return
        
        self._perform_compression(output_file)
    
    def _perform_compression(self, output_file: str):
        """Perform the PDF compression."""
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(self.total_pages)
        self.status_label.setVisible(False)
        self.compress_button.setEnabled(False)
        
        compression_level = self._get_compression_level()
        
        # Create and start worker thread
        self.worker = CompressionWorker(
            self.selected_pdf,
            output_file,
            compression_level
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(lambda result: self._on_finished(result, output_file))
        self.worker.error.connect(self._on_error)
        self.worker.start()
    
    def _on_progress(self, current: int, total: int):
        """Handle progress updates."""
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"Processing page {current}/{total}...")
    
    def _on_finished(self, result: dict, output_file: str):
        """Handle compression completion."""
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.progress_bar.setFormat("Complete!")
        
        service = PdfCompressService()
        original_str = service.format_file_size(result["original_size"])
        new_str = service.format_file_size(result["new_size"])
        reduction_str = service.format_file_size(result["size_reduction"])
        
        if result["size_reduction"] > 0:
            self.status_label.setText(
                f"✅ Compression complete!\n"
                f"📦 Original: {original_str}  →  New: {new_str}\n"
                f"💾 Saved: {reduction_str} ({result['reduction_percentage']:.1f}% reduction)"
            )
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.status_label.setText(
                f"ℹ️ Compression complete, but file size did not decrease.\n"
                f"📦 Original: {original_str}  →  New: {new_str}\n"
                f"The PDF may already be optimized."
            )
            self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        
        self.status_label.setVisible(True)
        self.compress_button.setEnabled(True)
        
        # Ask if user wants to open the compressed PDF
        reply = QMessageBox.question(
            self,
            "Compression Complete",
            f"PDF compressed successfully!\n\n"
            f"Original: {original_str}\n"
            f"Compressed: {new_str}\n"
            f"Saved: {reduction_str} ({result['reduction_percentage']:.1f}%)\n\n"
            f"Open the compressed PDF now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            import os
            os.startfile(output_file)
    
    def _on_error(self, error_message: str):
        """Handle compression error."""
        self.status_label.setText(f"❌ Error: {error_message}")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.status_label.setVisible(True)
        self.compress_button.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to compress PDF:\n{error_message}")
