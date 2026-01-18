# Troubleshooting Guide - PDF Toolkit

## Common Issues and Solutions

### Image to PDF Conversion Issues

#### Issue: "Failed to create PDF" but file exists and won't open

**Symptoms:**
- Progress bar reaches 100%
- Error message says "Failed to create PDF"
- A PDF file is created on disk
- PDF file cannot be opened with PDF viewers

**Possible Causes:**
1. **One or more images are corrupted or invalid**
   - The conversion partially completes before hitting a bad image
   - Corrupted file is left on disk

2. **Unsupported image format or color mode**
   - Some images may have unsupported color modes (CMYK, LAB, etc.)
   - Transparency in certain PNG files may cause issues

3. **Memory issues with large images**
   - Very large or high-resolution images can cause memory problems
   - Conversion may fail partway through

**Solutions:**

✅ **Solution 1: Validate your images first**
```
The latest version now validates all images before conversion.
If validation fails, you'll see which images are problematic.
```

✅ **Solution 2: Check image formats**
- Ensure all images are:
  - JPG/JPEG or PNG format
  - RGB color mode (not CMYK)
  - Not corrupted
  - Readable in Windows Photo Viewer or other image software

✅ **Solution 3: Convert images if needed**
- Open problematic images in an image editor (Paint, GIMP, Photoshop)
- Save as a new JPG or PNG file
- Use the newly saved image

✅ **Solution 4: Process in batches**
- Instead of 30 images at once, try:
  - Convert 10 images at a time
  - Merge the resulting PDFs using the "Merge PDFs" tool

✅ **Solution 5: Reduce image size**
- If images are very large (10MB+), resize them first:
  - Use an image editor to reduce resolution
  - Target 1-2MB per image for optimal results

✅ **Solution 6: Check console output**
- Run the app from terminal to see detailed error messages:
  ```bash
  python main.py
  ```
- Look for specific error messages in the console

#### Issue: Images appear in wrong order

**Solution:**
- Drag and drop images in the list to reorder them
- The order in the list is the order they'll appear in the PDF

#### Issue: Images are cut off or don't fit on page

**Solutions:**
- Try "None" margins to use the full page
- Switch to "Landscape" orientation for wide images
- Use a larger page size (Legal instead of A4)

#### Issue: "Permission denied" error

**Solutions:**
- Close any PDF viewers that might have the output file open
- Try saving to a different location (Desktop, Documents)
- Run the application as Administrator (right-click → Run as Administrator)

### PDF Merge Issues

#### Issue: Merged PDF is corrupted

**Solutions:**
- Ensure all source PDFs can be opened individually
- Try merging fewer PDFs at a time
- Check source PDFs aren't password-protected

#### Issue: Pages appear in wrong order

**Solution:**
- Drag PDFs in the list to reorder before merging

### PDF Split Issues

#### Issue: "Cannot read PDF" error

**Solutions:**
- Ensure PDF is not password-protected
- Try opening PDF in another viewer first to verify it's valid
- Check file is not corrupted

#### Issue: Page count shows 0

**Solution:**
- The PDF may be corrupted or password-protected
- Try a different PDF file

## Getting More Information

### Enable Detailed Logging

Run the application from the terminal to see detailed error messages:

**PowerShell:**
```powershell
cd X:\Programming\Python\pdf-toolkit
python main.py
```

**Command Prompt:**
```cmd
cd X:\Programming\Python\pdf-toolkit
python main.py
```

Look for error messages in the console output.

### Check Python Console Output

The application prints detailed information to the console:
- Number of images being converted
- Page dimensions and settings
- File sizes
- Error stack traces

### Common Error Messages

**"cannot identify image file"**
- Image file is corrupted or in unsupported format
- Solution: Open and re-save the image in an image editor

**"Image mode not supported"**
- Image uses CMYK or other non-RGB color mode
- Solution: Convert image to RGB mode

**"Out of memory"**
- Images are too large or too many images at once
- Solution: Process fewer images or reduce image sizes

**"Permission denied"**
- File is locked by another program
- Solution: Close other programs using the file

## Testing Your Images

### Quick Test with Individual Images

To find which image is causing problems:

1. Create a new conversion with just the first image
2. If it works, add the second image
3. Continue until you find the problematic image
4. Replace or fix the problematic image

### Image Checklist

✅ File format: JPG or PNG
✅ File size: < 10MB per image
✅ Opens correctly in Windows Photo Viewer
✅ Not password-protected or encrypted
✅ RGB color mode (not CMYK, Grayscale, LAB)
✅ Not corrupted

## Still Having Issues?

### Check the Project Files

Ensure all these files exist and are not corrupted:
```
pdf-toolkit/
├── main.py
├── ui/
│   └── pages/
│       └── image_to_pdf_page.py
└── services/
    └── image_to_pdf_service.py
```

### Reinstall Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Check Python and Package Versions

```bash
python --version
pip show PySide6 Pillow img2pdf pypdf
```

Required versions:
- Python: 3.10+
- PySide6: 6.6.0+
- Pillow: 10.0.0+
- img2pdf: 0.5.0+
- pypdf: 3.17.0+

## Recent Fixes (v1.1)

✅ **Fixed:** Progress bar showing 100% on failed conversions
✅ **Added:** Image validation before conversion
✅ **Added:** Automatic cleanup of corrupted output files
✅ **Added:** Detailed error messages with context
✅ **Added:** Better exception handling and logging
✅ **Improved:** Error messages now show specific issues

## Tips for Best Results

### Image Conversion
- Use JPG for photographs
- Use PNG for graphics with text
- Keep images under 5MB each
- Convert HEIC/WebP to JPG first
- Process in batches of 10-15 images

### PDF Operations
- Close PDF files before merging/splitting
- Use descriptive output filenames
- Save to easily accessible locations
- Check disk space before large operations

## Contact/Support

This is a portfolio project. For issues:
1. Check this troubleshooting guide
2. Review the console output for errors
3. Check the DEVELOPMENT.md for debugging tips
4. Review the code in the project files

---

**Last Updated:** January 18, 2026
**Version:** 1.1 (with improved error handling)
