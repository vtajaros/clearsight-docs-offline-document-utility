# ClearSight Docs

ClearSight Docs is a privacy-first, fully local desktop application for PDF document manipulation and Optical Character Recognition (OCR). It utilizes a hybrid architecture, combining a lightweight Electron/React frontend with a high-performance Python FastAPI backend to ensure documents never leave the host machine.

## Key Highlights

* **100% Local & Private**: No cloud uploads, no subscriptions, and no internet required. Your sensitive documents never leave your machine.
* **Cross-Platform**: Full native support for Linux, Windows, and macOS with platform-adaptive backend execution and custom desktop titlebar integration.
* **Blazing Fast Processing**: Leverages a dual-ingest strategy (Local Path Bypass) to circumvent standard HTTP upload limits, allowing instantaneous processing of multi-gigabyte files.
* **Modern Desktop Experience**: A beautifully crafted, responsive dark UI featuring custom frameless window management, smooth micro-animations, drag-and-drop workspaces, hardware-accelerated thumbnail grids, and robust memory management via LRU caching.
* **Real-time Feedback**: Complex operations like OCR feature live progress streaming via WebSockets, so you are always kept in the loop.

## Core Features

* **Merge PDFs**: Combine multiple PDF documents sequentially with drag-and-drop reordering and advanced sorting options (by name or date).
* **Split PDF**: Extract specific page ranges or explode a document into individual single-page files seamlessly.
* **Delete Pages**: Selectively remove pages using an interactive thumbnail grid and high-resolution previews.
* **Compress PDF**: Reduce file sizes with Low, Medium, and High optimization presets utilizing intelligent image recompression and stream optimizations.
* **OCR PDF**: Convert scanned documents or images into selectable Plain Text (`.txt`) or fully Searchable PDFs using the powerful Tesseract OCR engine.
* **PDF Bookmarks**: View, automatically generate (via heuristic font-size analysis), edit, and natively reorder the hierarchical table of contents for any PDF document.
* **Bionic Reading Converter**: Transform PDFs into bionic-reading formatted documents to enhance reading focus and speed.
* **Format Conversion**: 
  * **PDF to Images**: Extract pages into high-quality PNG or JPEG archives.
  * **Image to PDF**: Combine multiple image formats into a unified PDF document with customizable page sizes, margins, and orientations.

## Architecture & Tech Stack

The application is built on a decoupled client-server architecture running entirely on the local loopback interface:

* **Frontend**: Electron, React 19, Vite, Tailwind CSS v4.
* **Backend**: Python 3.10+, FastAPI, Uvicorn.
* **Core Processing Libraries**: `pypdf`, `pymupdf`, `pytesseract`, `pdf2image`, `img2pdf`, `reportlab`, `pikepdf`.

### Performance & Desktop Integration
* **Dual-Ingest Strategy**: Uses native Electron IPC (`dialog:openFiles`) to resolve absolute system paths and pass them to the FastAPI server, bypassing HTTP upload memory overhead.
* **Cross-Platform Backend Launcher**: Electron main process dynamically detects OS platform (`win32`, `linux`, `darwin`) to spawn Uvicorn from the appropriate virtual environment path (`.venv/bin/uvicorn` vs `.venv/Scripts/uvicorn.exe`).
* **Frameless CSD Window Management**: Renders a custom frameless titlebar with real-time IPC synchronization for window minimize, maximize, restore, and close states across all platforms, including Linux tiling compositors (e.g. KDE Plasma / KWin / Krohnkite).

## System Prerequisites

To run the backend services locally, the host machine must have the following system-level binaries installed:

1. **Poppler Utilities**: Required for PDF-to-Image rendering.
   * **Linux (Debian/Ubuntu)**: `sudo apt install poppler-utils`
   * **Linux (Fedora/RHEL)**: `sudo dnf install poppler-utils`
   * **Linux (Arch)**: `sudo pacman -S poppler`
   * **macOS**: `brew install poppler`
   * **Windows**: Set `POPPLER_PATH` to the Poppler `/bin` directory.
2. **Tesseract OCR**: Required for text extraction.
   * **Linux (Debian/Ubuntu)**: `sudo apt install tesseract-ocr`
   * **Linux (Fedora/RHEL)**: `sudo dnf install tesseract`
   * **Linux (Arch)**: `sudo pacman -S tesseract`
   * **macOS**: `brew install tesseract`
   * **Windows**: Set `TESSDATA_PREFIX` to your language training data path if not installed globally.

## Development Setup

### 1. Backend Environment Setup
```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux / macOS:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Frontend Environment Setup
```bash
cd frontend

# Install Node modules
npm install
```

### 3. Running the Application
```bash
cd frontend

# Launch Electron + Vite + FastAPI dev server
npm run dev
```
