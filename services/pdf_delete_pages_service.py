"""
PDF delete pages service.
Handles deleting specific pages from PDF files.
"""
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from typing import List


class PdfDeletePagesService:
    """Service for deleting pages from PDF files."""
    
    def delete_pages(
        self,
        pdf_path: str,
        output_path: str,
        pages_to_delete: List[int]
    ) -> bool:
        """
        Delete specific pages from a PDF.
        
        Args:
            pdf_path: Path to the source PDF file
            output_path: Path where the modified PDF should be saved
            pages_to_delete: List of page numbers to delete (1-indexed)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pdf_reader = PdfReader(pdf_path)
            pdf_writer = PdfWriter()
            
            total_pages = len(pdf_reader.pages)
            
            # Validate page numbers
            for page_num in pages_to_delete:
                if page_num < 1 or page_num > total_pages:
                    raise ValueError(f"Invalid page number: {page_num}. PDF has {total_pages} pages.")
            
            # Convert to 0-indexed set for faster lookup
            pages_to_delete_set = set(p - 1 for p in pages_to_delete)
            
            # Add pages that are NOT in the delete list
            for page_num in range(total_pages):
                if page_num not in pages_to_delete_set:
                    pdf_writer.add_page(pdf_reader.pages[page_num])
            
            # Check if any pages remain
            if len(pdf_writer.pages) == 0:
                raise ValueError("Cannot delete all pages from the PDF.")
            
            # Write the output PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            return True
            
        except Exception as e:
            print(f"Error deleting pages from PDF: {e}")
            raise
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the total number of pages in a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of pages in the PDF
        """
        try:
            pdf_reader = PdfReader(pdf_path)
            return len(pdf_reader.pages)
        except Exception as e:
            print(f"Error reading PDF: {e}")
            raise
