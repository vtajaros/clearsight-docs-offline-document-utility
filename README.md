# ClearSight Docs

ClearSight Docs is a privacy-first, fully local desktop application for PDF document manipulation and Optical Character Recognition (OCR). It utilizes a hybrid architecture, combining a lightweight Electron/React frontend with a high-performance Python FastAPI backend to ensure documents never leave the host machine.

## Key Highlights

* **100% Local & Private**: No cloud uploads, no subscriptions, and no internet required. Your sensitive documents never leave your machine.
* **Blazing Fast Processing**: Leverages a dual-ingest strategy (Local Path Bypass) to circumvent standard HTTP upload limits, allowing instantaneous processing of multi-gigabyte files.
* **Modern Desktop Experience**: A beautifully crafted, responsive dark UI featuring smooth micro-animations, drag-and-drop workspaces, hardware-accelerated thumbnail grids, and robust memory management via LRU caching.
* **Real-time Feedback**: Complex operations like OCR feature live progress streaming via WebSockets, so you are always kept in the loop.

## Core Features

* **Merge PDFs**: Combine multiple PDF documents sequentially with drag-and-drop reordering and advanced sorting options (by name or date).
* **Split PDF**: Extract specific page ranges or explode a document into individual single-page files seamlessly.
* **Delete Pages**: Selectively remove pages using an interactive thumbnail grid and high-resolution previews.
* **Compress PDF**: Reduce file sizes with Low, Medium, and High optimization presets utilizing intelligent image recompression and stream optimizations.
* **OCR PDF**: Convert scanned documents or images into selectable Plain Text (`.txt`) or fully Searchable PDFs using the powerful Tesseract OCR engine.
* **Format Conversion**: 
  * **PDF to Images**: Extract pages into high-quality PNG or JPEG archives.
  * **Image to PDF**: Combine multiple image formats into a unified PDF document with customizable page sizes, margins, and orientations.

## Architecture & Tech Stack

The application is built on a decoupled client-server architecture running entirely on the local loopback interface:

* **Frontend**: Electron, React 19, Vite, Tailwind CSS v4.
* **Backend**: Python 3, FastAPI, Uvicorn.
* **Core Processing Libraries**: `pypdf`, `pymupdf`, `pytesseract`, `pdf2image`, `img2pdf`, `reportlab`.

### Performance Optimization: Dual-Ingest Strategy
To prevent the V8 memory heap limits and serialization bottlenecks associated with HTTP multipart form uploads for large PDFs, the application implements a **Local Path Bypass**. The Electron frontend uses native IPC (`dialog:openFiles`) to resolve absolute system paths and passes these string paths to the backend. The FastAPI server reads the files directly from the disk. Standard `UploadFile` endpoints are preserved purely as a fallback.

## System Prerequisites

To run the backend services locally, the host machine must have the following system-level C++ binaries installed and accessible on the system PATH, or configured via environment variables:

1. **Poppler**: Required for PDF-to-Image rendering.
   * *Environment Variable*: Set `POPPLER_PATH` to the `/bin` directory.
2. **Tesseract OCR**: Required for text extraction.
   * *Environment Variable*: Set `TESSDATA_PREFIX` to your language training data path if not installed globally.

## Development Setup

### 1. Backend Environment
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

### 2. Frontend Environment
```bash
cd frontend
npm install
```

### 3. Running the Application
```bash
# In the root project directory, run your primary dev command
npm run dev
```
