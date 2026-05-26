"""
PDF compression service.
Handles compressing PDF files while maintaining quality.

Compression levels:
  low    — stream-only compression via pypdf (fast, minimal size reduction)
  medium — stream compression + image recompression at 75% JPEG quality
  high   — stream compression + aggressive image recompression at 45% JPEG quality
"""
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from typing import Callable, Optional
import os
import io
import tempfile
import shutil


class PdfCompressService:
    """Service for compressing PDF files."""

    # JPEG quality per compression level for image recompression
    IMAGE_QUALITY = {
        "low": None,   # No image recompression
        "medium": 75,
        "high": 45,
    }

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
            compression_level: "low", "medium", or "high"
            progress_callback: Optional callback(current_page, total_pages)

        Returns:
            Dict with original_size, new_size, reduction_percentage, success.
        """
        try:
            original_size = os.path.getsize(pdf_path)
            image_quality = self.IMAGE_QUALITY.get(compression_level)

            if image_quality is not None:
                # Medium / high: recompress images via PyMuPDF then stream-compress
                work_path = self._recompress_images(pdf_path, image_quality, progress_callback)
                try:
                    self._stream_compress(work_path, output_path)
                finally:
                    try:
                        os.unlink(work_path)
                    except Exception:
                        pass
            else:
                # Low: stream compression only
                self._stream_compress(pdf_path, output_path, progress_callback)

            new_size = os.path.getsize(output_path)
            size_reduction = original_size - new_size
            reduction_pct = (size_reduction / original_size * 100) if original_size > 0 else 0.0

            return {
                "success": True,
                "original_size": original_size,
                "new_size": new_size,
                "size_reduction": size_reduction,
                "reduction_percentage": round(reduction_pct, 2),
            }

        except Exception as e:
            print(f"Error compressing PDF: {e}")
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _stream_compress(
        self,
        src_path: str,
        dst_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """Write a pypdf copy with content-stream compression."""
        reader = PdfReader(src_path)
        writer = PdfWriter()
        total = len(reader.pages)
        for i, page in enumerate(reader.pages):
            added_page = writer.add_page(page)
            added_page.compress_content_streams()
            if progress_callback:
                progress_callback(i + 1, total)
        with open(dst_path, "wb") as f:
            writer.write(f)

    def _recompress_images(
        self,
        pdf_path: str,
        jpeg_quality: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        Use PyMuPDF to recompress all raster images in the PDF at the given
        JPEG quality. Returns the path to a temporary file — caller must delete it.
        """
        import fitz
        from PIL import Image

        doc = fitz.open(pdf_path)
        total = len(doc)

        for page_index in range(total):
            page = doc[page_index]
            if progress_callback:
                progress_callback(page_index + 1, total)

            for img in page.get_images(full=True):
                xref = img[0]
                try:
                    base = doc.extract_image(xref)
                    raw = base["image"]
                    ext = base["ext"].lower()

                    # Only recompress raster images (skip jbig2, ccitt, etc.)
                    if ext not in ("jpeg", "jpg", "png", "bmp", "tiff", "tif"):
                        continue

                    pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
                    buf = io.BytesIO()
                    pil_img.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
                    buf.seek(0)

                    doc.update_image(xref, stream=buf.read())
                except Exception:
                    # Skip images that can't be recompressed (e.g. masks, forms)
                    continue

        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, prefix="cs_compress_")
        tmp.close()
        doc.save(tmp.name, garbage=4, deflate=True, clean=True)
        doc.close()
        return tmp.name

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def get_pdf_info(self, pdf_path: str) -> dict:
        try:
            return {
                "file_size": os.path.getsize(pdf_path),
                "page_count": len(PdfReader(pdf_path).pages),
            }
        except Exception as e:
            print(f"Error reading PDF info: {e}")
            raise