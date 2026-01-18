"""
PDF to Images conversion service.
Handles converting PDF pages to images and packaging them in a ZIP file.
"""
from pathlib import Path
from typing import Optional
import zipfile
import tempfile
import os
import shutil

from PIL import Image


class PdfToImagesService:
    """Service for converting PDF pages to images."""
    
    def convert_pdf_to_images_zip(
        self,
        pdf_path: str,
        output_zip_path: str,
        image_format: str = "PNG",
        dpi: int = 150
    ) -> bool:
        """
        Convert all pages of a PDF to images and save as a ZIP file.
        
        Args:
            pdf_path: Path to the source PDF file
            output_zip_path: Path where the ZIP file should be saved
            image_format: Output image format (PNG or JPG)
            dpi: Resolution in dots per inch (higher = better quality, larger files)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Converting PDF to images: {pdf_path}")
            print(f"Output ZIP: {output_zip_path}")
            print(f"Format: {image_format}, DPI: {dpi}")
            
            # Import pdf2image here to avoid import errors if not installed
            try:
                from pdf2image import convert_from_path
                from pdf2image.exceptions import PDFInfoNotInstalledError
            except ImportError:
                # Fallback to pypdf + PIL method
                return self._convert_with_pypdf(pdf_path, output_zip_path, image_format)
            
            # Try using pdf2image (requires poppler)
            try:
                images = convert_from_path(pdf_path, dpi=dpi)
            except PDFInfoNotInstalledError:
                print("Poppler not installed, falling back to pypdf method")
                return self._convert_with_pypdf(pdf_path, output_zip_path, image_format)
            except Exception as e:
                print(f"pdf2image failed: {e}, falling back to pypdf method")
                return self._convert_with_pypdf(pdf_path, output_zip_path, image_format)
            
            # Get base filename without extension
            base_name = Path(pdf_path).stem
            
            # Create ZIP file with images
            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i, image in enumerate(images, start=1):
                    # Create filename with zero-padded page number
                    ext = 'png' if image_format.upper() == 'PNG' else 'jpg'
                    image_filename = f"{base_name}_page_{i:03d}.{ext}"
                    
                    # Save image to a temporary file, then add to ZIP
                    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
                        if image_format.upper() == 'PNG':
                            image.save(tmp.name, 'PNG')
                        else:
                            image.save(tmp.name, 'JPEG', quality=95)
                        
                        # Add to ZIP
                        zipf.write(tmp.name, image_filename)
                        
                        # Clean up temp file
                        os.unlink(tmp.name)
                    
                    print(f"  Added: {image_filename}")
            
            print(f"✓ Created ZIP with {len(images)} images")
            return True
            
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            import traceback
            traceback.print_exc()
            
            # Clean up partial ZIP file
            try:
                if Path(output_zip_path).exists():
                    Path(output_zip_path).unlink()
            except Exception:
                pass
            
            raise
    
    def _convert_with_pypdf(
        self,
        pdf_path: str,
        output_zip_path: str,
        image_format: str = "PNG"
    ) -> bool:
        """
        Fallback method using PyMuPDF to render PDF pages to images.
        """
        import fitz  # PyMuPDF
        
        print("Using PyMuPDF for PDF rendering...")
        
        doc = fitz.open(pdf_path)
        base_name = Path(pdf_path).stem
        
        # Create a temporary directory for images
        temp_dir = tempfile.mkdtemp()
        
        try:
            image_files = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Render page to image (2x zoom for good quality)
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)
                
                ext = 'png' if image_format.upper() == 'PNG' else 'jpg'
                image_filename = f"{base_name}_page_{page_num + 1:03d}.{ext}"
                temp_image_path = os.path.join(temp_dir, image_filename)
                
                # Save directly to the temp directory
                if image_format.upper() == 'PNG':
                    pix.save(temp_image_path)
                else:
                    # Convert to PIL for JPEG with quality setting
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img.save(temp_image_path, 'JPEG', quality=95)
                
                image_files.append((temp_image_path, image_filename))
                print(f"  Rendered: {image_filename}")
            
            doc.close()
            
            # Create ZIP file with all images
            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for temp_path, filename in image_files:
                    zipf.write(temp_path, filename)
                    print(f"  Added to ZIP: {filename}")
            
            print(f"✓ Created ZIP with {len(image_files)} images")
            return True
            
        finally:
            # Clean up temp directory
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not clean up temp directory: {e}")
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of pages, or 0 if error
        """
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return 0
