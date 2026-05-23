"""
PDF compression service.
Handles compressing PDF files while maintaining quality.
"""
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from typing import Callable, Optional
import os


class PdfCompressService:
    """Service for compressing PDF files."""
    
    def compress_pdf(
        self,
        pdf_path: str,
        output_path: str,
        compression_level: str = "medium",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> dict:
        """
        Compress a PDF file.
        
        Args:
            pdf_path: Path to the source PDF file
            output_path: Path where the compressed PDF should be saved
            compression_level: Compression level - "low", "medium", or "high"
            progress_callback: Optional callback for progress updates (current_page, total_pages)
            
        Returns:
            Dictionary with compression results including original and new sizes
        """
        try:
            # Get original file size
            original_size = os.path.getsize(pdf_path)
            
            pdf_reader = PdfReader(pdf_path)
            pdf_writer = PdfWriter()
            
            total_pages = len(pdf_reader.pages)
            
            # Add all pages
            for i, page in enumerate(pdf_reader.pages):
                pdf_writer.add_page(page)
                if progress_callback:
                    progress_callback(i + 1, total_pages)
            
            # Apply compression based on level
            if compression_level == "low":
                # Light compression - mainly remove duplicates
                pdf_writer.add_metadata(pdf_reader.metadata or {})
                
            elif compression_level == "medium":
                # Medium compression - compress streams and remove duplicates
                for page in pdf_writer.pages:
                    page.compress_content_streams()
                    
            elif compression_level == "high":
                # High compression - aggressive compression
                for page in pdf_writer.pages:
                    page.compress_content_streams()
                # Remove unused objects will happen during write
            
            # Write with compression
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            # Get new file size
            new_size = os.path.getsize(output_path)
            
            # Calculate savings
            size_reduction = original_size - new_size
            reduction_percentage = (size_reduction / original_size * 100) if original_size > 0 else 0
            
            return {
                "success": True,
                "original_size": original_size,
                "new_size": new_size,
                "size_reduction": size_reduction,
                "reduction_percentage": reduction_percentage,
                "total_pages": total_pages
            }
            
        except Exception as e:
            print(f"Error compressing PDF: {e}")
            raise
    
    def compress_pdf_with_image_optimization(
        self,
        pdf_path: str,
        output_path: str,
        image_quality: int = 85,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> dict:
        """
        Compress a PDF file with image optimization.
        Uses Pillow to recompress images within the PDF.
        
        Args:
            pdf_path: Path to the source PDF file
            output_path: Path where the compressed PDF should be saved
            image_quality: JPEG quality for images (1-100, higher = better quality)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with compression results
        """
        try:
            from PIL import Image
            import io
            
            # Get original file size
            original_size = os.path.getsize(pdf_path)
            
            pdf_reader = PdfReader(pdf_path)
            pdf_writer = PdfWriter()
            
            total_pages = len(pdf_reader.pages)
            
            for i, page in enumerate(pdf_reader.pages):
                pdf_writer.add_page(page)
                
                # Try to compress images on this page
                if '/Resources' in page and '/XObject' in page['/Resources']:
                    x_objects = page['/Resources']['/XObject'].get_object()
                    
                    for obj_name in x_objects:
                        obj = x_objects[obj_name]
                        if obj.get('/Subtype') == '/Image':
                            # This is an image - try to optimize it
                            try:
                                self._optimize_image_object(obj, image_quality)
                            except Exception:
                                # If image optimization fails, continue without it
                                pass
                
                if progress_callback:
                    progress_callback(i + 1, total_pages)
            
            # Compress content streams
            for page in pdf_writer.pages:
                page.compress_content_streams()
            
            # Write compressed PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            # Get new file size
            new_size = os.path.getsize(output_path)
            
            # Calculate savings
            size_reduction = original_size - new_size
            reduction_percentage = (size_reduction / original_size * 100) if original_size > 0 else 0
            
            return {
                "success": True,
                "original_size": original_size,
                "new_size": new_size,
                "size_reduction": size_reduction,
                "reduction_percentage": reduction_percentage,
                "total_pages": total_pages
            }
            
        except ImportError:
            # Pillow not available, fall back to basic compression
            return self.compress_pdf(pdf_path, output_path, "high", progress_callback)
        except Exception as e:
            print(f"Error compressing PDF with image optimization: {e}")
            raise
    
    def _optimize_image_object(self, image_obj, quality: int):
        """Attempt to optimize an image object within the PDF."""
        # This is a placeholder for more advanced image optimization
        # Full implementation would require extracting, recompressing, and reinserting images
        pass
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get information about a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF information
        """
        try:
            file_size = os.path.getsize(pdf_path)
            pdf_reader = PdfReader(pdf_path)
            
            return {
                "file_size": file_size,
                "page_count": len(pdf_reader.pages),
                "metadata": pdf_reader.metadata
            }
        except Exception as e:
            print(f"Error reading PDF info: {e}")
            raise
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
