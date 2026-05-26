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

        Raises:
            ValueError: If any page index is out of range.
        """
        try:
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)

            out_of_range = [p for p in pages_to_delete if p < 0 or p >= total_pages]
            if out_of_range:
                raise ValueError(
                    f"Page index out of range: {out_of_range}. "
                    f"PDF has {total_pages} pages (0-indexed 0–{total_pages - 1})."
                )

            writer = PdfWriter()
            delete_set = set(pages_to_delete)
            for i, page in enumerate(reader.pages):
                if i not in delete_set:
                    writer.add_page(page)

            with open(output_path, "wb") as f:
                writer.write(f)

            return True

        except ValueError:
            raise  # Let the API layer handle this as a 400
        except Exception as e:
            print(f"Error in delete_pages: {e}")
            return False