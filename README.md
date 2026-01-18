# ClearSight Docs - Offline Document Utility

A modern, fully offline desktop application for PDF and image manipulation built with Python and PySide6.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-Qt-green)
![Windows](https://img.shields.io/badge/Windows-64--bit-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

### ✨ Current Features

- **Image to PDF Conversion**
  - Support for JPG and PNG formats
  - Multiple image selection with drag-and-drop
  - Visual reordering of images before conversion
  - Page size options (A4, Letter, Legal)
  - Orientation control (Portrait/Landscape)
  - Customizable margins (None, Small, Medium, Large)

- **PDF Merge**
  - Combine multiple PDF files into one
  - Drag-and-drop reordering
  - Maintains original quality

- **PDF Split**
  - Extract specific page ranges
  - Split into individual pages
  - Batch processing support

- **PDF to Images**
  - Convert PDF pages to image files
  - Support for PNG, JPG output formats
  - Configurable DPI/quality settings

- **PDF Compression**
  - Reduce PDF file size
  - Multiple compression levels

- **PDF Extract Pages**
  - Extract specific pages from a PDF
  - Create new PDF from selected pages

- **PDF Delete Pages**
  - Remove unwanted pages from PDF
  - Preview before deletion

- **PDF to Word**
  - Convert PDF documents to Word format
  - Preserves text content

- **OCR (Optical Character Recognition)**
  - Extract text from scanned PDFs and images
  - Powered by Tesseract OCR engine
  - Bundled with installer (no separate installation needed)

## Screenshots

<img width="1918" height="1012" alt="image" src="https://github.com/user-attachments/assets/0e1d091b-1f44-414e-ab48-3c45b136c4ec" />
<img width="1917" height="1015" alt="image" src="https://github.com/user-attachments/assets/d009d798-7788-442f-bf0a-24262a81d4ed" />
<img width="1919" height="1018" alt="image" src="https://github.com/user-attachments/assets/0d954fa4-c0c8-44e9-8f3c-791f9ecd2174" />
<img width="1918" height="1016" alt="image" src="https://github.com/user-attachments/assets/6898fb3e-8e22-4964-883e-9d0fbb0af2da" />


## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. **Clone or download this repository**

```bash
git clone https://github.com/vtajaros/ClearSight-Docs-Offline-Document-Tool-.git
cd ClearSight-Docs-Offline-Document-Tool-
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run the application**

```bash
python main.py
```

### Windows Installer

For end users, a Windows installer is available that bundles everything including Tesseract OCR and Poppler:

1. Download `ClearSightDocs_Setup.exe` from the [Releases](https://github.com/vtajaros/ClearSight-Docs-Offline-Document-Tool-/releases) page
2. Run the installer and follow the prompts
3. Launch ClearSight Docs from the Start Menu or Desktop shortcut

## Project Structure

```
ClearSight-Docs/
│
├── main.py                 # Application entry point
│
├── ui/                     # User interface components
│   ├── __init__.py
│   ├── main_window.py      # Main window with sidebar navigation
│   └── pages/              # Individual tool pages
│       ├── __init__.py
│       ├── image_to_pdf_page.py
│       ├── pdf_merge_page.py
│       ├── pdf_split_page.py
│       ├── pdf_to_images_page.py
│       ├── pdf_compress_page.py
│       ├── pdf_extract_pages_page.py
│       ├── pdf_delete_pages_page.py
│       ├── pdf_to_word_page.py
│       └── ocr_page.py
│
├── services/               # Business logic and file processing
│   ├── __init__.py
│   ├── image_to_pdf_service.py
│   ├── pdf_merge_service.py
│   ├── pdf_split_service.py
│   ├── pdf_to_images_service.py
│   ├── pdf_compress_service.py
│   ├── pdf_extract_pages_service.py
│   ├── pdf_delete_pages_service.py
│   ├── pdf_to_word_service.py
│   └── ocr_service.py
│
├── utils/                  # Helper functions and utilities
│   └── __init__.py
│
├── installer/              # Windows installer build scripts
│   ├── build_installer.bat
│   ├── ClearSightDocs.iss
│   └── INSTALLER_README.md
│
├── tesseract-portable/     # Bundled Tesseract OCR engine
├── poppler-portable/       # Bundled Poppler PDF utilities
│
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Technology Stack

- **Python 3.10+** - Core programming language
- **PySide6** - Qt-based GUI framework for cross-platform desktop UI
- **Pillow** - Image processing library
- **img2pdf** - Efficient image-to-PDF conversion
- **pypdf** - PDF manipulation and processing
- **pdf2image** - PDF to image conversion (uses Poppler)
- **pytesseract** - Python wrapper for Tesseract OCR
- **Tesseract OCR** - Optical character recognition engine
- **Poppler** - PDF rendering library

## Usage

### Image to PDF

1. Click on "Image to PDF" in the sidebar
2. Add images using the "Add Images" button or drag and drop
3. Reorder images by dragging them in the list
4. Configure page size, orientation, and margins
5. Click "Convert to PDF" and choose save location

### Merge PDFs

1. Click on "Merge PDFs" in the sidebar
2. Add PDF files using the "Add PDFs" button or drag and drop
3. Reorder PDFs by dragging them (merge order)
4. Click "Merge PDFs" and choose save location

### Split PDF

1. Click on "Split PDF" in the sidebar
2. Select a PDF file using the "Browse" button
3. Choose split mode:
   - **Extract page range**: Specify start and end pages
   - **Split into individual pages**: Creates separate PDF for each page
4. Click "Split PDF" and choose save location/directory

### PDF to Images

1. Click on "PDF to Images" in the sidebar
2. Select a PDF file to convert
3. Choose output format (PNG or JPG)
4. Set DPI/quality settings as needed
5. Click "Convert" and choose output folder

### Compress PDF

1. Click on "Compress PDF" in the sidebar
2. Select a PDF file to compress
3. Choose compression level (Low, Medium, High)
4. Click "Compress" and choose save location

### Extract Pages

1. Click on "Extract Pages" in the sidebar
2. Select a PDF file
3. Specify which pages to extract (e.g., 1-3, 5, 7-10)
4. Click "Extract" and choose save location

### Delete Pages

1. Click on "Delete Pages" in the sidebar
2. Select a PDF file
3. Preview the pages and select which ones to delete
4. Click "Delete Pages" and save the modified PDF

### PDF to Word

1. Click on "PDF to Word" in the sidebar
2. Select a PDF file to convert
3. Click "Convert to Word" and choose save location
4. The text content will be extracted into a Word document

### OCR (Text Recognition)

1. Click on "OCR" in the sidebar
2. Select a scanned PDF or image file
3. Choose the language (English by default)
4. Click "Extract Text" to perform OCR
5. Copy the extracted text or save it to a file

## Development

### Code Organization

The project follows clean architecture principles:

- **UI Layer** (`ui/`): Handles all user interface logic, event handling, and user interactions
- **Service Layer** (`services/`): Contains business logic for file processing operations
- **Utils Layer** (`utils/`): Provides helper functions and validators

### Key Design Patterns

- **Separation of Concerns**: UI code is separated from business logic
- **Single Responsibility**: Each class has a focused, well-defined purpose
- **Qt Signals/Slots**: Event-driven architecture using Qt's signal/slot mechanism

### Adding New Features

To add a new tool:

1. Create a new page in `ui/pages/`
2. Create corresponding service in `services/`
3. Add navigation button in `main_window.py`
4. Register the page in the stacked widget

## System Requirements

- **Windows 10/11 (64-bit)** - Required for the installer version
- No internet connection required
- Works completely offline
- Lightweight and fast

> **Note:** The Windows installer requires 64-bit Windows due to bundled Tesseract OCR and Poppler dependencies. Running from source may work on other platforms.

## Future Enhancements

Potential features for future versions:

- [x] PDF compression
- [x] PDF to images conversion
- [x] OCR (Optical Character Recognition)
- [x] PDF to Word conversion
- [x] PDF extract/delete pages
- [ ] PDF rotation
- [ ] Watermark addition
- [ ] PDF encryption/decryption
- [ ] Batch processing automation
- [ ] Dark mode theme
- [ ] Multi-language OCR support

## Contributing

This is a portfolio project, but suggestions and feedback are welcome!

## License

MIT License - Feel free to use this project for learning and portfolio purposes.

## Acknowledgments

- Built with [PySide6](https://www.qt.io/qt-for-python) (Qt for Python)
- Uses [img2pdf](https://gitlab.mister-muffin.de/josch/img2pdf) for image conversion
- PDF handling powered by [pypdf](https://github.com/py-pdf/pypdf)
- OCR powered by [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- PDF rendering by [Poppler](https://poppler.freedesktop.org/)

## Author

Created by Val Rique Tajaros as a portfolio project demonstrating:
- Desktop application development with Python
- Qt/PySide6 GUI programming
- Clean code architecture
- File processing and manipulation
- Modern UI/UX design principles

---

**Note**: This application runs entirely offline and does not require any internet connection or external services.
