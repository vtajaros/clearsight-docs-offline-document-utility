"""
PDF Extract Pages page with visual thumbnail selection.
Allows users to visually select and extract pages from a PDF document.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFileDialog, QProgressBar, QMessageBox,
    QFrame, QListWidget, QListWidgetItem, QAbstractItemView,
    QListView, QSplitter, QScrollArea, QCheckBox, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QImage, QFont

from services.pdf_extract_pages_service import PdfExtractPagesService

# Try to import fitz (PyMuPDF) for PDF thumbnails
try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


class PdfExtractPagesPage(QWidget):
    """Page for extracting pages from PDF files with visual selection."""
    
    THUMBNAIL_SIZE = 150  # Size of page thumbnails
    PREVIEW_WIDTH = 550   # Width of preview panel
    
    def __init__(self):
        super().__init__()
        self.selected_pdf = None
        self.total_pages = 0
        self.page_thumbnails = []  # Store page pixmaps for preview
        self.current_preview_page = -1  # Currently previewed page
        self.zoom_level = 1.0  # Zoom level for preview
        self._is_loading = False  # Flag to track if PDF is being loaded
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Page title
        title_label = QLabel("Extract PDF Pages")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        description_label = QLabel("Select pages to extract by clicking on them. Selected pages (highlighted in purple) will be extracted to a new PDF.")
        description_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        layout.addWidget(description_label)
        
        # File selection group
        file_group = self._create_file_selection_group()
        layout.addWidget(file_group)
        
        # Main content area with splitter (pages list + preview)
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setVisible(False)
        
        # Pages selection group
        pages_group = self._create_pages_selection_group()
        self.content_splitter.addWidget(pages_group)
        
        # Preview panel
        preview_group = self._create_preview_group()
        self.content_splitter.addWidget(preview_group)
        
        # Set splitter sizes
        self.content_splitter.setSizes([600, 400])
        layout.addWidget(self.content_splitter)
        
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
        
        # Extract button
        self.extract_button = QPushButton("Extract Selected Pages")
        self.extract_button.setEnabled(False)
        self.extract_button.setMinimumHeight(45)
        self.extract_button.setStyleSheet("""
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
        self.extract_button.clicked.connect(self._extract_pages)
        layout.addWidget(self.extract_button)
        
    def _create_file_selection_group(self):
        """Create the file selection group with drop zone."""
        group = QGroupBox("Select PDF File")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(8)
        
        # Drop zone frame - compact
        self.drop_zone = QFrame()
        self.drop_zone.setAcceptDrops(True)
        self.drop_zone.setFixedHeight(50)
        self.drop_zone.setStyleSheet("""
            QFrame {
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
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
        
        self.file_label = QLabel("Drag and drop a PDF file here or click Browse...")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #2c3e50; font-style: italic; font-weight: bold; border: none; background: transparent;")
        drop_layout.addWidget(self.file_label)
        
        # Set up drop events
        self.drop_zone.dragEnterEvent = self._drag_enter_event
        self.drop_zone.dragMoveEvent = self._drag_move_event
        self.drop_zone.dropEvent = self._drop_event
        self.drop_zone.mousePressEvent = self._drop_zone_clicked
        self.drop_zone.setCursor(Qt.CursorShape.PointingHandCursor)
        
        group_layout.addWidget(self.drop_zone)
        
        # Browse button row
        button_row = QHBoxLayout()
        button_row.addStretch()
        
        select_button = QPushButton("Browse...")
        select_button.clicked.connect(self._select_pdf)
        button_row.addWidget(select_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_pdf)
        self.clear_button.setVisible(False)
        button_row.addWidget(self.clear_button)
        
        group_layout.addLayout(button_row)
        
        return group
    
    def _create_pages_selection_group(self):
        """Create the pages selection group with thumbnails."""
        group = QGroupBox("Pages (Click to select for extraction)")
        group_layout = QVBoxLayout(group)
        
        # Button row
        button_layout = QHBoxLayout()
        
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self._select_all_pages)
        button_layout.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self._deselect_all_pages)
        button_layout.addWidget(self.deselect_all_button)
        
        self.invert_selection_button = QPushButton("Invert Selection")
        self.invert_selection_button.clicked.connect(self._invert_selection)
        button_layout.addWidget(self.invert_selection_button)
        
        button_layout.addStretch()
        
        # Selection count label
        self.selection_label = QLabel("0 pages selected for extraction")
        self.selection_label.setStyleSheet("color: #9b59b6; font-weight: bold;")
        button_layout.addWidget(self.selection_label)
        
        group_layout.addLayout(button_layout)
        
        # Pages list with thumbnails
        self.pages_list = QListWidget()
        self.pages_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.pages_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.pages_list.setIconSize(QSize(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE))
        self.pages_list.setGridSize(QSize(self.THUMBNAIL_SIZE + 30, self.THUMBNAIL_SIZE + 50))
        self.pages_list.setMovement(QListView.Movement.Static)
        self.pages_list.setSpacing(10)
        self.pages_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.pages_list.setWrapping(True)
        self.pages_list.setWordWrap(True)
        self.pages_list.setUniformItemSizes(True)
        self.pages_list.setMinimumHeight(300)
        self.pages_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #f8f9fa;
                padding: 10px;
            }
            QListWidget::item {
                padding: 5px;
                border-radius: 5px;
                margin: 5px;
                color: #2c3e50;
                border: 2px solid transparent;
            }
            QListWidget::item:selected {
                background-color: #e8daef;
                border: 2px solid #9b59b6;
                color: #7d3c98;
            }
            QListWidget::item:hover {
                background-color: #ebf5fb;
                border: 2px solid #3498db;
            }
        """)
        self.pages_list.itemSelectionChanged.connect(self._update_selection_status)
        self.pages_list.itemClicked.connect(self._on_page_clicked)
        
        group_layout.addWidget(self.pages_list)
        
        # Options row
        options_layout = QHBoxLayout()
        self.preserve_order_checkbox = QCheckBox("Extract pages in selection order (instead of page number order)")
        self.preserve_order_checkbox.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self.preserve_order_checkbox.setToolTip(
            "When checked, pages will appear in the output PDF in the order you selected them.\n"
            "Otherwise, pages are sorted by their original page number."
        )
        options_layout.addWidget(self.preserve_order_checkbox)
        options_layout.addStretch()
        group_layout.addLayout(options_layout)
        
        return group
    
    def _create_preview_group(self):
        """Create the preview panel."""
        group = QGroupBox("Page Preview")
        group.setFixedWidth(self.PREVIEW_WIDTH)
        group_layout = QVBoxLayout(group)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        
        self.zoom_out_button = QPushButton("−")
        self.zoom_out_button.setFixedSize(32, 32)
        self.zoom_out_button.setToolTip("Zoom Out")
        self.zoom_out_button.setStyleSheet("""
            QPushButton {
                font-size: 18px; font-weight: bold;
                background-color: #3498db; color: white;
                border: none; border-radius: 5px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.zoom_out_button.clicked.connect(self._zoom_out)
        zoom_layout.addWidget(self.zoom_out_button)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setMinimumWidth(55)
        self.zoom_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 12px;")
        zoom_layout.addWidget(self.zoom_label)
        
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setFixedSize(32, 32)
        self.zoom_in_button.setToolTip("Zoom In")
        self.zoom_in_button.setStyleSheet("""
            QPushButton {
                font-size: 18px; font-weight: bold;
                background-color: #3498db; color: white;
                border: none; border-radius: 5px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.zoom_in_button.clicked.connect(self._zoom_in)
        zoom_layout.addWidget(self.zoom_in_button)
        
        self.zoom_reset_button = QPushButton("Fit")
        self.zoom_reset_button.setFixedSize(45, 32)
        self.zoom_reset_button.setToolTip("Reset to Fit")
        self.zoom_reset_button.setStyleSheet("""
            QPushButton {
                font-size: 12px; font-weight: bold;
                background-color: #27ae60; color: white;
                border: none; border-radius: 5px;
            }
            QPushButton:hover { background-color: #219a52; }
        """)
        self.zoom_reset_button.clicked.connect(self._zoom_reset)
        zoom_layout.addWidget(self.zoom_reset_button)
        
        zoom_layout.addStretch()
        group_layout.addLayout(zoom_layout)
        
        # Preview scroll area with both scrollbars
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(False)  # Don't resize widget, allow scrolling
        self.preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.preview_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.preview_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #ffffff;
            }
        """)
        
        # Preview label
        self.preview_label = QLabel("Select a page to preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: #95a5a6; font-style: italic;")
        self.preview_label.setMinimumSize(500, 650)
        
        self.preview_scroll.setWidget(self.preview_label)
        group_layout.addWidget(self.preview_scroll, 1)  # Give it stretch factor
        
        # Page info label
        self.page_info_label = QLabel("")
        self.page_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_info_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        group_layout.addWidget(self.page_info_label)
        
        return group
    
    def _drag_enter_event(self, event):
        """Handle drag enter event for file drops."""
        if self._is_loading:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def _drag_move_event(self, event):
        """Handle drag move event for file drops."""
        if self._is_loading:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def _drop_event(self, event):
        """Handle drop event for file drops."""
        if self._is_loading:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    self._load_pdf(file_path)
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def _drop_zone_clicked(self, event):
        """Handle click on drop zone to open file browser."""
        # Only trigger browse if no file is loaded and not currently loading
        if self.selected_pdf is None and not self._is_loading:
            self._select_pdf()
    
    def _select_pdf(self):
        """Open file dialog to select a PDF."""
        if self._is_loading:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF File",
            "",
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            self._load_pdf(file_path)
    
    def _clear_pdf(self):
        """Clear the loaded PDF."""
        if self._is_loading:
            return
        self.selected_pdf = None
        self.total_pages = 0
        self.page_thumbnails.clear()
        self.pages_list.clear()
        self.content_splitter.setVisible(False)
        self.clear_button.setVisible(False)
        self.extract_button.setEnabled(False)
        self.file_label.setText("Drag and drop a PDF file here or click Browse...")
        self.file_label.setStyleSheet("color: #2c3e50; font-style: italic; font-weight: bold; border: none; background: transparent;")
        self.preview_label.setText("Select a page to preview")
        self.preview_label.setPixmap(QPixmap())
        self.page_info_label.setText("")
        # Restore click-to-browse cursor
        self.drop_zone.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_label.setVisible(False)
    
    def _load_pdf(self, file_path: str):
        """Load a PDF file and display page thumbnails."""
        if self._is_loading:
            return
        
        self._is_loading = True
        self.selected_pdf = file_path
        self.file_label.setText(f"⏳ Loading {Path(file_path).name}...")
        self.file_label.setStyleSheet("color: #2c3e50; font-style: normal; font-weight: bold; border: none; background: transparent;")
        self.clear_button.setVisible(False)  # Disable clear while loading
        # Change cursor since file is being loaded
        self.drop_zone.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Clear previous data
        self.pages_list.clear()
        self.page_thumbnails.clear()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            if not HAS_FITZ:
                QMessageBox.warning(self, "Warning", "PyMuPDF (fitz) is required for page thumbnails.\nInstall it with: pip install pymupdf")
                self.progress_bar.setVisible(False)
                return
            
            doc = fitz.open(file_path)
            self.total_pages = doc.page_count
            self.progress_bar.setMaximum(self.total_pages)
            
            for page_num in range(self.total_pages):
                page = doc[page_num]
                
                # Create thumbnail
                mat = fitz.Matrix(0.3, 0.3)  # Scale for thumbnail
                pix = page.get_pixmap(matrix=mat)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                thumbnail_pixmap = QPixmap.fromImage(img)
                
                # Scale to consistent thumbnail size
                scaled_thumb = thumbnail_pixmap.scaled(
                    self.THUMBNAIL_SIZE,
                    self.THUMBNAIL_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Create larger preview
                mat_preview = fitz.Matrix(1.0, 1.0)  # Larger for preview
                pix_preview = page.get_pixmap(matrix=mat_preview)
                img_preview = QImage(pix_preview.samples, pix_preview.width, pix_preview.height, pix_preview.stride, QImage.Format.Format_RGB888)
                preview_pixmap = QPixmap.fromImage(img_preview)
                self.page_thumbnails.append(preview_pixmap)
                
                # Add to list
                item = QListWidgetItem(QIcon(scaled_thumb), f"Page {page_num + 1}")
                item.setData(Qt.ItemDataRole.UserRole, page_num)
                item.setSizeHint(QSize(self.THUMBNAIL_SIZE + 20, self.THUMBNAIL_SIZE + 40))
                # Make label bold for better visibility
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                self.pages_list.addItem(item)
                
                self.progress_bar.setValue(page_num + 1)
                
                # Process events to keep UI responsive
                QApplication.processEvents()
                
            doc.close()
            
            self.file_label.setText(f"📄 {Path(file_path).name}")
            self.clear_button.setVisible(True)
            self.content_splitter.setVisible(True)
            self._update_selection_status()
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not read PDF:\n{str(e)}")
            self.selected_pdf = None
            self.progress_bar.setVisible(False)
        finally:
            self._is_loading = False
    
    def _on_page_clicked(self, item):
        """Handle page click for preview."""
        page_num = item.data(Qt.ItemDataRole.UserRole)
        self.current_preview_page = page_num
        self._update_preview()
        
        is_selected = item.isSelected()
        status = "📑 SELECTED FOR EXTRACTION" if is_selected else "Not selected"
        self.page_info_label.setText(f"Page {page_num + 1} of {self.total_pages}\n{status}")
        self.page_info_label.setStyleSheet(f"color: {'#9b59b6' if is_selected else '#7f8c8d'}; font-weight: bold;")
    
    def _update_preview(self):
        """Update the preview with current zoom level."""
        if self.current_preview_page < 0 or self.current_preview_page >= len(self.page_thumbnails):
            return
        
        preview = self.page_thumbnails[self.current_preview_page]
        # Apply zoom to base size
        base_width, base_height = 520, 720
        scaled_width = int(base_width * self.zoom_level)
        scaled_height = int(base_height * self.zoom_level)
        
        scaled = preview.scaled(
            scaled_width, scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled)
        self.preview_label.setFixedSize(scaled.size())
        self.preview_label.setStyleSheet("")
    
    def _zoom_in(self):
        """Zoom in the preview."""
        if self.zoom_level < 3.0:
            self.zoom_level += 0.25
            self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
            self._update_preview()
    
    def _zoom_out(self):
        """Zoom out the preview."""
        if self.zoom_level > 0.25:
            self.zoom_level -= 0.25
            self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
            self._update_preview()
    
    def _zoom_reset(self):
        """Reset zoom to fit."""
        self.zoom_level = 1.0
        self.zoom_label.setText("100%")
        self._update_preview()
    
    def _update_selection_status(self):
        """Update the selection status label and button state."""
        selected_count = len(self.pages_list.selectedItems())
        
        if selected_count == 0:
            self.selection_label.setText("No pages selected for extraction")
            self.selection_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        else:
            self.selection_label.setText(f"{selected_count} page(s) selected for extraction")
            self.selection_label.setStyleSheet("color: #9b59b6; font-weight: bold;")
        
        # Enable extract button only if at least one page is selected
        self.extract_button.setEnabled(selected_count > 0)
    
    def _select_all_pages(self):
        """Select all pages."""
        self.pages_list.selectAll()
    
    def _deselect_all_pages(self):
        """Deselect all pages."""
        self.pages_list.clearSelection()
    
    def _invert_selection(self):
        """Invert the current selection."""
        for i in range(self.pages_list.count()):
            item = self.pages_list.item(i)
            item.setSelected(not item.isSelected())
    
    def _extract_pages(self):
        """Extract the selected pages from the PDF."""
        if not self.selected_pdf:
            return
        
        # Get selected page numbers (1-indexed)
        pages_to_extract = []
        for item in self.pages_list.selectedItems():
            page_num = item.data(Qt.ItemDataRole.UserRole) + 1  # Convert to 1-indexed
            pages_to_extract.append(page_num)
        
        if not pages_to_extract:
            return
        
        # Sort unless preserve order is checked
        preserve_order = self.preserve_order_checkbox.isChecked()
        if not preserve_order:
            pages_to_extract = sorted(pages_to_extract)
        
        # Ask user where to save the output PDF
        default_name = Path(self.selected_pdf).stem + "_extracted.pdf"
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Extracted PDF As",
            default_name,
            "PDF Files (*.pdf)"
        )
        
        if not output_file:
            return
        
        self._perform_extract(pages_to_extract, output_file, preserve_order)
    
    def _perform_extract(self, pages_to_extract: list, output_file: str, preserve_order: bool):
        """Perform the page extraction."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.status_label.setVisible(False)
        self.extract_button.setEnabled(False)
        
        try:
            service = PdfExtractPagesService()
            
            if preserve_order:
                service.extract_pages_preserve_order(
                    self.selected_pdf,
                    output_file,
                    pages_to_extract
                )
            else:
                service.extract_pages(
                    self.selected_pdf,
                    output_file,
                    pages_to_extract
                )
            
            self.progress_bar.setValue(100)
            
            self.status_label.setText(f"✅ Extracted {len(pages_to_extract)} page(s) to new PDF.")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.status_label.setVisible(True)
            
            # Ask if user wants to open the extracted PDF
            reply = QMessageBox.question(
                self,
                "Success",
                f"Pages extracted successfully!\n\nOpen the new PDF now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import os
                os.startfile(output_file)
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.status_label.setVisible(True)
            QMessageBox.critical(self, "Error", f"Failed to extract pages:\n{str(e)}")
        
        finally:
            self.extract_button.setEnabled(True)
            self.progress_bar.setVisible(False)
