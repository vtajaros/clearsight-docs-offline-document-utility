# Testing Guide - PDF Toolkit

## Manual Testing Checklist

Use this checklist to verify all features work correctly.

## General Application Tests

### Application Launch
- [ ] Application starts without errors
- [ ] Main window appears with correct title
- [ ] Sidebar is visible with 3 tools
- [ ] Default page (Image to PDF) is selected

### Navigation
- [ ] Click "Image to PDF" - page switches correctly
- [ ] Click "Merge PDFs" - page switches correctly
- [ ] Click "Split PDF" - page switches correctly
- [ ] Active button is highlighted in sidebar

## Image to PDF Tests

### File Selection
- [ ] Click "Add Images" - file dialog opens
- [ ] Select single JPG file - appears in list
- [ ] Select single PNG file - appears in list
- [ ] Select multiple images - all appear in list
- [ ] Duplicate selection - no duplicates added
- [ ] Cancel file dialog - no errors

### Drag and Drop
- [ ] Drag JPG from explorer - file added
- [ ] Drag PNG from explorer - file added
- [ ] Drag multiple images - all added
- [ ] Drag non-image file - ignored
- [ ] Drag PDF file - ignored

### List Management
- [ ] Images appear with 📷 icon and name
- [ ] Select image - highlight appears
- [ ] Select multiple (Ctrl+click) - multiple highlighted
- [ ] "Remove Selected" button enables when selected
- [ ] "Clear All" button enables when list has items
- [ ] Remove selected - items removed
- [ ] Clear all - all items removed
- [ ] Drop hint visible when list empty

### Reordering
- [ ] Drag image up in list - order changes
- [ ] Drag image down in list - order changes
- [ ] Drag to top - becomes first
- [ ] Drag to bottom - becomes last

### Settings
- [ ] Change page size to A4 - no errors
- [ ] Change page size to Letter - no errors
- [ ] Change page size to Legal - no errors
- [ ] Change orientation to Portrait - no errors
- [ ] Change orientation to Landscape - no errors
- [ ] Change margins to None - no errors
- [ ] Change margins to Small - no errors
- [ ] Change margins to Medium - no errors
- [ ] Change margins to Large - no errors

### Conversion
- [ ] Convert button disabled when no images
- [ ] Convert button enabled when images added
- [ ] Click convert - save dialog appears
- [ ] Enter filename - conversion starts
- [ ] Progress bar appears and updates
- [ ] Success message appears
- [ ] File explorer opens on success (if Yes clicked)
- [ ] Output PDF file exists and opens correctly
- [ ] Cancel save dialog - no conversion

### Error Handling
- [ ] Add corrupted image - handled gracefully
- [ ] Try to save to read-only location - error shown
- [ ] Cancel during conversion - handled properly

## PDF Merge Tests

### File Selection
- [ ] Click "Add PDFs" - file dialog opens
- [ ] Select single PDF - appears in list
- [ ] Select multiple PDFs - all appear
- [ ] Duplicate selection - no duplicates
- [ ] Cancel file dialog - no errors

### Drag and Drop
- [ ] Drag PDF from explorer - file added
- [ ] Drag multiple PDFs - all added
- [ ] Drag non-PDF file - ignored
- [ ] Drag image file - ignored

### List Management
- [ ] PDFs appear with 📄 icon and name
- [ ] Selection works correctly
- [ ] Remove selected works
- [ ] Clear all works
- [ ] Drop hint visible when empty

### Reordering
- [ ] Drag PDF up - order changes
- [ ] Drag PDF down - order changes
- [ ] Final merge order matches list order

### Merging
- [ ] Merge button disabled with 0 files
- [ ] Merge button disabled with 1 file
- [ ] Merge button enabled with 2+ files
- [ ] Click merge - save dialog appears
- [ ] Merge completes successfully
- [ ] Progress bar shows
- [ ] Success message appears
- [ ] Output PDF contains all pages in order

### Error Handling
- [ ] Add corrupted PDF - error handled
- [ ] Merge with encrypted PDF - handled
- [ ] Save to invalid location - error shown

## PDF Split Tests

### File Selection
- [ ] Click "Browse" - file dialog opens
- [ ] Select PDF - filename appears
- [ ] Page count displayed correctly
- [ ] Split button becomes enabled

### Page Range Mode
- [ ] "Extract page range" radio selected by default
- [ ] Start page spinbox enabled
- [ ] End page spinbox enabled
- [ ] Start page minimum is 1
- [ ] End page maximum matches PDF page count
- [ ] Invalid range (start > end) - error shown

### Individual Pages Mode
- [ ] Select "Split into individual pages" radio
- [ ] Page spinboxes become disabled
- [ ] Help text visible

### Splitting - Page Range
- [ ] Select range (e.g., 1-3) - works correctly
- [ ] Click split - save dialog appears
- [ ] Output PDF contains only selected pages
- [ ] Original PDF unchanged

### Splitting - Individual Pages
- [ ] Select individual pages mode
- [ ] Click split - directory dialog appears
- [ ] Split completes successfully
- [ ] Correct number of files created
- [ ] Files named correctly (page_001.pdf, etc.)
- [ ] Each file contains single page

### Error Handling
- [ ] Invalid page range - error shown
- [ ] Corrupted PDF - error handled
- [ ] Save to invalid location - error shown

## Cross-Feature Tests

### Multiple Operations
- [ ] Convert images, then merge PDFs - both work
- [ ] Split PDF, then convert images - both work
- [ ] Perform operations in random order - all work

### File System
- [ ] Create PDF with spaces in name - works
- [ ] Create PDF with special characters - works
- [ ] Save to different drive - works
- [ ] Save to network location (if available) - works

### Performance
- [ ] Convert 10+ images - completes in reasonable time
- [ ] Merge 10+ PDFs - completes in reasonable time
- [ ] Split large PDF (50+ pages) - works correctly

## UI/UX Tests

### Responsiveness
- [ ] Resize window smaller - UI adapts
- [ ] Resize window larger - UI adapts
- [ ] Minimize and restore - works correctly
- [ ] Maximize window - works correctly

### Visual Feedback
- [ ] Hover over buttons - visual change
- [ ] Disabled buttons appear grayed out
- [ ] Progress bars animate correctly
- [ ] Status messages visible and clear

### User Flow
- [ ] First-time user can figure out how to use tools
- [ ] Error messages are helpful and actionable
- [ ] Success messages are encouraging
- [ ] File explorer integration is convenient

## Edge Cases

### Empty Operations
- [ ] Convert with 0 images - button disabled
- [ ] Merge with 0 PDFs - button disabled
- [ ] Merge with 1 PDF - button disabled
- [ ] Split without selecting file - button disabled

### Large Files
- [ ] Convert very large image (10MB+) - works
- [ ] Merge large PDF (100+ pages) - works
- [ ] Split large PDF - works

### File Names
- [ ] Very long filename - handled
- [ ] Unicode characters in filename - handled
- [ ] Special characters in path - handled

## Platform-Specific Tests (Windows)

### Windows Integration
- [ ] Double-click run.bat - app launches
- [ ] File explorer opens correctly
- [ ] File dialogs use Windows native style
- [ ] Icons display correctly

### Drag and Drop
- [ ] Drag from Windows Explorer - works
- [ ] Drag from desktop - works
- [ ] Drag from Quick Access - works

## Regression Tests

After making changes, verify:
- [ ] All previous features still work
- [ ] No new errors in console
- [ ] Performance hasn't degraded
- [ ] UI still looks correct

---

## Bug Report Template

If you find a bug, document it as follows:

```
BUG: [Short description]

Steps to Reproduce:
1. [First step]
2. [Second step]
3. [etc.]

Expected Behavior:
[What should happen]

Actual Behavior:
[What actually happened]

Error Message (if any):
[Copy error message]

Environment:
- OS: Windows 10/11
- Python: 3.x
- PySide6: 6.x
```

---

## Test Results Summary

Date: _______________
Tester: _______________

Total Tests: ______
Passed: ______
Failed: ______
Skipped: ______

Pass Rate: ______%

Critical Issues: ______
Minor Issues: ______

Notes:
_______________________________________
_______________________________________
_______________________________________

---

**Happy Testing!** 🧪
