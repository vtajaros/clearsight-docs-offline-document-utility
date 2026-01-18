"""
PDF extract pages service.
Handles extracting specific pages from PDF files.
"""
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from typing import List


class PdfExtractPagesService:
    """Service for extracting specific pages from PDF files."""
    
    def extract_pages(
        self,
        pdf_path: str,
        output_path: str,
        pages_to_extract: List[int]
    ) -> bool:
        """
        Extract specific pages from a PDF into a new PDF.
        
        Args:
            pdf_path: Path to the source PDF file
            output_path: Path where the extracted PDF should be saved
            pages_to_extract: List of page numbers to extract (1-indexed)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pdf_reader = PdfReader(pdf_path)
            pdf_writer = PdfWriter()
            
            total_pages = len(pdf_reader.pages)
            
            # Validate page numbers
            for page_num in pages_to_extract:
                if page_num < 1 or page_num > total_pages:
                    raise ValueError(f"Invalid page number: {page_num}. PDF has {total_pages} pages.")
            
            if not pages_to_extract:
                raise ValueError("No pages specified to extract.")
            
            # Sort pages and add them in order
            sorted_pages = sorted(set(pages_to_extract))
            
            # Add specified pages (convert from 1-indexed to 0-indexed)
            for page_num in sorted_pages:
                pdf_writer.add_page(pdf_reader.pages[page_num - 1])
            
            # Write the output PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            return True
            
        except Exception as e:
            print(f"Error extracting pages from PDF: {e}")
            raise
    
    def extract_pages_preserve_order(
        self,
        pdf_path: str,
        output_path: str,
        pages_to_extract: List[int]
    ) -> bool:
        """
        Extract specific pages from a PDF into a new PDF, preserving the specified order.
        
        Args:
            pdf_path: Path to the source PDF file
            output_path: Path where the extracted PDF should be saved
            pages_to_extract: List of page numbers to extract (1-indexed), in desired order
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pdf_reader = PdfReader(pdf_path)
            pdf_writer = PdfWriter()
            
            total_pages = len(pdf_reader.pages)
            
            # Validate page numbers
            for page_num in pages_to_extract:
                if page_num < 1 or page_num > total_pages:
                    raise ValueError(f"Invalid page number: {page_num}. PDF has {total_pages} pages.")
            
            if not pages_to_extract:
                raise ValueError("No pages specified to extract.")
            
            # Add pages in the specified order (convert from 1-indexed to 0-indexed)
            for page_num in pages_to_extract:
                pdf_writer.add_page(pdf_reader.pages[page_num - 1])
            
            # Write the output PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            return True
            
        except Exception as e:
            print(f"Error extracting pages from PDF: {e}")
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
