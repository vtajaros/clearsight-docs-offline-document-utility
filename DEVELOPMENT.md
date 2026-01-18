# Development Guide - PDF Toolkit

## Architecture Overview

The application follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────┐
│         UI Layer (PySide6)          │  ← User interactions
├─────────────────────────────────────┤
│      Service Layer (Business)       │  ← File processing logic
├─────────────────────────────────────┤
│     Utils Layer (Helpers)           │  ← Shared utilities
└─────────────────────────────────────┘
```

## Code Organization

### 1. UI Layer (`ui/`)

**Main Window** (`main_window.py`)
- Creates the application window
- Manages sidebar navigation
- Handles page switching via QStackedWidget
- Uses Qt signals/slots for navigation

**Pages** (`ui/pages/`)
- Each tool has its own page class
- Inherits from `QWidget`
- Manages its own UI components
- Calls service layer for business logic
- Never directly manipulates files

### 2. Service Layer (`services/`)

**Purpose**: Contains all business logic for file operations

Each service class:
- Takes input parameters (file paths, settings)
- Performs file processing operations
- Returns success/failure status
- Handles exceptions internally
- Independent of UI (can be tested separately)

### 3. Utils Layer (`utils/`)

**Purpose**: Reusable helper functions

Examples:
- File validation
- Path manipulation
- Configuration management
- Constants

## Adding a New Tool

Follow these steps to add a new feature (e.g., "PDF Rotate"):

### Step 1: Create the Service

Create `services/pdf_rotate_service.py`:

```python
"""PDF rotation service."""
from pypdf import PdfWriter, PdfReader


class PdfRotateService:
    """Service for rotating PDF pages."""
    
    def rotate_pdf(self, pdf_path: str, output_path: str, 
                   rotation: int) -> bool:
        """
        Rotate all pages in a PDF.
        
        Args:
            pdf_path: Input PDF path
            output_path: Output PDF path
            rotation: Rotation angle (90, 180, 270)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            
            for page in reader.pages:
                page.rotate(rotation)
                writer.add_page(page)
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            return True
        except Exception as e:
            print(f"Error rotating PDF: {e}")
            return False
```

### Step 2: Create the UI Page

Create `ui/pages/pdf_rotate_page.py`:

```python
"""PDF Rotate page."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QFileDialog
)
from services.pdf_rotate_service import PdfRotateService


class PdfRotatePage(QWidget):
    """Page for rotating PDF files."""
    
    def __init__(self):
        super().__init__()
        self.selected_pdf = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Rotate PDF Pages")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        # File selection button
        self.select_btn = QPushButton("Select PDF")
        self.select_btn.clicked.connect(self._select_pdf)
        layout.addWidget(self.select_btn)
        
        # Rotation selector
        self.rotation_combo = QComboBox()
        self.rotation_combo.addItems(["90°", "180°", "270°"])
        layout.addWidget(self.rotation_combo)
        
        # Rotate button
        self.rotate_btn = QPushButton("Rotate PDF")
        self.rotate_btn.setEnabled(False)
        self.rotate_btn.clicked.connect(self._rotate_pdf)
        layout.addWidget(self.rotate_btn)
        
        layout.addStretch()
    
    def _select_pdf(self):
        """Select a PDF file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.selected_pdf = file_path
            self.rotate_btn.setEnabled(True)
    
    def _rotate_pdf(self):
        """Rotate the selected PDF."""
        if not self.selected_pdf:
            return
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Rotated PDF", "", "PDF Files (*.pdf)"
        )
        
        if not output_path:
            return
        
        # Get rotation value
        rotation_text = self.rotation_combo.currentText()
        rotation = int(rotation_text.replace("°", ""))
        
        # Call service
        service = PdfRotateService()
        success = service.rotate_pdf(
            self.selected_pdf,
            output_path,
            rotation
        )
        
        if success:
            # Show success message
            print("PDF rotated successfully!")
```

### Step 3: Register in Main Window

Edit `ui/main_window.py`:

```python
# Add import at top
from ui.pages.pdf_rotate_page import PdfRotatePage

# In _create_sidebar method, add button:
btn_pdf_rotate = QPushButton("🔄 Rotate PDF")
btn_pdf_rotate.setCheckable(True)
btn_pdf_rotate.clicked.connect(lambda: self._switch_page(3))
self.nav_buttons.append(btn_pdf_rotate)
sidebar_layout.addWidget(btn_pdf_rotate)

# In _add_pages method, add page:
self.pdf_rotate_page = PdfRotatePage()
self.stacked_widget.addWidget(self.pdf_rotate_page)
```

## UI Best Practices

### Layout Management

Use appropriate layouts:
- `QVBoxLayout`: Vertical stacking
- `QHBoxLayout`: Horizontal arrangement
- `QGridLayout`: Grid positioning
- `QFormLayout`: Form-style labels and inputs

### Styling

Apply styles using `setStyleSheet()`:

```python
button.setStyleSheet("""
    QPushButton {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 10px;
    }
    QPushButton:hover {
        background-color: #2980b9;
    }
""")
```

### Signals and Slots

Connect events using Qt's signal/slot mechanism:

```python
# Signal connection
self.button.clicked.connect(self._handle_click)

# Custom signals
class MyWidget(QWidget):
    file_selected = Signal(str)  # Define signal
    
    def _select_file(self):
        # Emit signal
        self.file_selected.emit(file_path)
```

## Service Best Practices

### Error Handling

Always handle exceptions:

```python
def process_file(self, file_path: str) -> bool:
    try:
        # Processing logic
        return True
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
```

### Return Values

- Use `bool` for success/failure
- Use `Optional[T]` for nullable returns
- Use `dict` for complex return data

### Type Hints

Always use type hints:

```python
def merge_pdfs(
    self,
    pdf_paths: List[str],
    output_path: str
) -> bool:
    pass
```

## Testing Strategy

### Manual Testing Checklist

For each feature:
- ✅ Test with valid inputs
- ✅ Test with invalid inputs
- ✅ Test with missing files
- ✅ Test with corrupted files
- ✅ Test cancel operations
- ✅ Test drag-and-drop
- ✅ Test keyboard shortcuts

### Unit Testing (Future)

Create `tests/` directory:

```python
import unittest
from services.pdf_merge_service import PdfMergeService


class TestPdfMergeService(unittest.TestCase):
    def setUp(self):
        self.service = PdfMergeService()
    
    def test_merge_two_pdfs(self):
        result = self.service.merge_pdfs(
            ['test1.pdf', 'test2.pdf'],
            'output.pdf'
        )
        self.assertTrue(result)
```

## Debugging Tips

### Print Debugging

Add debug prints in services:

```python
def convert_images_to_pdf(self, images, output):
    print(f"Converting {len(images)} images")
    print(f"Output path: {output}")
    # ... processing
    print("Conversion complete")
```

### Qt Debug Output

Enable Qt debug messages:

```python
import sys
from PySide6.QtCore import qInstallMessageHandler

def qt_message_handler(mode, context, message):
    print(f"Qt: {message}")

qInstallMessageHandler(qt_message_handler)
```

### Exception Handling

Catch and display errors:

```python
try:
    result = self._process_file()
except Exception as e:
    import traceback
    print(traceback.format_exc())
    QMessageBox.critical(self, "Error", str(e))
```

## Performance Optimization

### For Large Files

- Use progress callbacks for long operations
- Process in chunks when possible
- Use QThread for background processing

### Memory Management

- Close file handles explicitly
- Use context managers (`with` statements)
- Clear large data structures when done

## Code Style

### Follow PEP 8

- Use 4 spaces for indentation
- Maximum line length: 88-100 characters
- Use snake_case for functions and variables
- Use PascalCase for class names

### Naming Conventions

- Private methods: `_method_name()`
- Public methods: `method_name()`
- Constants: `CONSTANT_NAME`
- Protected: `_protected_variable`

### Documentation

Use docstrings for all public methods:

```python
def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> bool:
    """
    Merge multiple PDF files into one.
    
    Args:
        pdf_paths: List of input PDF file paths
        output_path: Path for the merged output file
    
    Returns:
        True if successful, False otherwise
    
    Raises:
        ValueError: If pdf_paths is empty
        FileNotFoundError: If input file doesn't exist
    """
```

## Deployment

### Creating an Executable (Future)

Use PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name="PDF Toolkit" main.py
```

### Distribution

Package includes:
- Executable
- README
- LICENSE
- Sample files (optional)

## Resources

### PySide6 Documentation
- https://doc.qt.io/qtforpython/

### Python Libraries
- pypdf: https://pypdf.readthedocs.io/
- Pillow: https://pillow.readthedocs.io/
- img2pdf: https://gitlab.mister-muffin.de/josch/img2pdf

### Qt Widgets Reference
- https://doc.qt.io/qt-6/widget-classes.html

---

**Happy coding!** 🚀
