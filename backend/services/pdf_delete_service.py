import os
from pypdf import PdfReader, PdfWriter

class PdfDeleteService:
    def delete_pages(self, input_path: str, output_path: str, pages_to_delete: list[int]) -> bool:
        """
        Delete specified pages from a PDF.
        
        Args:
            input_path: Path to the input PDF.
            output_path: Path to save the output PDF.
            pages_to_delete: A list of 0-indexed page numbers to delete.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            delete_set = set(pages_to_delete)
            for i, page in enumerate(reader.pages):
                if i not in delete_set:
                    writer.add_page(page)
                    
            with open(output_path, "wb") as f:
                writer.write(f)
                
            return True
        except Exception as e:
            print(f"Error in delete_pages: {e}")
            return False
