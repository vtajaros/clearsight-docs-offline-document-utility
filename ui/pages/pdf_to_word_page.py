"""
PDF to Word Page for converting PDFs to Word documents.
Provides UI for PDF to DOCX conversion with OCR support.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFileDialog, QProgressBar, QMessageBox,
    QComboBox, QFrame, QCheckBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QThread, Signal

from services.pdf_to_word_service import (
    PDFToWordService, PDFToWordSettings, ConversionResult,
    ConversionMode
)
from services.ocr_service import AccuracyMode


class ConversionWorker(QThread):
    """Worker thread for PDF to Word conversion."""
    
    progress = Signal(int, int, str)
    finished = Signal(object)
    
    def __init__(
        self,
        service: PDFToWordService,
        pdf_path: str,
        output_path: str,
        settings: PDFToWordSettings
    ):
        super().__init__()
        self.service = service
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.settings = settings
    
    def run(self):
        """Run conversion in background thread."""
        result = self.service.convert(
            self.pdf_path,
            self.output_path,
            self.settings,
            progress_callback=self._on_progress
        )
        self.finished.emit(result)
    
    def _on_progress(self, current: int, total: int, message: str):
        """Emit progress signal."""
        self.progress.emit(current, total, message)


class PDFToWordPage(QWidget):
    """Page for PDF to Word conversion."""
    
    # Language display names and codes for OCR
    LANGUAGES = {
        "English": "eng",
        "French": "fra",
        "German": "deu",
        "Spanish": "spa",
        "Italian": "ita",
        "Portuguese": "por",
        "Dutch": "nld",
        "Russian": "rus",
        "Chinese (Simplified)": "chi_sim",
        "Chinese (Traditional)": "chi_tra",
        "Japanese": "jpn",
        "Korean": "kor",
        "Arabic": "ara",
    }
    
    # Quality presets
    QUALITY_PRESETS = {
        "Standard (300 DPI)": 300,
        "High (400 DPI)": 400,
        "Maximum (600 DPI)": 600,
    }
    
    def __init__(self):
        super().__init__()
        self.selected_pdf = None
        self.total_pages = 0
        self.service = PDFToWordService()
        self.worker = None
        self._init_ui()
        self._check_tesseract()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Page title
        title_label = QLabel("PDF to Word")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        description_label = QLabel(
            "Convert PDF documents to editable Word (.docx) format. "
            "Supports OCR for scanned PDFs and preserves formatting when possible."
        )
        description_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        
        # Tesseract status info (for OCR features)
        self.tesseract_info = QLabel(
            "ℹ️ Tesseract OCR not detected. OCR features will be limited."
        )
        self.tesseract_info.setStyleSheet(
            "color: #f39c12; padding: 10px; "
            "background-color: #fef9e7; border-radius: 5px;"
        )
        self.tesseract_info.setVisible(False)
        layout.addWidget(self.tesseract_info)
        
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
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Convert button
        self.convert_button = QPushButton("Convert to Word Document")
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
        self.convert_button.clicked.connect(self._start_conversion)
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
                background-color: #ebf5fb;
            }
        """)
        
        # Drop zone layout
        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.file_label = QLabel("Drag and drop a PDF file here\nor click Browse...")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet(
            "color: #2c3e50; font-style: italic; font-weight: bold; border: none; background: transparent;"
        )
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
        
        # PDF info label
        self.pdf_info_label = QLabel("")
        self.pdf_info_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        self.pdf_info_label.setVisible(False)
        group_layout.addWidget(self.pdf_info_label)
        
        # Text detection info
        self.text_detection_label = QLabel("")
        self.text_detection_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.text_detection_label.setVisible(False)
        group_layout.addWidget(self.text_detection_label)
        
        return group
    
    def _create_settings_group(self):
        """Create the conversion settings group."""
        group = QGroupBox("Conversion Settings")
        group_layout = QVBoxLayout(group)
        
        # First row: Conversion mode
        row1 = QHBoxLayout()
        
        mode_label = QLabel("Conversion Mode:")
        row1.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.setMinimumWidth(200)
        self.mode_combo.addItem("Auto (detect if OCR needed)", ConversionMode.AUTO)
        self.mode_combo.addItem("Text Only (faster, no OCR)", ConversionMode.TEXT_ONLY)
        self.mode_combo.addItem("Always Use OCR", ConversionMode.OCR_ALWAYS)
        self.mode_combo.addItem("Preserve Layout (as images)", ConversionMode.PRESERVE_LAYOUT)
        self.mode_combo.setToolTip(
            "Auto: Automatically uses OCR if the PDF appears to be scanned.\n"
            "Text Only: Extracts text directly, faster but won't work for scanned PDFs.\n"
            "Always OCR: Forces OCR even if text exists, useful for poor quality PDFs.\n"
            "Preserve Layout: Converts pages to images, best for complex layouts."
        )
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        row1.addWidget(self.mode_combo)
        
        row1.addStretch()
        group_layout.addLayout(row1)
        
        # OCR Settings section (shown/hidden based on mode)
        self.ocr_settings_widget = QWidget()
        ocr_layout = QVBoxLayout(self.ocr_settings_widget)
        ocr_layout.setContentsMargins(0, 10, 0, 0)
        
        # OCR settings row
        ocr_row = QHBoxLayout()
        
        # Language selector
        lang_label = QLabel("OCR Language:")
        ocr_row.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.setMinimumWidth(150)
        for display_name in self.LANGUAGES.keys():
            self.language_combo.addItem(display_name)
        self.language_combo.setCurrentText("English")
        self.language_combo.setToolTip("Select the language of the text in the PDF for OCR")
        ocr_row.addWidget(self.language_combo)
        
        ocr_row.addSpacing(20)
        
        # Quality selector
        quality_label = QLabel("Quality:")
        ocr_row.addWidget(quality_label)
        
        self.quality_combo = QComboBox()
        self.quality_combo.setMinimumWidth(150)
        for preset in self.QUALITY_PRESETS.keys():
            self.quality_combo.addItem(preset)
        self.quality_combo.setCurrentText("Standard (300 DPI)")
        self.quality_combo.setToolTip("Higher DPI = better quality but slower")
        ocr_row.addWidget(self.quality_combo)
        
        ocr_row.addStretch()
        ocr_layout.addLayout(ocr_row)
        
        # Accuracy mode row
        accuracy_row = QHBoxLayout()
        
        accuracy_label = QLabel("OCR Mode:")
        accuracy_row.addWidget(accuracy_label)
        
        self.accuracy_group = QButtonGroup(self)
        
        self.fast_radio = QRadioButton("Fast")
        self.fast_radio.setToolTip("Minimal preprocessing - fastest")
        self.accuracy_group.addButton(self.fast_radio)
        accuracy_row.addWidget(self.fast_radio)
        
        self.balanced_radio = QRadioButton("Balanced")
        self.balanced_radio.setChecked(True)
        self.balanced_radio.setToolTip("Moderate preprocessing - good balance")
        self.accuracy_group.addButton(self.balanced_radio)
        accuracy_row.addWidget(self.balanced_radio)
        
        self.accurate_radio = QRadioButton("Accurate")
        self.accurate_radio.setToolTip("Full preprocessing - slowest but most accurate")
        self.accuracy_group.addButton(self.accurate_radio)
        accuracy_row.addWidget(self.accurate_radio)
        
        accuracy_row.addStretch()
        ocr_layout.addLayout(accuracy_row)
        
        group_layout.addWidget(self.ocr_settings_widget)
        
        # Options row
        options_row = QHBoxLayout()
        
        self.include_images_check = QCheckBox("Include images from PDF")
        self.include_images_check.setChecked(True)
        self.include_images_check.setToolTip("Extract and embed images from the PDF")
        options_row.addWidget(self.include_images_check)
        
        self.preserve_formatting_check = QCheckBox("Preserve text formatting")
        self.preserve_formatting_check.setChecked(True)
        self.preserve_formatting_check.setToolTip("Try to preserve bold, italic, font sizes, etc.")
        options_row.addWidget(self.preserve_formatting_check)
        
        options_row.addStretch()
        group_layout.addLayout(options_row)
        
        return group
    
    def _check_tesseract(self):
        """Check if Tesseract is available."""
        if not self.service.is_tesseract_available():
            self.tesseract_info.setVisible(True)
    
    def _on_mode_changed(self, index):
        """Handle conversion mode change."""
        mode = self.mode_combo.currentData()
        
        # Show/hide OCR settings based on mode
        show_ocr = mode in [ConversionMode.AUTO, ConversionMode.OCR_ALWAYS, ConversionMode.PRESERVE_LAYOUT]
        self.ocr_settings_widget.setVisible(show_ocr)
        
        # Show/hide formatting options based on mode
        show_formatting = mode != ConversionMode.PRESERVE_LAYOUT
        self.preserve_formatting_check.setVisible(show_formatting)
        self.include_images_check.setVisible(mode != ConversionMode.PRESERVE_LAYOUT)
    
    def _drag_enter_event(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def _drag_move_event(self, event):
        """Handle drag move event."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def _drop_event(self, event):
        """Handle drop event."""
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
        """Load and analyze a PDF file."""
        self.selected_pdf = file_path
        
        # Update file label
        file_name = Path(file_path).name
        self.file_label.setText(f"📄 {file_name}")
        self.file_label.setStyleSheet(
            "color: #2c3e50; font-weight: bold; border: none; background: transparent;"
        )
        
        # Check PDF for text
        has_text, page_count = self.service.pdf_has_text(file_path)
        self.total_pages = page_count
        
        # Update info labels
        self.pdf_info_label.setText(f"Pages: {page_count}")
        self.pdf_info_label.setVisible(True)
        
        if has_text:
            self.text_detection_label.setText(
                "✓ This PDF contains extractable text. Text extraction will be fast."
            )
            self.text_detection_label.setStyleSheet("color: #27ae60; font-style: italic;")
        else:
            self.text_detection_label.setText(
                "⚠ This PDF appears to be scanned/image-based. OCR will be used."
            )
            self.text_detection_label.setStyleSheet("color: #f39c12; font-style: italic;")
        
        self.text_detection_label.setVisible(True)
        
        # Enable convert button
        self.convert_button.setEnabled(True)
        
        # Hide previous status
        self.status_label.setVisible(False)
    
    def _get_settings(self) -> PDFToWordSettings:
        """Get current settings from UI."""
        # Get conversion mode
        conversion_mode = self.mode_combo.currentData()
        
        # Get language
        lang_display = self.language_combo.currentText()
        lang_code = self.LANGUAGES.get(lang_display, "eng")
        
        # Get DPI
        quality_text = self.quality_combo.currentText()
        dpi = self.QUALITY_PRESETS.get(quality_text, 300)
        
        # Get accuracy mode
        if self.fast_radio.isChecked():
            accuracy_mode = AccuracyMode.FAST
        elif self.accurate_radio.isChecked():
            accuracy_mode = AccuracyMode.ACCURATE
        else:
            accuracy_mode = AccuracyMode.BALANCED
        
        return PDFToWordSettings(
            conversion_mode=conversion_mode,
            language=lang_code,
            dpi=dpi,
            accuracy_mode=accuracy_mode,
            include_images=self.include_images_check.isChecked(),
            preserve_formatting=self.preserve_formatting_check.isChecked()
        )
    
    def _start_conversion(self):
        """Start the conversion process."""
        if not self.selected_pdf:
            return
        
        settings = self._get_settings()
        
        # Check if OCR is needed but not available
        if settings.conversion_mode == ConversionMode.OCR_ALWAYS and not self.service.is_tesseract_available():
            QMessageBox.warning(
                self,
                "Tesseract Not Found",
                "OCR mode requires Tesseract to be installed.\n"
                "Please install Tesseract or choose a different conversion mode."
            )
            return
        
        # Suggest output filename
        base_name = Path(self.selected_pdf).stem
        suggested_name = f"{base_name}.docx"
        
        # Ask where to save
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Word Document As",
            suggested_name,
            "Word Documents (*.docx)"
        )
        
        if not output_path:
            return
        
        # Ensure .docx extension
        if not output_path.lower().endswith('.docx'):
            output_path += '.docx'
        
        # Disable UI during conversion
        self.convert_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(False)
        
        # Start worker thread
        self.worker = ConversionWorker(
            self.service,
            self.selected_pdf,
            output_path,
            settings
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_conversion_finished)
        self.worker.start()
    
    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress updates."""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.progress_bar.setFormat(f"{message} ({percent}%)")
        else:
            self.progress_bar.setFormat(message)
    
    def _on_conversion_finished(self, result: ConversionResult):
        """Handle conversion completion."""
        self.progress_bar.setVisible(False)
        self.convert_button.setEnabled(True)
        
        if result.success:
            ocr_info = " (used OCR)" if result.used_ocr else ""
            self.status_label.setText(
                f"✓ Successfully converted {result.pages_converted} pages{ocr_info}!\n"
                f"Saved to: {result.output_path}"
            )
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            # Ask if user wants to open the file
            reply = QMessageBox.question(
                self,
                "Conversion Complete",
                f"Successfully converted to Word document!\n\n"
                f"Would you like to open the file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import subprocess
                import os
                # Open the file directly with default application
                os.startfile(result.output_path)
        else:
            self.status_label.setText(f"✗ Conversion failed: {result.error_message}")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
            QMessageBox.critical(
                self,
                "Conversion Failed",
                f"Failed to convert PDF to Word:\n\n{result.error_message}"
            )
        
        self.status_label.setVisible(True)
        self.worker = None
