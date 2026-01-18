# Quick Start Guide - PDF Toolkit

## First-Time Setup

### 1. Install Python
Make sure you have Python 3.10 or higher installed.

Check your Python version:
```bash
python --version
```

### 2. Install Dependencies

Navigate to the project folder and install required packages:

```bash
cd X:\Programming\Python\pdf-toolkit
pip install -r requirements.txt
```

This will install:
- PySide6 (Qt GUI framework)
- Pillow (image processing)
- img2pdf (image to PDF conversion)
- pypdf (PDF manipulation)

### 3. Run the Application

```bash
python main.py
```

## Using the Application

### Image to PDF
1. Click "Image to PDF" in the left sidebar
2. Drag and drop images OR click "Add Images" button
3. Drag images in the list to reorder them
4. Choose settings (Page Size: A4/Letter, Orientation, Margins)
5. Click "Convert to PDF"
6. Choose where to save your PDF

### Merge PDFs
1. Click "Merge PDFs" in the left sidebar
2. Add PDF files (drag-drop or button)
3. Reorder files if needed (drag in list)
4. Click "Merge PDFs"
5. Save the combined PDF

### Split PDF
1. Click "Split PDF" in the left sidebar
2. Browse and select a PDF file
3. Choose split option:
   - Extract specific page range (e.g., pages 5-10)
   - Split into individual pages
4. Click "Split PDF"
5. Choose output location

## Tips

- **Drag and Drop**: All file lists support drag-and-drop for easy reordering
- **Multiple Selection**: Hold Ctrl to select multiple items to remove
- **File Preview**: File names show with icons for easy identification
- **Progress Feedback**: Watch the progress bar and status messages
- **Quality**: All operations maintain original file quality

## Troubleshooting

### Application won't start
- Ensure Python 3.10+ is installed
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Import errors
```bash
pip install --upgrade -r requirements.txt
```

### UI looks blurry on high-DPI displays
The app includes high-DPI scaling support, but you can adjust Windows display settings if needed.

## Project Structure Quick Reference

```
pdf-toolkit/
├── main.py              # Start here - run this file
├── ui/                  # All UI code
│   ├── main_window.py   # Main app window
│   └── pages/           # Individual tool pages
├── services/            # File processing logic
├── requirements.txt     # Dependencies
└── README.md           # Full documentation
```

## Development Mode

If you want to modify the code:

1. **Edit UI**: Modify files in `ui/` folder
2. **Edit Logic**: Modify files in `services/` folder
3. **Test**: Run `python main.py` to see changes immediately
4. **No Compilation**: Python runs directly, no build step needed

## Support

For issues or questions, refer to the main README.md file.

---

**Enjoy using PDF Toolkit!** 📄✨
