"""
Image to PDF conversion page with thumbnail previews.
Allows users to select multiple images, preview them, reorder, and convert to PDF.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLabel, QComboBox, QGroupBox, QFileDialog, QProgressBar,
    QMessageBox, QListWidgetItem, QAbstractItemView, QListView
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont

from services.image_to_pdf_service import ImageToPdfService


class ImageToPdfPage(QWidget):
    """Page for converting images to PDF with thumbnail previews."""
    
    THUMBNAIL_SIZE = 120  # Size of thumbnail previews
    
    def __init__(self):
        super().__init__()
        self.image_files = []  # List to store selected image file paths
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Page title
        title_label = QLabel("Image to PDF Converter")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        description_label = QLabel("Convert JPG and PNG images to a single PDF document. Drag thumbnails to reorder.")
        description_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        layout.addWidget(description_label)
        
        # File selection area with preview
        file_group = self._create_file_selection_group()
        layout.addWidget(file_group)
        
        # Settings area
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
        self.convert_button = QPushButton("Convert to PDF")
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
        self.convert_button.clicked.connect(self._convert_to_pdf)
        layout.addWidget(self.convert_button)
        
    def _create_file_selection_group(self):
        """Create the file selection group with thumbnail preview list."""
        group = QGroupBox("Images")
        group_layout = QVBoxLayout(group)
        
        # Button row
        button_layout = QHBoxLayout()
        
        self.add_files_button = QPushButton("➕ Add Images")
        self.add_files_button.clicked.connect(self._add_images)
        button_layout.addWidget(self.add_files_button)
        
        self.remove_files_button = QPushButton("🗑️ Remove Selected")
        self.remove_files_button.clicked.connect(self._remove_selected_images)
        self.remove_files_button.setEnabled(False)
        button_layout.addWidget(self.remove_files_button)
        
        self.clear_files_button = QPushButton("Clear All")
        self.clear_files_button.clicked.connect(self._clear_all_images)
        self.clear_files_button.setEnabled(False)
        button_layout.addWidget(self.clear_files_button)
        
        # Move buttons
        self.move_up_button = QPushButton("⬆️ Move Up")
        self.move_up_button.clicked.connect(self._move_up)
        self.move_up_button.setEnabled(False)
        button_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("⬇️ Move Down")
        self.move_down_button.clicked.connect(self._move_down)
        self.move_down_button.setEnabled(False)
        button_layout.addWidget(self.move_down_button)
        
        button_layout.addStretch()
        
        # Image count label
        self.count_label = QLabel("0 images")
        self.count_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        button_layout.addWidget(self.count_label)
        
        group_layout.addLayout(button_layout)
        
        # Image list with thumbnail icons - grid view style
        self.image_list = QListWidget()
        self.image_list.setDragEnabled(False)  # Disable internal dragging
        self.image_list.setAcceptDrops(True)  # Accept external file drops
        self.image_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.image_list.setMinimumHeight(300)
        self.image_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.image_list.setIconSize(QSize(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE))
        self.image_list.setGridSize(QSize(self.THUMBNAIL_SIZE + 30, self.THUMBNAIL_SIZE + 50))  # Fixed grid cells
        self.image_list.setMovement(QListView.Movement.Static)  # Items cannot be moved by user
        self.image_list.setSpacing(10)
        self.image_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.image_list.setWrapping(True)
        self.image_list.setWordWrap(True)
        self.image_list.setUniformItemSizes(True)  # All items same size for consistent grid
        self.image_list.setStyleSheet("""
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
        self.image_list.itemSelectionChanged.connect(self._update_button_states)
        
        # Set up external file drop handling
        self.image_list.dragEnterEvent = self._drag_enter_event
        self.image_list.dragMoveEvent = self._drag_move_event
        self.image_list.dropEvent = self._drop_event
        
        # Drop hint label (shown when list is empty)
        self.drop_hint_label = QLabel("Drag and drop images here or click 'Add Images'\nSupported formats: JPG, PNG\n\n📷 Use Move Up/Down to reorder")
        self.drop_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_hint_label.setStyleSheet("color: #95a5a6; font-style: italic; font-size: 13px;")
        
        group_layout.addWidget(self.drop_hint_label)
        group_layout.addWidget(self.image_list)
        
        return group
    
    def _create_settings_group(self):
        """Create the PDF settings group."""
        group = QGroupBox("PDF Settings")
        group_layout = QHBoxLayout(group)
        
        # Page size
        page_size_label = QLabel("Page Size:")
        group_layout.addWidget(page_size_label)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4", "Letter", "Legal"])
        self.page_size_combo.setCurrentText("A4")
        group_layout.addWidget(self.page_size_combo)
        
        group_layout.addSpacing(20)
        
        # Orientation
        orientation_label = QLabel("Orientation:")
        group_layout.addWidget(orientation_label)
        
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["Portrait", "Landscape"])
        group_layout.addWidget(self.orientation_combo)
        
        group_layout.addSpacing(20)
        
        # Margins
        margin_label = QLabel("Margins:")
        group_layout.addWidget(margin_label)
        
        self.margin_combo = QComboBox()
        self.margin_combo.addItems(["None", "Small", "Medium", "Large"])
        self.margin_combo.setCurrentText("Small")
        group_layout.addWidget(self.margin_combo)
        
        group_layout.addStretch()
        
        return group
    
    def _create_thumbnail(self, image_path: str) -> QIcon:
        """Create a thumbnail icon from an image file."""
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                # Return a placeholder if image can't be loaded
                return QIcon()
            
            # Scale to thumbnail size while maintaining aspect ratio
            scaled = pixmap.scaled(
                self.THUMBNAIL_SIZE, 
                self.THUMBNAIL_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            return QIcon(scaled)
        except Exception as e:
            print(f"Error creating thumbnail for {image_path}: {e}")
            return QIcon()
    
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
                if self._is_valid_image(file_path):
                    files.append(file_path)
            
            if files:
                self._add_image_files(files)
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def _is_valid_image(self, file_path: str) -> bool:
        """Check if the file is a valid image format."""
        valid_extensions = {'.jpg', '.jpeg', '.png'}
        return Path(file_path).suffix.lower() in valid_extensions
    
    def _add_images(self):
        """Open file dialog to add images."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Image Files (*.jpg *.jpeg *.png)"
        )
        
        if files:
            self._add_image_files(files)
    
    def _add_image_files(self, files: list):
        """Add image files to the list with thumbnails."""
        for file_path in files:
            if file_path not in self.image_files:
                self.image_files.append(file_path)
                
                # Create list item with thumbnail
                thumbnail = self._create_thumbnail(file_path)
                filename = Path(file_path).name
                
                # Truncate long filenames
                display_name = filename if len(filename) <= 15 else filename[:12] + "..."
                
                item = QListWidgetItem(thumbnail, display_name)
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                item.setToolTip(filename)  # Show full name on hover
                item.setSizeHint(QSize(self.THUMBNAIL_SIZE + 20, self.THUMBNAIL_SIZE + 40))
                # Make label bold for better visibility
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                self.image_list.addItem(item)
        
        self._update_button_states()
        self._update_drop_hint_visibility()
    
    def _remove_selected_images(self):
        """Remove selected images from the list."""
        for item in self.image_list.selectedItems():
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.image_files:
                self.image_files.remove(file_path)
            self.image_list.takeItem(self.image_list.row(item))
        
        self._update_button_states()
        self._update_drop_hint_visibility()
    
    def _clear_all_images(self):
        """Clear all images from the list."""
        self.image_files.clear()
        self.image_list.clear()
        self._update_button_states()
        self._update_drop_hint_visibility()
    
    def _move_up(self):
        """Move selected item up in the list."""
        current_row = self.image_list.currentRow()
        if current_row > 0:
            item = self.image_list.takeItem(current_row)
            self.image_list.insertItem(current_row - 1, item)
            self.image_list.setCurrentRow(current_row - 1)
            self._handle_reorder()
    
    def _move_down(self):
        """Move selected item down in the list."""
        current_row = self.image_list.currentRow()
        if current_row < self.image_list.count() - 1:
            item = self.image_list.takeItem(current_row)
            self.image_list.insertItem(current_row + 1, item)
            self.image_list.setCurrentRow(current_row + 1)
            self._handle_reorder()
    
    def _handle_reorder(self):
        """Handle reordering of images via drag and drop."""
        # Update the image_files list based on the new order
        self.image_files.clear()
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            self.image_files.append(file_path)
    
    def _update_button_states(self):
        """Update the enabled state of buttons based on current state."""
        has_items = self.image_list.count() > 0
        has_selection = len(self.image_list.selectedItems()) > 0
        single_selection = len(self.image_list.selectedItems()) == 1
        current_row = self.image_list.currentRow()
        
        self.remove_files_button.setEnabled(has_selection)
        self.clear_files_button.setEnabled(has_items)
        self.convert_button.setEnabled(has_items)
        
        # Move buttons only enabled with single selection
        self.move_up_button.setEnabled(single_selection and current_row > 0)
        self.move_down_button.setEnabled(single_selection and current_row < self.image_list.count() - 1)
        
        # Update count label
        count = self.image_list.count()
        self.count_label.setText(f"{count} image{'s' if count != 1 else ''}")
    
    def _update_drop_hint_visibility(self):
        """Show/hide the drop hint label based on list contents."""
        self.drop_hint_label.setVisible(self.image_list.count() == 0)
    
    def _convert_to_pdf(self):
        """Convert the images to PDF."""
        if not self.image_files:
            return
        
        # Ask user where to save the PDF
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF As",
            "output.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not output_file:
            return
        
        # Get settings
        page_size = self.page_size_combo.currentText()
        orientation = self.orientation_combo.currentText()
        margin = self.margin_combo.currentText()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(False)
        self.convert_button.setEnabled(False)
        
        # Validate images before conversion
        service = ImageToPdfService()
        invalid_images = []
        for img_path in self.image_files:
            if not service.validate_image(img_path):
                invalid_images.append(Path(img_path).name)
        
        if invalid_images:
            self.progress_bar.setVisible(False)
            self.convert_button.setEnabled(True)
            QMessageBox.warning(
                self,
                "Invalid Images",
                f"The following images are invalid or corrupted:\n\n" +
                "\n".join(invalid_images[:10]) +
                ("\n..." if len(invalid_images) > 10 else "") +
                f"\n\nPlease remove these images and try again."
            )
            return
        
        try:
            # Use the service to convert
            service.convert_images_to_pdf(
                self.image_files,
                output_file,
                page_size=page_size,
                orientation=orientation,
                margin=margin
            )
            
            # Only set to 100% on success
            self.progress_bar.setValue(100)
            
            self.status_label.setText(f"✅ PDF created successfully: {Path(output_file).name}")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.status_label.setVisible(True)
            
            # Ask if user wants to open the created PDF
            reply = QMessageBox.question(
                self,
                "Success",
                f"PDF created successfully!\n\nOpen the PDF now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import os
                # Open the PDF with the default application
                os.startfile(output_file)
                
        except Exception as e:
            # Don't set progress to 100% on error
            self.progress_bar.setValue(0)
            
            # Show detailed error message
            error_msg = str(e)
            
            # Provide helpful context for common errors
            if "cannot identify image file" in error_msg.lower():
                error_msg = "One or more image files are corrupted or in an unsupported format.\n\nPlease check your image files and try again."
            elif "permission" in error_msg.lower() or "denied" in error_msg.lower():
                error_msg = "Permission denied. The output location may be read-only or in use by another program.\n\nTry saving to a different location."
            elif "memory" in error_msg.lower():
                error_msg = "Out of memory. Try converting fewer images at once or using smaller image files."
            
            self.status_label.setText(f"❌ Error: Conversion failed")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.status_label.setVisible(True)
            
            # Show detailed error dialog
            QMessageBox.critical(
                self, 
                "Conversion Failed", 
                f"Failed to create PDF:\n\n{error_msg}\n\nPlease check the console for detailed error information."
            )
        
        finally:
            self.convert_button.setEnabled(True)
