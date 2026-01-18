"""
Main window for PDF Toolkit application.
Provides the main UI with sidebar navigation and stacked pages.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from ui.pages.image_to_pdf_page import ImageToPdfPage
from ui.pages.pdf_merge_page import PdfMergePage
from ui.pages.pdf_split_page import PdfSplitPage
from ui.pages.pdf_to_images_page import PdfToImagesPage
from ui.pages.ocr_page import OCRPage
from ui.pages.pdf_to_word_page import PDFToWordPage
from ui.pages.pdf_delete_pages_page import PdfDeletePagesPage
from ui.pages.pdf_extract_pages_page import PdfExtractPagesPage
from ui.pages.pdf_compress_page import PdfCompressPage


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""
    
    def __init__(self, icon_path=None):
        super().__init__()
        self.setWindowTitle("ClearSight Docs - Offline Document Utility")
        self.setMinimumSize(1000, 700)
        
        # Set window icon for title bar
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        # Initialize UI
        self._init_ui()
        
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
        version_label = QLabel("v1.5.0")
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
