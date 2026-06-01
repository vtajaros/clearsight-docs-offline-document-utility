"""
Option A — Path-bypass branch tests for ClearSight Docs API.

Covers the `file_path` / `files_path` form fields added in Task 2.
Every endpoint that received a bypass branch has at least:
  - happy path  (valid path → correct response)
  - missing file (non-existent path → 400)
  - wrong extension (non-PDF / non-image → 400 / 422)

Run from the backend/ directory:
    pytest tests/test_api_path_bypass.py -v
"""

import io
import json
import shutil
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

poppler_available = shutil.which("pdftoppm") is not None


# ---------------------------------------------------------------------------
# Helpers — reuse the same minimal fixture builders as test_api.py
# ---------------------------------------------------------------------------

def _make_pdf(tmp_path: Path, name: str = "test.pdf", pages: int = 3) -> Path:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import letter

    pdf_path = tmp_path / name
    c = rl_canvas.Canvas(str(pdf_path), pagesize=letter)
    for i in range(pages):
        c.drawString(72, 720, f"ClearSight bypass test page {i + 1}")
        c.showPage()
    c.save()
    return pdf_path


def _make_image(tmp_path: Path, name: str = "test.png", fmt: str = "PNG") -> Path:
    from PIL import Image

    p = tmp_path / name
    Image.new("RGB", (100, 100), color="red").save(p, format=fmt)
    return p


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    import api as api_module
    with TestClient(api_module.app, headers={"Authorization": f"Bearer {api_module.API_TOKEN}"}) as c:
        yield c


@pytest.fixture()
def pdf(tmp_path):
    return _make_pdf(tmp_path, pages=3)


@pytest.fixture()
def two_pdfs(tmp_path):
    return _make_pdf(tmp_path, "a.pdf", pages=2), _make_pdf(tmp_path, "b.pdf", pages=2)


@pytest.fixture()
def png(tmp_path):
    return _make_image(tmp_path, "img.png", "PNG")


@pytest.fixture()
def two_images(tmp_path):
    return (
        _make_image(tmp_path, "img1.png", "PNG"),
        _make_image(tmp_path, "img2.jpg", "JPEG"),
    )


# ---------------------------------------------------------------------------
# OCR — file_path bypass
# ---------------------------------------------------------------------------

class TestOcrPathBypass:
    def test_txt_output_via_path(self, client, pdf):
        """Happy path: local PDF path → text output."""
        r = client.post(
            "/api/ocr",
            data={"file_path": str(pdf), "output_format": "txt", "language": "eng"},
        )
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/plain")
        assert b"ClearSight" in r.content

    def test_pdf_output_via_path(self, client, pdf):
        """Happy path: local PDF path → searchable PDF output."""
        r = client.post(
            "/api/ocr",
            data={"file_path": str(pdf), "output_format": "pdf", "language": "eng"},
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:4] == b"%PDF"

    def test_missing_file_returns_400(self, client, tmp_path):
        """Non-existent path → 400."""
        r = client.post(
            "/api/ocr",
            data={"file_path": str(tmp_path / "ghost.pdf"), "output_format": "txt"},
        )
        assert r.status_code == 400
        assert "not found" in r.json()["detail"].lower()

    def test_non_pdf_path_returns_400(self, client, tmp_path):
        """Path pointing at a .txt file → 400."""
        txt = tmp_path / "doc.txt"
        txt.write_text("not a pdf")
        r = client.post(
            "/api/ocr",
            data={"file_path": str(txt), "output_format": "txt"},
        )
        assert r.status_code == 400

    def test_neither_file_nor_path_returns_400(self, client):
        """Supplying nothing → 400."""
        r = client.post("/api/ocr", data={"output_format": "txt"})
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Merge — files_path bypass
# ---------------------------------------------------------------------------

class TestMergePathBypass:
    def test_merge_two_pdfs_via_path(self, client, two_pdfs):
        """Happy path: two local paths → merged 4-page PDF."""
        a, b = two_pdfs
        r = client.post(
            "/api/merge",
            data={"files_path": [str(a), str(b)]},
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"

        from pypdf import PdfReader
        assert len(PdfReader(io.BytesIO(r.content)).pages) == 4

    def test_merge_single_path_returns_400(self, client, pdf):
        """Only one path → 400 (need at least 2)."""
        r = client.post(
            "/api/merge",
            data={"files_path": [str(pdf)]},
        )
        assert r.status_code == 400

    def test_merge_missing_path_returns_400(self, client, tmp_path, pdf):
        """One valid + one missing → 400."""
        r = client.post(
            "/api/merge",
            data={"files_path": [str(pdf), str(tmp_path / "ghost.pdf")]},
        )
        assert r.status_code == 400

    def test_merge_non_pdf_path_returns_400(self, client, pdf, tmp_path):
        """One PDF + one .txt → 400."""
        txt = tmp_path / "note.txt"
        txt.write_text("hello")
        r = client.post(
            "/api/merge",
            data={"files_path": [str(pdf), str(txt)]},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Split/range — file_path bypass
# ---------------------------------------------------------------------------

class TestSplitRangePathBypass:
    def test_split_range_via_path(self, client, pdf):
        """Happy path: pages 1-2 of a 3-page PDF."""
        r = client.post(
            "/api/split/range",
            data={"file_path": str(pdf), "start_page": 1, "end_page": 2},
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"

        from pypdf import PdfReader
        assert len(PdfReader(io.BytesIO(r.content)).pages) == 2

    def test_invalid_range_via_path_returns_400(self, client, pdf):
        """end < start → 400 regardless of path vs upload."""
        r = client.post(
            "/api/split/range",
            data={"file_path": str(pdf), "start_page": 3, "end_page": 1},
        )
        assert r.status_code == 400

    def test_missing_file_returns_400(self, client, tmp_path):
        r = client.post(
            "/api/split/range",
            data={"file_path": str(tmp_path / "ghost.pdf"), "start_page": 1, "end_page": 2},
        )
        assert r.status_code == 400

    def test_non_pdf_path_returns_400(self, client, tmp_path):
        txt = tmp_path / "note.txt"
        txt.write_text("hello")
        r = client.post(
            "/api/split/range",
            data={"file_path": str(txt), "start_page": 1, "end_page": 1},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Split/pages — file_path bypass
# ---------------------------------------------------------------------------

class TestSplitPagesPathBypass:
    def test_split_pages_via_path(self, client, pdf):
        """Happy path: 3-page PDF → ZIP with 3 single-page PDFs."""
        r = client.post(
            "/api/split/pages",
            data={"file_path": str(pdf)},
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/zip"

        names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
        assert len(names) == 3
        assert all(n.endswith(".pdf") for n in names)

    def test_missing_file_returns_400(self, client, tmp_path):
        r = client.post(
            "/api/split/pages",
            data={"file_path": str(tmp_path / "ghost.pdf")},
        )
        assert r.status_code == 400

    def test_non_pdf_path_returns_400(self, client, tmp_path):
        txt = tmp_path / "note.txt"
        txt.write_text("hello")
        r = client.post(
            "/api/split/pages",
            data={"file_path": str(txt)},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Compress — file_path bypass
# ---------------------------------------------------------------------------

class TestCompressPathBypass:
    def test_compress_via_path(self, client, pdf):
        """Happy path: compress and get stats header."""
        r = client.post(
            "/api/compress",
            data={"file_path": str(pdf), "compression_level": "medium"},
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert "x-compression-stats" in r.headers

        stats = json.loads(r.headers["x-compression-stats"])
        assert {"original_size", "new_size", "reduction_percentage"} <= stats.keys()

    def test_all_compression_levels_via_path(self, client, pdf):
        """Low, medium, high all succeed."""
        for level in ("low", "medium", "high"):
            r = client.post(
                "/api/compress",
                data={"file_path": str(pdf), "compression_level": level},
            )
            assert r.status_code == 200, f"Failed for level={level}"

    def test_invalid_level_via_path_returns_400(self, client, pdf):
        r = client.post(
            "/api/compress",
            data={"file_path": str(pdf), "compression_level": "extreme"},
        )
        assert r.status_code == 400

    def test_missing_file_returns_400(self, client, tmp_path):
        r = client.post(
            "/api/compress",
            data={"file_path": str(tmp_path / "ghost.pdf"), "compression_level": "medium"},
        )
        assert r.status_code == 400

    def test_non_pdf_path_returns_400(self, client, tmp_path):
        txt = tmp_path / "note.txt"
        txt.write_text("hello")
        r = client.post(
            "/api/compress",
            data={"file_path": str(txt), "compression_level": "medium"},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# PDF to Images — file_path bypass
# ---------------------------------------------------------------------------

class TestPdfToImagesPathBypass:
    @pytest.mark.skipif(not poppler_available, reason="Poppler not installed")
    def test_png_via_path(self, client, pdf):
        """Happy path: PDF path → ZIP of PNGs."""
        r = client.post(
            "/api/pdf-to-images",
            data={"file_path": str(pdf), "image_format": "PNG", "dpi": 72},
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/zip"

        names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
        assert len(names) == 3
        assert all(n.endswith(".png") for n in names)

    @pytest.mark.skipif(not poppler_available, reason="Poppler not installed")
    def test_jpg_via_path(self, client, pdf):
        r = client.post(
            "/api/pdf-to-images",
            data={"file_path": str(pdf), "image_format": "JPG", "dpi": 72},
        )
        assert r.status_code == 200
        names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
        assert all(n.endswith(".jpg") for n in names)

    def test_invalid_format_via_path_returns_400(self, client, pdf):
        r = client.post(
            "/api/pdf-to-images",
            data={"file_path": str(pdf), "image_format": "BMP"},
        )
        assert r.status_code == 400

    def test_missing_file_returns_400(self, client, tmp_path):
        r = client.post(
            "/api/pdf-to-images",
            data={"file_path": str(tmp_path / "ghost.pdf"), "image_format": "PNG"},
        )
        assert r.status_code == 400

    def test_non_pdf_path_returns_400(self, client, tmp_path):
        txt = tmp_path / "note.txt"
        txt.write_text("hello")
        r = client.post(
            "/api/pdf-to-images",
            data={"file_path": str(txt), "image_format": "PNG"},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Image to PDF — files_path bypass
# ---------------------------------------------------------------------------

class TestImageToPdfPathBypass:
    def test_two_images_via_path(self, client, two_images):
        """Happy path: two image paths → 2-page PDF."""
        img1, img2 = two_images
        r = client.post(
            "/api/image-to-pdf",
            data={
                "files_path": [str(img1), str(img2)],
                "page_size": "A4",
                "orientation": "Portrait",
                "margin": "Small",
            },
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"

        from pypdf import PdfReader
        assert len(PdfReader(io.BytesIO(r.content)).pages) == 2

    def test_single_image_via_path(self, client, png):
        """Single image path → 1-page PDF."""
        r = client.post(
            "/api/image-to-pdf",
            data={"files_path": [str(png)], "page_size": "Letter"},
        )
        assert r.status_code == 200

        from pypdf import PdfReader
        assert len(PdfReader(io.BytesIO(r.content)).pages) == 1

    def test_missing_image_returns_400(self, client, tmp_path):
        r = client.post(
            "/api/image-to-pdf",
            data={"files_path": [str(tmp_path / "ghost.png")]},
        )
        assert r.status_code == 400

    def test_non_image_path_returns_422(self, client, tmp_path):
        """A .txt file in the image list → 422."""
        txt = tmp_path / "doc.txt"
        txt.write_text("hello")
        r = client.post(
            "/api/image-to-pdf",
            data={"files_path": [str(txt)]},
        )
        assert r.status_code == 422

    def test_pdf_as_image_path_returns_422(self, client, pdf):
        """Passing a .pdf where images are expected → 422."""
        r = client.post(
            "/api/image-to-pdf",
            data={"files_path": [str(pdf)]},
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Delete Pages — file_path bypass
# ---------------------------------------------------------------------------

class TestDeletePagesPathBypass:
    def test_delete_pages_via_path(self, client, pdf):
        """Happy path: 3-page PDF -> delete page 1 (0-indexed 1) -> 2 pages."""
        r = client.post(
            "/api/delete-pages",
            data={"file_path": str(pdf), "pages_to_delete": "[1]"},
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"

        from pypdf import PdfReader
        assert len(PdfReader(io.BytesIO(r.content)).pages) == 2

    def test_invalid_pages_format_returns_400(self, client, pdf):
        r = client.post(
            "/api/delete-pages",
            data={"file_path": str(pdf), "pages_to_delete": "not_json"},
        )
        assert r.status_code == 400

    def test_missing_file_returns_400(self, client, tmp_path):
        r = client.post(
            "/api/delete-pages",
            data={"file_path": str(tmp_path / "ghost.pdf")},
        )
        assert r.status_code == 400

    def test_non_pdf_path_returns_400(self, client, tmp_path):
        txt = tmp_path / "note.txt"
        txt.write_text("hello")
        r = client.post(
            "/api/delete-pages",
            data={"file_path": str(txt)},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Path Traversal Prevention
# ---------------------------------------------------------------------------

class TestPathTraversalPrevention:
    def test_single_input_traversal_returns_400(self, client):
        r = client.post(
            "/api/ocr",
            data={"file_path": "/etc/passwd/../../secret.pdf"},
        )
        assert r.status_code == 400
        assert "traversal" in r.json()["detail"].lower()

    def test_multiple_inputs_traversal_returns_400(self, client, pdf):
        r = client.post(
            "/api/merge",
            data={"files_path": [str(pdf), "../../etc/passwd/secret.pdf"]},
        )
        assert r.status_code == 400
        assert "traversal" in r.json()["detail"].lower()
