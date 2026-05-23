"""
PDF merge service.
Handles merging multiple PDF files into a single document.
"""
from typing import List
from pypdf import PdfWriter, PdfReader


class PdfMergeService:
    """Service for merging PDF files."""
    
    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> bool:
        """
        Merge multiple PDF files into a single PDF.
        
        Args:
            pdf_paths: List of paths to PDF files (in order)
            output_path: Path where the merged PDF should be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create PDF writer
            pdf_writer = PdfWriter()
            
            # Add all pages from each PDF
            for pdf_path in pdf_paths:
                pdf_reader = PdfReader(pdf_path)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
            
            # Write the merged PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            return True
            
        except Exception as e:
            print(f"Error merging PDFs: {e}")
            return False
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get information about a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF information (page count, etc.)
        """
        try:
            pdf_reader = PdfReader(pdf_path)
            return {
                'page_count': len(pdf_reader.pages),
                'metadata': pdf_reader.metadata
            }
        except Exception as e:
            print(f"Error reading PDF info: {e}")
            return {'page_count': 0, 'metadata': None}
