"""
OCR Page for PDF text extraction and searchable PDF creation.
Provides UI for converting scanned/image-based PDFs to text or searchable PDFs.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFileDialog, QProgressBar, QMessageBox,
    QComboBox, QFrame, QCheckBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QThread, Signal

from services.ocr_service import (
    OCRService, OCRSettings, OCRResult,
    OutputFormat, AccuracyMode
)


class OCRWorker(QThread):
    """Worker thread for OCR processing to keep UI responsive."""
    
    # Signals for progress and completion
    progress = Signal(int, int, str)  # current_page, total_pages, message
    finished = Signal(object)  # OCRResult
    
    def __init__(
        self,
        service: OCRService,
        pdf_path: str,
        output_path: str,
        settings: OCRSettings
    ):
        super().__init__()
        self.service = service
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.settings = settings
    
    def run(self):
        """Run OCR processing in background thread."""
        result = self.service.process_pdf(
            self.pdf_path,
            self.output_path,
            self.settings,
            progress_callback=self._on_progress
        )
        self.finished.emit(result)
    
    def _on_progress(self, current: int, total: int, message: str):
        """Emit progress signal."""
        self.progress.emit(current, total, message)


class OCRPage(QWidget):
    """Page for OCR / PDF to Text conversion."""
    
    # Language display names and codes
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
    
    # Quality presets with minimum 300 DPI for OCR
    QUALITY_PRESETS = {
        "Standard (300 DPI)": 300,
        "High (400 DPI)": 400,
        "Maximum (600 DPI)": 600,
    }
    
    def __init__(self):
        super().__init__()
        self.selected_pdf = None
        self.total_pages = 0
        self.ocr_service = OCRService()
        self.worker = None
        self._init_ui()
        self._check_tesseract()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Page title
        title_label = QLabel("OCR / PDF to Text")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        description_label = QLabel(
            "Extract text from scanned PDFs using OCR, or create searchable PDFs with text layers."
        )
        description_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        
        # Tesseract status warning (hidden by default)
        self.tesseract_warning = QLabel(
            "⚠️ Tesseract OCR not found! Please install Tesseract and add it to your PATH."
        )
        self.tesseract_warning.setStyleSheet(
            "color: #e74c3c; font-weight: bold; padding: 10px; "
            "background-color: #fadbd8; border-radius: 5px;"
        )
        self.tesseract_warning.setVisible(False)
        layout.addWidget(self.tesseract_warning)
        
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
        self.convert_button = QPushButton("Extract Text / Create Searchable PDF")
        self.convert_button.setEnabled(False)
        self.convert_button.setMinimumHeight(45)
        self.convert_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #5d6d7e;
                color: #aeb6bf;
            }
        """)
        self.convert_button.clicked.connect(self._start_ocr)
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
                border-color: #9b59b6;
                background-color: #f5eef8;
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
        """Create the OCR settings group."""
        group = QGroupBox("OCR Settings")
        group_layout = QVBoxLayout(group)
        
        # First row: Language and Quality
        row1 = QHBoxLayout()
        
        # Language selector
        lang_label = QLabel("Language:")
        row1.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.setMinimumWidth(150)
        for display_name in self.LANGUAGES.keys():
            self.language_combo.addItem(display_name)
        self.language_combo.setCurrentText("English")
        self.language_combo.setToolTip("Select the language of the text in the PDF")
        row1.addWidget(self.language_combo)
        
        row1.addSpacing(30)
        
        # Quality/DPI selector
        quality_label = QLabel("Quality:")
        row1.addWidget(quality_label)
        
        self.quality_combo = QComboBox()
        self.quality_combo.setMinimumWidth(150)
        for preset in self.QUALITY_PRESETS.keys():
            self.quality_combo.addItem(preset)
        self.quality_combo.setCurrentText("Standard (300 DPI)")
        self.quality_combo.setToolTip(
            "Higher DPI = better accuracy but slower processing.\n"
            "300 DPI is the minimum for good OCR results."
        )
        row1.addWidget(self.quality_combo)
        
        row1.addStretch()
        group_layout.addLayout(row1)
        
        # Second row: Output format
        row2 = QHBoxLayout()
        
        format_label = QLabel("Output Format:")
        row2.addWidget(format_label)
        
        self.format_group = QButtonGroup(self)
        
        self.txt_radio = QRadioButton("Plain Text (.txt)")
        self.txt_radio.setChecked(True)
        self.txt_radio.setToolTip("Extract text and save as a plain text file")
        self.format_group.addButton(self.txt_radio)
        row2.addWidget(self.txt_radio)
        
        self.pdf_radio = QRadioButton("Searchable PDF")
        self.pdf_radio.setToolTip(
            "Create a PDF with invisible text layer for searching and copying"
        )
        self.format_group.addButton(self.pdf_radio)
        row2.addWidget(self.pdf_radio)
        
        row2.addStretch()
        group_layout.addLayout(row2)
        
        # Third row: Accuracy mode
        row3 = QHBoxLayout()
        
        accuracy_label = QLabel("Processing Mode:")
        row3.addWidget(accuracy_label)
        
        self.accuracy_group = QButtonGroup(self)
        
        self.fast_radio = QRadioButton("Fast")
        self.fast_radio.setToolTip("Minimal image preprocessing - fastest but may be less accurate")
        self.accuracy_group.addButton(self.fast_radio)
        row3.addWidget(self.fast_radio)
        
        self.balanced_radio = QRadioButton("Balanced")
        self.balanced_radio.setChecked(True)
        self.balanced_radio.setToolTip("Moderate preprocessing - good balance of speed and accuracy")
        self.accuracy_group.addButton(self.balanced_radio)
        row3.addWidget(self.balanced_radio)
        
        self.accurate_radio = QRadioButton("Accurate")
        self.accurate_radio.setToolTip(
            "Full preprocessing (noise removal, deskew) - slowest but most accurate"
        )
        self.accuracy_group.addButton(self.accurate_radio)
        row3.addWidget(self.accurate_radio)
        
        row3.addStretch()
        group_layout.addLayout(row3)
        
        # Fourth row: Force OCR checkbox
        row4 = QHBoxLayout()
        
        self.force_ocr_check = QCheckBox("Force OCR even if PDF already contains text")
        self.force_ocr_check.setToolTip(
            "By default, if the PDF already has extractable text, OCR is skipped.\n"
            "Check this to force OCR processing anyway."
        )
        row4.addWidget(self.force_ocr_check)
        
        row4.addStretch()
        group_layout.addLayout(row4)
        
        # Fifth row: Page separators checkbox (only for text output)
        row5 = QHBoxLayout()
        
        self.page_separators_check = QCheckBox("Include page separators (--- Page X ---) in text output")
        self.page_separators_check.setToolTip(
            "When checked, adds '--- Page X ---' markers between each page's text.\n"
            "Useful for identifying which page text came from."
        )
        self.page_separators_check.setChecked(False)  # Default to no separators
        row5.addWidget(self.page_separators_check)
        
        row5.addStretch()
        group_layout.addLayout(row5)
        
        return group
    
    def _check_tesseract(self):
        """Check if Tesseract is available and update UI accordingly."""
        if not self.ocr_service.is_tesseract_available():
            self.tesseract_warning.setVisible(True)
            self.convert_button.setEnabled(False)
    
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
        """Load a PDF file and analyze it."""
        self.selected_pdf = file_path
        self.file_label.setText(f"📄 {Path(file_path).name}")
        self.file_label.setStyleSheet(
            "color: #2c3e50; font-style: normal; font-weight: bold; "
            "border: none; background: transparent;"
        )
        
        # Get page count and check for existing text
        try:
            has_text, page_count = self.ocr_service.pdf_has_text(file_path)
            self.total_pages = page_count
            
            self.pdf_info_label.setText(f"📄 Total pages: {page_count}")
            self.pdf_info_label.setVisible(True)
            
            if has_text:
                self.text_detection_label.setText(
                    "ℹ️ This PDF already contains extractable text. "
                    "OCR will be skipped unless 'Force OCR' is checked."
                )
                self.text_detection_label.setStyleSheet("color: #27ae60; font-style: italic;")
            else:
                self.text_detection_label.setText(
                    "📝 This appears to be a scanned/image PDF. OCR will be performed."
                )
                self.text_detection_label.setStyleSheet("color: #e67e22; font-style: italic;")
            
            self.text_detection_label.setVisible(True)
            
            # Enable convert button if Tesseract is available
            if self.ocr_service.is_tesseract_available():
                self.convert_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not read PDF:\n{str(e)}")
            self.selected_pdf = None
    
    def _get_settings(self) -> OCRSettings:
        """Get current OCR settings from UI."""
        # Get language code
        lang_display = self.language_combo.currentText()
        lang_code = self.LANGUAGES.get(lang_display, "eng")
        
        # Get output format
        if self.txt_radio.isChecked():
            output_format = OutputFormat.TEXT
        else:
            output_format = OutputFormat.SEARCHABLE_PDF
        
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
        
        return OCRSettings(
            language=lang_code,
            output_format=output_format,
            dpi=dpi,
            accuracy_mode=accuracy_mode,
            force_ocr=self.force_ocr_check.isChecked(),
            include_page_separators=self.page_separators_check.isChecked()
        )
    
    def _start_ocr(self):
        """Start OCR processing."""
        if not self.selected_pdf:
            return
        
        settings = self._get_settings()
        
        # Determine file extension and filter
        if settings.output_format == OutputFormat.TEXT:
            ext = ".txt"
            filter_str = "Text Files (*.txt)"
        else:
            ext = ".pdf"
            filter_str = "PDF Files (*.pdf)"
        
        # Suggest output filename
        base_name = Path(self.selected_pdf).stem
        suggested_name = f"{base_name}_ocr{ext}"
        
        # Ask where to save
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Output As",
            suggested_name,
            filter_str
        )
        
        if not output_path:
            return
        
        # Update UI for processing
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Initializing...")
        self.status_label.setVisible(False)
        self.convert_button.setEnabled(False)
        
        # Create and start worker thread
        self.worker = OCRWorker(
            self.ocr_service,
            self.selected_pdf,
            output_path,
            settings
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress updates from worker."""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.progress_bar.setFormat(f"{message} ({percent}%)")
        else:
            self.progress_bar.setFormat(message)
    
    def _on_finished(self, result: OCRResult):
        """Handle OCR completion."""
        self.progress_bar.setValue(100)
        self.convert_button.setEnabled(True)
        
        if result.success:
            # Build success message
            if result.skipped_ocr:
                msg = f"✅ Text extracted successfully!\n"
                msg += f"Pages processed: {result.total_pages}"
            else:
                msg = f"✅ OCR completed successfully!\n"
                msg += f"Pages processed: {result.total_pages}\n"
                msg += f"Pages with text: {result.pages_with_text}"
            
            self.status_label.setText(msg)
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.status_label.setVisible(True)
            
            # Ask if user wants to open the file
            reply = QMessageBox.question(
                self,
                "Success",
                f"OCR completed successfully!\n\nOpen the output file now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import os
                os.startfile(result.output_path)
        else:
            self.status_label.setText(f"❌ {result.error_message}")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.status_label.setVisible(True)
            
            QMessageBox.critical(
                self,
                "Error",
                f"OCR failed:\n{result.error_message}"
            )
        
        # Cleanup worker
        self.worker = None
