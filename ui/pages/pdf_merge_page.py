"""
PDF Merge page.
Allows users to select multiple PDF files and merge them into one.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLabel, QGroupBox, QFileDialog, QProgressBar, QMessageBox,
    QListWidgetItem, QAbstractItemView, QListView
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QImage, QFont

from services.pdf_merge_service import PdfMergeService

# Try to import fitz (PyMuPDF) for PDF thumbnails
try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


class PdfMergePage(QWidget):
    """Page for merging multiple PDF files."""
    
    THUMBNAIL_SIZE = 120  # Size of PDF preview thumbnails
    
    def __init__(self):
        super().__init__()
        self.pdf_files = []  # List to store selected PDF file paths
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Page title
        title_label = QLabel("Merge PDF Documents")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        description_label = QLabel("Combine multiple PDF files into a single document")
        description_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        layout.addWidget(description_label)
        
        # File selection area
        file_group = self._create_file_selection_group()
        layout.addWidget(file_group)
        
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
        
        # Merge button
        self.merge_button = QPushButton("Merge PDFs")
        self.merge_button.setEnabled(False)
        self.merge_button.setMinimumHeight(45)
        self.merge_button.setStyleSheet("""
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
        self.merge_button.clicked.connect(self._merge_pdfs)
        layout.addWidget(self.merge_button)
        
    def _create_file_selection_group(self):
        """Create the file selection group with drag-drop list."""
        group = QGroupBox("PDF Files")
        group_layout = QVBoxLayout(group)
        
        # Button row
        button_layout = QHBoxLayout()
        
        self.add_files_button = QPushButton("➕ Add PDFs")
        self.add_files_button.clicked.connect(self._add_pdfs)
        button_layout.addWidget(self.add_files_button)
        
        self.remove_files_button = QPushButton("🗑️ Remove Selected")
        self.remove_files_button.clicked.connect(self._remove_selected_pdfs)
        self.remove_files_button.setEnabled(False)
        button_layout.addWidget(self.remove_files_button)
        
        self.clear_files_button = QPushButton("Clear All")
        self.clear_files_button.clicked.connect(self._clear_all_pdfs)
        self.clear_files_button.setEnabled(False)
        button_layout.addWidget(self.clear_files_button)
        
        # Move buttons for reordering
        self.move_up_button = QPushButton("⬆️ Move Up")
        self.move_up_button.clicked.connect(self._move_up)
        self.move_up_button.setEnabled(False)
        button_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("⬇️ Move Down")
        self.move_down_button.clicked.connect(self._move_down)
        self.move_down_button.setEnabled(False)
        button_layout.addWidget(self.move_down_button)
        
        button_layout.addStretch()
        
        # PDF count label
        self.count_label = QLabel("0 PDFs")
        self.count_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        button_layout.addWidget(self.count_label)
        
        group_layout.addLayout(button_layout)
        
        # PDF list with thumbnails
        self.pdf_list = QListWidget()
        self.pdf_list.setDragEnabled(False)  # Disable internal dragging
        self.pdf_list.setAcceptDrops(True)  # Accept external file drops
        self.pdf_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.pdf_list.setMinimumHeight(350)
        self.pdf_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.pdf_list.setIconSize(QSize(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE))
        self.pdf_list.setGridSize(QSize(self.THUMBNAIL_SIZE + 30, self.THUMBNAIL_SIZE + 50))  # Fixed grid cells
        self.pdf_list.setMovement(QListView.Movement.Static)  # Items cannot be moved by user
        self.pdf_list.setSpacing(10)
        self.pdf_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.pdf_list.setWrapping(True)
        self.pdf_list.setWordWrap(True)
        self.pdf_list.setUniformItemSizes(True)  # All items same size for consistent grid
        self.pdf_list.setStyleSheet("""
            QListWidget {
                border: 2px dashed #bdc3c7;
                border-radius: 5px;
                background-color: #ecf0f1;
                padding: 10px;
            }
            QListWidget::item {
                padding: 5px;
                border-radius: 5px;
                margin: 5px;
                color: #2c3e50;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #d5dbdb;
            }
        """)
        self.pdf_list.itemSelectionChanged.connect(self._update_button_states)
        
        # Set up external file drop handling
        self.pdf_list.dragEnterEvent = self._drag_enter_event
        self.pdf_list.dragMoveEvent = self._drag_move_event
        self.pdf_list.dropEvent = self._drop_event
        
        # Drop hint label
        self.drop_hint_label = QLabel("Drag and drop PDF files here or click 'Add PDFs'\nFiles will be merged in the order shown\n\n📄 Use Move Up/Down to reorder")
        self.drop_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_hint_label.setStyleSheet("color: #95a5a6; font-style: italic; font-size: 13px;")
        
        group_layout.addWidget(self.drop_hint_label)
        group_layout.addWidget(self.pdf_list)
        
        return group
    
    def _drag_enter_event(self, event):
        """Handle drag enter event for external file drops."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def _drag_move_event(self, event):
        """Handle drag move event for external file drops."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def _drop_event(self, event):
        """Handle drop event for external file drops."""
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    files.append(file_path)
            
            if files:
                self._add_pdf_files(files)
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def _add_pdfs(self):
        """Open file dialog to add PDFs."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF Files",
            "",
            "PDF Files (*.pdf)"
        )
        
        if files:
            self._add_pdf_files(files)
    
    def _create_pdf_thumbnail(self, pdf_path: str) -> QIcon:
        """Create a thumbnail from the first page of a PDF."""
        if not HAS_FITZ:
            # Return a default PDF icon if PyMuPDF is not available
            return self._create_placeholder_icon()
        
        try:
            doc = fitz.open(pdf_path)
            if doc.page_count > 0:
                page = doc[0]
                # Render at a reasonable resolution for thumbnail
                mat = fitz.Matrix(0.5, 0.5)  # Scale down
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to QImage then QPixmap
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
                
                # Scale to thumbnail size
                scaled = pixmap.scaled(
                    self.THUMBNAIL_SIZE,
                    self.THUMBNAIL_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                doc.close()
                return QIcon(scaled)
            doc.close()
        except Exception as e:
            print(f"Error creating PDF thumbnail for {pdf_path}: {e}")
        
        return self._create_placeholder_icon()
    
    def _create_placeholder_icon(self) -> QIcon:
        """Create a placeholder icon for PDFs without thumbnails."""
        # Create a simple colored rectangle as placeholder
        pixmap = QPixmap(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE)
        pixmap.fill(Qt.GlobalColor.white)
        return QIcon(pixmap)
    
    def _add_pdf_files(self, files: list):
        """Add PDF files to the list with thumbnails."""
        for file_path in files:
            if file_path not in self.pdf_files:
                self.pdf_files.append(file_path)
                
                # Create thumbnail from first page
                thumbnail = self._create_pdf_thumbnail(file_path)
                filename = Path(file_path).name
                
                # Truncate long filenames
                display_name = filename if len(filename) <= 18 else filename[:15] + "..."
                
                item = QListWidgetItem(thumbnail, display_name)
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                item.setToolTip(filename)  # Show full name on hover
                item.setSizeHint(QSize(self.THUMBNAIL_SIZE + 20, self.THUMBNAIL_SIZE + 40))
                # Make label bold for better visibility
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                self.pdf_list.addItem(item)
        
        self._update_button_states()
        self._update_drop_hint_visibility()
    
    def _remove_selected_pdfs(self):
        """Remove selected PDFs from the list."""
        for item in self.pdf_list.selectedItems():
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.pdf_files:
                self.pdf_files.remove(file_path)
            self.pdf_list.takeItem(self.pdf_list.row(item))
        
        self._update_button_states()
        self._update_drop_hint_visibility()
    
    def _clear_all_pdfs(self):
        """Clear all PDFs from the list."""
        self.pdf_files.clear()
        self.pdf_list.clear()
        self._update_button_states()
        self._update_drop_hint_visibility()
    
    def _handle_reorder(self):
        """Handle reordering of PDFs via drag and drop."""
        # Update the pdf_files list based on the new order
        self.pdf_files.clear()
        for i in range(self.pdf_list.count()):
            item = self.pdf_list.item(i)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            self.pdf_files.append(file_path)
    
    def _move_up(self):
        """Move selected item up in the list."""
        current_row = self.pdf_list.currentRow()
        if current_row > 0:
            item = self.pdf_list.takeItem(current_row)
            self.pdf_list.insertItem(current_row - 1, item)
            self.pdf_list.setCurrentRow(current_row - 1)
            self._handle_reorder()
    
    def _move_down(self):
        """Move selected item down in the list."""
        current_row = self.pdf_list.currentRow()
        if current_row < self.pdf_list.count() - 1:
            item = self.pdf_list.takeItem(current_row)
            self.pdf_list.insertItem(current_row + 1, item)
            self.pdf_list.setCurrentRow(current_row + 1)
            self._handle_reorder()
    
    def _update_button_states(self):
        """Update the enabled state of buttons based on current state."""
        has_items = self.pdf_list.count() > 1  # Need at least 2 PDFs to merge
        has_selection = len(self.pdf_list.selectedItems()) > 0
        single_selection = len(self.pdf_list.selectedItems()) == 1
        current_row = self.pdf_list.currentRow()
        
        self.remove_files_button.setEnabled(has_selection)
        self.clear_files_button.setEnabled(self.pdf_list.count() > 0)
        self.merge_button.setEnabled(has_items)
        
        # Move buttons only enabled with single selection
        self.move_up_button.setEnabled(single_selection and current_row > 0)
        self.move_down_button.setEnabled(single_selection and current_row < self.pdf_list.count() - 1)
        
        # Update count label
        count = self.pdf_list.count()
        self.count_label.setText(f"{count} PDF{'s' if count != 1 else ''}")
    
    def _update_drop_hint_visibility(self):
        """Show/hide the drop hint label based on list contents."""
        self.drop_hint_label.setVisible(self.pdf_list.count() == 0)
    
    def _merge_pdfs(self):
        """Merge the PDFs."""
        if len(self.pdf_files) < 2:
            return
        
        # Ask user where to save the merged PDF
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Merged PDF As",
            "merged.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not output_file:
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(False)
        self.merge_button.setEnabled(False)
        
        try:
            # Use the service to merge
            service = PdfMergeService()
            success = service.merge_pdfs(self.pdf_files, output_file)
            
            self.progress_bar.setValue(100)
            
            if success:
                self.status_label.setText(f"✅ PDFs merged successfully: {Path(output_file).name}")
                self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.status_label.setVisible(True)
                
                # Ask if user wants to open the merged PDF
                reply = QMessageBox.question(
                    self,
                    "Success",
                    f"PDFs merged successfully!\n\nOpen the PDF now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    import os
                    os.startfile(output_file)
            else:
                self.status_label.setText("❌ Failed to merge PDFs")
                self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                self.status_label.setVisible(True)
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.status_label.setVisible(True)
            QMessageBox.critical(self, "Error", f"Failed to merge PDFs:\n{str(e)}")
        
        finally:
            self.merge_button.setEnabled(len(self.pdf_files) > 1)
