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

*Coming soon*

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. **Clone or download this repository**

2. **Install dependencies**

```bash
cd pdf-toolkit
pip install -r requirements.txt
```

3. **Run the application**

```bash
python main.py
```

## Project Structure

```
pdf-toolkit/
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
│       └── pdf_split_page.py
│
├── services/               # Business logic and file processing
│   ├── __init__.py
│   ├── image_to_pdf_service.py
│   ├── pdf_merge_service.py
│   └── pdf_split_service.py
│
├── utils/                  # Helper functions and utilities
│   └── __init__.py
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

## Author

Created by Val Rique Tajaros as a portfolio project demonstrating:
- Desktop application development with Python
- Qt/PySide6 GUI programming
- Clean code architecture
- File processing and manipulation
- Modern UI/UX design principles

---

**Note**: This application runs entirely offline and does not require any internet connection or external services.
