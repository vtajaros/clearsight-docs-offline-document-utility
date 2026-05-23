"""
PDF split service.
Handles splitting PDF files by page range or into individual pages.
"""
from pathlib import Path
from pypdf import PdfWriter, PdfReader


class PdfSplitService:
    """Service for splitting PDF files."""
    
    def split_by_range(
        self,
        pdf_path: str,
        output_path: str,
        start_page: int,
        end_page: int
    ) -> bool:
        """
        Extract a range of pages from a PDF.
        
        Args:
            pdf_path: Path to the source PDF file
            output_path: Path where the split PDF should be saved
            start_page: First page to extract (1-indexed)
            end_page: Last page to extract (1-indexed, inclusive)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pdf_reader = PdfReader(pdf_path)
            pdf_writer = PdfWriter()
            
            # Validate page range
            total_pages = len(pdf_reader.pages)
            if start_page < 1 or end_page > total_pages or start_page > end_page:
                raise ValueError(f"Invalid page range. PDF has {total_pages} pages.")
            
            # Add pages to writer (convert from 1-indexed to 0-indexed)
            for page_num in range(start_page - 1, end_page):
                pdf_writer.add_page(pdf_reader.pages[page_num])
            
            # Write the output PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            return True
            
        except Exception as e:
            print(f"Error splitting PDF by range: {e}")
            return False
    
    def split_into_pages(self, pdf_path: str, output_dir: str) -> bool:
        """
        Split a PDF into individual pages.
        
        Args:
            pdf_path: Path to the source PDF file
            output_dir: Directory where individual page PDFs should be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pdf_reader = PdfReader(pdf_path)
            total_pages = len(pdf_reader.pages)
            
            # Get the base filename
            base_name = Path(pdf_path).stem
            output_dir_path = Path(output_dir)
            
            # Create output directory if it doesn't exist
            output_dir_path.mkdir(parents=True, exist_ok=True)
            
            # Split each page
            for page_num in range(total_pages):
                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])
                
                # Create output filename with zero-padded page number
                output_filename = f"{base_name}_page_{page_num + 1:03d}.pdf"
                output_path = output_dir_path / output_filename
                
                # Write the page
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
            
            return True
            
        except Exception as e:
            print(f"Error splitting PDF into pages: {e}")
            return False
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of pages, or 0 if error
        """
        try:
            pdf_reader = PdfReader(pdf_path)
            return len(pdf_reader.pages)
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return 0
