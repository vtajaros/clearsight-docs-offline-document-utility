"""
PDF compression service.
Handles compressing PDF files while maintaining quality.

Compression levels:
  low    — stream-only deflate via PyMuPDF (fast, safe)
  medium — image recompression at 75% JPEG quality + deflate
  high   — image recompression at 45% JPEG quality + deflate
"""
from typing import Callable, Optional
import os
import io
import time


class PdfCompressService:

    IMAGE_QUALITY = {
        "low": None,
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
        try:
            original_size = os.path.getsize(pdf_path)
            image_quality = self.IMAGE_QUALITY.get(compression_level)

            if image_quality is not None:
                self._recompress_images(pdf_path, output_path, image_quality, progress_callback)
            else:
                self._stream_compress_only(pdf_path, output_path, progress_callback)

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

    def _stream_compress_only(
        self,
        src_path: str,
        dst_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """Low mode: single-pass PyMuPDF deflate, no image recompression."""
        import fitz
        doc = fitz.open(src_path)
        total = len(doc)
        if progress_callback:
            progress_callback(0, total)
        doc.save(dst_path, garbage=4, deflate=True, deflate_images=True,
                 deflate_fonts=True, clean=True)
        if progress_callback:
            progress_callback(total, total)
        doc.close()

    def _recompress_images(
        self,
        pdf_path: str,
        output_path: str,
        jpeg_quality: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        import fitz
        from PIL import Image

        doc = fitz.open(pdf_path)
        total = len(doc)
        seen_xrefs: set[int] = set()
        total_saved = 0
        t0 = time.time()

        for page_index in range(total):
            if progress_callback:
                progress_callback(page_index + 1, total)

            page = doc[page_index]

            for img in page.get_images(full=True):
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)

                try:
                    base = doc.extract_image(xref)
                    raw = base["image"]
                    ext = base["ext"].lower()
                    width = base.get("width", 0)
                    height = base.get("height", 0)

                    if width * height < 4096:
                        continue

                    if ext not in ("jpeg", "jpg", "jpx", "jp2", "png",
                                   "bmp", "tiff", "tif", "jxr", "pnm"):
                        continue

                    pil_img = Image.open(io.BytesIO(raw))
                    if pil_img.mode == "RGBA":
                        pil_img = pil_img.convert("RGB")
                    elif pil_img.mode not in ("RGB", "L"):
                        pil_img = pil_img.convert("RGB")

                    buf = io.BytesIO()
                    pil_img.save(buf, format="JPEG", quality=jpeg_quality,
                                 optimize=True, progressive=True)
                    new_bytes = buf.getvalue()

                    if len(new_bytes) >= len(raw):
                        continue

                    # Update the xref stream AND fix the filter/colorspace metadata
                    # so PDF viewers decode the new JPEG bytes correctly
                    doc.update_stream(xref, new_bytes, new=1, compress=0)
                    # Overwrite the filter to DCTDecode (standard JPEG) and clear
                    # any old colorspace/filter entries that would corrupt rendering
                    doc.xref_set_key(xref, "Filter", "/DCTDecode")
                    doc.xref_set_key(xref, "ColorSpace",
                                     "/DeviceGray" if pil_img.mode == "L" else "/DeviceRGB")
                    # Remove JPX/exotic filter entries if present
                    try:
                        doc.xref_set_key(xref, "DecodeParms", "null")
                    except Exception:
                        pass

                    total_saved += len(raw) - len(new_bytes)
                    # ASCII-only print to avoid charmap crash on Windows console
                    print(f"  xref={xref} {ext} {width}x{height} "
                          f"{len(raw)//1024}KB -> {len(new_bytes)//1024}KB")

                except Exception as ex:
                    print(f"  xref={xref} skipped: {repr(ex)}")
                    continue

        print(f"Total image bytes saved: {total_saved // 1024}KB in {time.time()-t0:.1f}s")
        doc.save(output_path, garbage=4, deflate=True,
                 deflate_images=True, deflate_fonts=True, clean=True)
        doc.close()

    def diagnose_pdf(self, pdf_path: str) -> dict:
        import fitz
        from PIL import Image

        doc = fitz.open(pdf_path)
        page_count = len(doc)
        total_images = 0
        image_format_breakdown = {}
        estimated_image_data_bytes = 0
        already_compressed_count = 0
        seen_xrefs = set()

        for page_index in range(page_count):
            page = doc[page_index]
            for img in page.get_images(full=True):
                total_images += 1
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)

                try:
                    base = doc.extract_image(xref)
                    ext = base["ext"].lower()
                    image_format_breakdown[ext] = image_format_breakdown.get(ext, 0) + 1
                    raw = base["image"]
                    orig_size = len(raw)
                    estimated_image_data_bytes += orig_size

                    width = base.get("width", 0)
                    height = base.get("height", 0)

                    if width * height >= 4096 and ext in ("jpeg", "jpg", "jpx", "jp2", "png", "bmp", "tiff", "tif", "jxr", "pnm"):
                        pil_img = Image.open(io.BytesIO(raw))
                        if pil_img.mode not in ("RGB", "L", "RGBA"):
                            pil_img = pil_img.convert("RGB")
                        if pil_img.mode == "RGBA":
                            pil_img = pil_img.convert("RGB")
                        buf = io.BytesIO()
                        pil_img.save(buf, format="JPEG", quality=75, optimize=True, progressive=True)
                        new_size = len(buf.getvalue())
                        if new_size >= orig_size * 0.95:
                            already_compressed_count += 1
                    else:
                        # If tiny or unsupported, we can't save much anyway, consider it already compressed
                        already_compressed_count += 1

                except Exception:
                    continue

        doc.close()

        already_compressed_ratio = 0.0
        if seen_xrefs:
            already_compressed_ratio = already_compressed_count / len(seen_xrefs)

        return {
            "page_count": page_count,
            "total_images": total_images,
            "image_format_breakdown": image_format_breakdown,
            "estimated_image_data_bytes": estimated_image_data_bytes,
            "already_compressed_ratio": round(already_compressed_ratio, 4)
        }

    # ------------------------------------------------------------------

    def get_pdf_info(self, pdf_path: str) -> dict:
        try:
            import fitz
            doc = fitz.open(pdf_path)
            info = {
                "file_size": os.path.getsize(pdf_path),
                "page_count": len(doc),
            }
            doc.close()
            return info
        except Exception as e:
            print(f"Error reading PDF info: {e}")
            raise