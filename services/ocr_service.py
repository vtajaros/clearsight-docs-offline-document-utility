"""
OCR Service for PDF text extraction and searchable PDF creation.
Handles conversion of scanned/image-based PDFs to text or searchable PDFs.

Uses Tesseract OCR via pytesseract for text recognition.
Uses pdf2image (with Poppler) for PDF to image conversion.
"""
import os
import re
import sys
import tempfile
import shutil
import unicodedata
from pathlib import Path
from typing import Optional, Callable, Tuple, List
from dataclasses import dataclass
from enum import Enum

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _configure_poppler_path():
    """
    Configure Poppler path for pdf2image.
    
    When running as a PyInstaller bundle, Poppler is placed in a 'poppler/bin'
    subfolder relative to the executable.
    """
    poppler_path = None
    
    # When running as a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        bundled_path = os.path.join(exe_dir, 'poppler', 'bin')
        if os.path.isdir(bundled_path):
            poppler_path = bundled_path
    else:
        # Development mode - check relative to project
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dev_paths = [
            os.path.join(project_dir, 'poppler-portable', 'bin'),
            os.path.join(project_dir, 'poppler', 'bin'),
        ]
        for path in dev_paths:
            if os.path.isdir(path):
                poppler_path = path
                break
    
    # Add to PATH if found
    if poppler_path and poppler_path not in os.environ.get('PATH', ''):
        os.environ['PATH'] = poppler_path + os.pathsep + os.environ.get('PATH', '')
    
    return poppler_path


# Configure Poppler on module import
_POPPLER_PATH = _configure_poppler_path()


class OutputFormat(Enum):
    """Output format options for OCR."""
    TEXT = "txt"
    SEARCHABLE_PDF = "pdf"


class AccuracyMode(Enum):
    """OCR accuracy vs speed trade-off."""
    FAST = "fast"           # Less preprocessing, faster
    BALANCED = "balanced"   # Moderate preprocessing
    ACCURATE = "accurate"   # Full preprocessing, slower


@dataclass
class OCRSettings:
    """Settings for OCR processing."""
    language: str = "eng"
    output_format: OutputFormat = OutputFormat.TEXT
    dpi: int = 300
    accuracy_mode: AccuracyMode = AccuracyMode.BALANCED
    force_ocr: bool = False  # Force OCR even if text exists
    include_page_separators: bool = False  # Include "--- Page X ---" separators in text output


@dataclass
class OCRResult:
    """Result of OCR processing."""
    success: bool
    output_path: Optional[str] = None
    total_pages: int = 0
    pages_with_text: int = 0
    error_message: Optional[str] = None
    skipped_ocr: bool = False  # True if PDF already had text


class OCRService:
    """
    Service for performing OCR on PDF documents.
    
    Converts scanned or image-based PDFs to:
    - Plain text files (.txt)
    - Searchable PDFs (original pages with text layer)
    """
    
    # Minimum DPI for OCR quality
    MIN_OCR_DPI = 300
    
    # Common Tesseract installation paths on Windows
    TESSERACT_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    
    def __init__(self):
        """Initialize the OCR service."""
        self._configure_tesseract_path()
        self._verify_tesseract()
    
    def _get_bundled_tesseract_path(self) -> Optional[str]:
        """
        Get the path to bundled Tesseract OCR for PyInstaller distribution.
        
        When the app is bundled with PyInstaller, Tesseract is placed in
        a 'tesseract' subfolder relative to the executable.
        
        Returns:
            Path to bundled tesseract.exe if found, None otherwise.
        """
        import sys
        
        # When running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Get the directory where the executable is located
            exe_dir = os.path.dirname(sys.executable)
            
            # Check for tesseract in subdirectory
            bundled_path = os.path.join(exe_dir, 'tesseract', 'tesseract.exe')
            if os.path.isfile(bundled_path):
                return bundled_path
            
            # Also check same directory as executable
            same_dir_path = os.path.join(exe_dir, 'tesseract.exe')
            if os.path.isfile(same_dir_path):
                return same_dir_path
        
        # When running in development, check relative to project
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Check various possible locations
        dev_paths = [
            os.path.join(project_dir, 'tesseract', 'tesseract.exe'),
            os.path.join(project_dir, 'tesseract-portable', 'tesseract.exe'),
            os.path.join(project_dir, 'Tesseract-OCR', 'tesseract.exe'),
        ]
        
        for path in dev_paths:
            if os.path.isfile(path):
                return path
        
        return None
    
    def _get_bundled_tessdata_path(self) -> Optional[str]:
        """
        Get the path to bundled tessdata (language data) folder.
        
        Returns:
            Path to tessdata folder if found, None otherwise.
        """
        import sys
        
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            tessdata_path = os.path.join(exe_dir, 'tesseract', 'tessdata')
            if os.path.isdir(tessdata_path):
                return tessdata_path
        
        return None
    
    def _configure_tesseract_path(self):
        """
        Try to find and configure Tesseract executable path.
        
        Search order:
        1. Bundled Tesseract (for PyInstaller distribution)
        2. Already configured/accessible Tesseract
        3. Common system installation paths
        4. Registry-based installed path
        """
        # First, check for bundled Tesseract (highest priority for distributions)
        bundled_path = self._get_bundled_tesseract_path()
        if bundled_path:
            pytesseract.pytesseract.tesseract_cmd = bundled_path
            
            # Also set TESSDATA_PREFIX if bundled tessdata exists
            tessdata_path = self._get_bundled_tessdata_path()
            if tessdata_path:
                os.environ['TESSDATA_PREFIX'] = os.path.dirname(tessdata_path)
            return
        
        # Check if tesseract is already accessible
        try:
            pytesseract.get_tesseract_version()
            return  # Already configured and working
        except pytesseract.TesseractNotFoundError:
            pass
        
        # Search common system installation paths
        for path in self.TESSERACT_PATHS:
            if os.path.isfile(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return
        
        # Check Windows registry for installed Tesseract
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Tesseract-OCR") as key:
                install_path = winreg.QueryValueEx(key, "InstallDir")[0]
                reg_tesseract = os.path.join(install_path, "tesseract.exe")
                if os.path.isfile(reg_tesseract):
                    pytesseract.pytesseract.tesseract_cmd = reg_tesseract
                    return
        except (OSError, ImportError):
            pass
    
    def _verify_tesseract(self) -> bool:
        """
        Verify that Tesseract OCR is installed and accessible.
        
        Returns:
            True if Tesseract is available, False otherwise.
        """
        try:
            pytesseract.get_tesseract_version()
            return True
        except pytesseract.TesseractNotFoundError:
            return False
    
    def is_tesseract_available(self) -> bool:
        """Check if Tesseract is available."""
        return self._verify_tesseract()
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of available Tesseract languages.
        
        Returns:
            List of language codes (e.g., ['eng', 'fra', 'deu'])
        """
        try:
            langs = pytesseract.get_languages()
            # Filter out 'osd' (orientation and script detection)
            return [lang for lang in langs if lang != 'osd']
        except Exception:
            return ['eng']  # Default to English if we can't get the list
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize OCR text to use consistent characters while preserving
        important symbols like Greek letters, math symbols, etc.
        
        Args:
            text: Raw OCR text.
            
        Returns:
            Normalized text with consistent formatting.
        """
        if not text:
            return text
        
        # Character replacements for consistency
        # Maps various Unicode variants to standard ASCII where appropriate
        replacements = {
            # Quotes
            '"': '"', '"': '"', '„': '"', '‟': '"',
            ''': "'", ''': "'", '‚': "'", '‛': "'",
            '«': '"', '»': '"',
            # Dashes and hyphens
            '–': '-', '—': '-', '‐': '-', '‑': '-', '‒': '-',
            '−': '-',  # Minus sign to hyphen
            # Spaces (normalize various space characters to regular space)
            '\u00a0': ' ',  # Non-breaking space
            '\u2000': ' ', '\u2001': ' ', '\u2002': ' ', '\u2003': ' ',
            '\u2004': ' ', '\u2005': ' ', '\u2006': ' ', '\u2007': ' ',
            '\u2008': ' ', '\u2009': ' ', '\u200a': ' ', '\u202f': ' ',
            '\u205f': ' ',
            # Bullets and list markers
            '•': '*', '◦': '*', '▪': '*', '▫': '*',
            '●': '*', '○': '*',
            # Ellipsis
            '…': '...',
            # Fractions (keep as-is, they're useful)
            # Greek letters - PRESERVE these (commonly used in math/science)
            # Math symbols - PRESERVE these
            # Degree symbol - PRESERVE
            # Multiplication/division - keep recognizable
            '×': 'x',  # Some contexts prefer 'x' for multiplication
            '÷': '/',
        }
        
        # Apply replacements
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove zero-width characters that can cause rendering issues
        zero_width_chars = [
            '\u200b',  # Zero-width space
            '\u200c',  # Zero-width non-joiner
            '\u200d',  # Zero-width joiner
            '\ufeff',  # Byte order mark
            '\u2060',  # Word joiner
        ]
        for char in zero_width_chars:
            text = text.replace(char, '')
        
        # Clean up multiple spaces (but preserve intentional indentation)
        text = re.sub(r'[^\S\n]+', ' ', text)  # Replace multiple spaces with single space
        
        # Clean up multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def pdf_has_text(self, pdf_path: str) -> Tuple[bool, int]:
        """
        Check if a PDF already contains extractable text.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Tuple of (has_text, page_count)
        """
        try:
            reader = PdfReader(pdf_path)
            page_count = len(reader.pages)
            
            # Check first few pages for text
            pages_to_check = min(3, page_count)
            for i in range(pages_to_check):
                text = reader.pages[i].extract_text()
                if text and text.strip():
                    return True, page_count
            
            return False, page_count
        except Exception:
            return False, 0
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Number of pages.
        """
        try:
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception:
            return 0
    
    def process_pdf(
        self,
        pdf_path: str,
        output_path: str,
        settings: OCRSettings,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> OCRResult:
        """
        Process a PDF with OCR.
        
        Args:
            pdf_path: Path to the input PDF.
            output_path: Path for the output file.
            settings: OCR settings.
            progress_callback: Optional callback(current_page, total_pages, status_message)
            
        Returns:
            OCRResult with processing outcome.
        """
        # Enforce minimum DPI for OCR
        effective_dpi = max(settings.dpi, self.MIN_OCR_DPI)
        
        # Check if PDF already has text
        has_text, page_count = self.pdf_has_text(pdf_path)
        
        if has_text and not settings.force_ocr:
            # Extract existing text instead of running OCR
            if progress_callback:
                progress_callback(0, page_count, "PDF already contains text, extracting...")
            
            if settings.output_format == OutputFormat.TEXT:
                return self._extract_existing_text(pdf_path, output_path, settings, progress_callback)
            else:
                # For searchable PDF, just copy the original since it already has text
                shutil.copy(pdf_path, output_path)
                return OCRResult(
                    success=True,
                    output_path=output_path,
                    total_pages=page_count,
                    pages_with_text=page_count,
                    skipped_ocr=True
                )
        
        # Perform OCR
        if settings.output_format == OutputFormat.TEXT:
            return self._ocr_to_text(pdf_path, output_path, settings, effective_dpi, progress_callback)
        else:
            return self._ocr_to_searchable_pdf(pdf_path, output_path, settings, effective_dpi, progress_callback)
    
    def _extract_existing_text(
        self,
        pdf_path: str,
        output_path: str,
        settings: OCRSettings,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> OCRResult:
        """Extract text from a PDF that already contains text."""
        try:
            reader = PdfReader(pdf_path)
            page_count = len(reader.pages)
            all_text = []
            
            for i, page in enumerate(reader.pages):
                if progress_callback:
                    progress_callback(i + 1, page_count, f"Extracting text from page {i + 1}...")
                
                text = page.extract_text()
                if text:
                    # Normalize the extracted text for consistent formatting
                    normalized_text = self._normalize_text(text)
                    if settings.include_page_separators:
                        all_text.append(f"--- Page {i + 1} ---\n{normalized_text}\n")
                    else:
                        all_text.append(normalized_text)
            
            # Write to output file
            separator = '\n' if settings.include_page_separators else '\n\n'
            final_text = separator.join(all_text)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_text)
            
            return OCRResult(
                success=True,
                output_path=output_path,
                total_pages=page_count,
                pages_with_text=len(all_text),
                skipped_ocr=True
            )
        except Exception as e:
            return OCRResult(
                success=False,
                error_message=f"Failed to extract text: {str(e)}"
            )
    
    def _ocr_to_text(
        self,
        pdf_path: str,
        output_path: str,
        settings: OCRSettings,
        effective_dpi: int,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> OCRResult:
        """Perform OCR and save result as plain text."""
        temp_dir = None
        try:
            # Create temporary directory for images
            temp_dir = tempfile.mkdtemp()
            
            if progress_callback:
                progress_callback(0, 0, "Converting PDF to images...")
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=effective_dpi)
            page_count = len(images)
            all_text = []
            pages_with_text = 0
            
            for i, image in enumerate(images):
                if progress_callback:
                    progress_callback(i + 1, page_count, f"Processing page {i + 1} of {page_count}...")
                
                # Preprocess image
                processed_image = self._preprocess_image(image, settings.accuracy_mode)
                
                # Run OCR
                text = pytesseract.image_to_string(
                    processed_image,
                    lang=settings.language,
                    config=self._get_tesseract_config(settings.accuracy_mode)
                )
                
                if text and text.strip():
                    # Normalize the OCR text for consistent formatting
                    normalized_text = self._normalize_text(text)
                    if settings.include_page_separators:
                        all_text.append(f"--- Page {i + 1} ---\n{normalized_text}\n")
                    else:
                        all_text.append(normalized_text)
                    pages_with_text += 1
            
            # Write output - apply final normalization to the combined text
            separator = '\n' if settings.include_page_separators else '\n\n'
            final_text = separator.join(all_text)
            final_text = self._normalize_text(final_text)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_text)
            
            return OCRResult(
                success=True,
                output_path=output_path,
                total_pages=page_count,
                pages_with_text=pages_with_text
            )
            
        except Exception as e:
            return OCRResult(
                success=False,
                error_message=f"OCR failed: {str(e)}"
            )
        finally:
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _ocr_to_searchable_pdf(
        self,
        pdf_path: str,
        output_path: str,
        settings: OCRSettings,
        effective_dpi: int,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> OCRResult:
        """Perform OCR and create searchable PDF with text layer."""
        temp_dir = None
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            if progress_callback:
                progress_callback(0, 0, "Converting PDF to images...")
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=effective_dpi)
            page_count = len(images)
            pages_with_text = 0
            
            # Create output PDF
            writer = PdfWriter()
            
            for i, image in enumerate(images):
                if progress_callback:
                    progress_callback(i + 1, page_count, f"Processing page {i + 1} of {page_count}...")
                
                # Preprocess image for OCR
                processed_image = self._preprocess_image(image, settings.accuracy_mode)
                
                # Get OCR data with bounding boxes
                ocr_data = pytesseract.image_to_data(
                    processed_image,
                    lang=settings.language,
                    config=self._get_tesseract_config(settings.accuracy_mode),
                    output_type=pytesseract.Output.DICT
                )
                
                # Check if any text was found
                has_text = any(
                    text.strip() 
                    for text in ocr_data['text'] 
                    if text and text.strip()
                )
                if has_text:
                    pages_with_text += 1
                
                # Save original image as PDF page
                page_pdf_path = os.path.join(temp_dir, f"page_{i}.pdf")
                image.save(page_pdf_path, "PDF", resolution=effective_dpi)
                
                # Create text layer PDF
                text_layer_path = os.path.join(temp_dir, f"text_layer_{i}.pdf")
                self._create_text_layer(
                    text_layer_path,
                    ocr_data,
                    image.width,
                    image.height,
                    effective_dpi
                )
                
                # Merge image page with text layer
                page_reader = PdfReader(page_pdf_path)
                text_reader = PdfReader(text_layer_path)
                
                page = page_reader.pages[0]
                text_page = text_reader.pages[0]
                
                # Merge text layer under the image (so text is selectable but invisible)
                page.merge_page(text_page)
                writer.add_page(page)
            
            # Write final PDF
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            return OCRResult(
                success=True,
                output_path=output_path,
                total_pages=page_count,
                pages_with_text=pages_with_text
            )
            
        except Exception as e:
            return OCRResult(
                success=False,
                error_message=f"OCR failed: {str(e)}"
            )
        finally:
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _preprocess_image(self, image: Image.Image, accuracy_mode: AccuracyMode) -> Image.Image:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: PIL Image to preprocess.
            accuracy_mode: Level of preprocessing to apply.
            
        Returns:
            Preprocessed PIL Image.
        """
        # Convert PIL Image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        if accuracy_mode == AccuracyMode.FAST:
            # Minimal preprocessing - just grayscale
            return Image.fromarray(gray)
        
        # Apply adaptive thresholding for better text contrast
        if accuracy_mode == AccuracyMode.ACCURATE:
            # Full preprocessing
            # Noise removal
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # Adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Deskew
            coords = np.column_stack(np.where(thresh > 0))
            if len(coords) > 0:
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = 90 + angle
                if abs(angle) > 0.5:  # Only deskew if angle is significant
                    (h, w) = thresh.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    thresh = cv2.warpAffine(
                        thresh, M, (w, h),
                        flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE
                    )
            
            return Image.fromarray(thresh)
        
        else:  # BALANCED mode
            # Moderate preprocessing
            # Light denoising
            denoised = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Otsu's thresholding
            _, thresh = cv2.threshold(
                denoised, 0, 255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            
            return Image.fromarray(thresh)
    
    def _get_tesseract_config(self, accuracy_mode: AccuracyMode) -> str:
        """
        Get Tesseract configuration based on accuracy mode.
        
        Args:
            accuracy_mode: The accuracy mode setting.
            
        Returns:
            Tesseract config string.
        """
        if accuracy_mode == AccuracyMode.FAST:
            # Fast mode - use legacy engine
            return '--oem 0 --psm 3'
        elif accuracy_mode == AccuracyMode.ACCURATE:
            # Accurate mode - LSTM engine with more analysis
            return '--oem 1 --psm 3'
        else:
            # Balanced - LSTM with standard settings
            return '--oem 1 --psm 3'
    
    def _create_text_layer(
        self,
        output_path: str,
        ocr_data: dict,
        width: int,
        height: int,
        dpi: int
    ):
        """
        Create a PDF with invisible text layer for searchability.
        
        Args:
            output_path: Path for the text layer PDF.
            ocr_data: OCR data dictionary from pytesseract.
            width: Image width in pixels.
            height: Image height in pixels.
            dpi: DPI of the image.
        """
        # Calculate page size in points (72 points per inch)
        page_width = (width / dpi) * 72
        page_height = (height / dpi) * 72
        
        c = canvas.Canvas(output_path, pagesize=(page_width, page_height))
        
        # Set invisible text (white with 0 opacity would work, or very small)
        c.setFillColorRGB(1, 1, 1, 0)  # Transparent white
        
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            text = ocr_data['text'][i]
            if text and text.strip():
                # Get bounding box coordinates
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                
                # Convert pixel coordinates to points
                x_pt = (x / dpi) * 72
                # PDF coordinates start from bottom, image from top
                y_pt = page_height - ((y + h) / dpi) * 72
                
                # Estimate font size from box height
                font_size = max(6, (h / dpi) * 72 * 0.8)
                
                try:
                    c.setFont("Helvetica", font_size)
                    c.drawString(x_pt, y_pt, text)
                except Exception:
                    pass  # Skip problematic text
        
        c.save()
