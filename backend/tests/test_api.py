"""
Tests for ClearSight Docs API endpoints.
Run with: pytest tests/test_api.py -v

Requires a minimal real PDF on disk. Tests use pytest's tmp_path fixture
so no manual cleanup is needed.
"""
import io
import json
import zipfile
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

poppler_available = shutil.which("pdftoppm") is not None

# ---------------------------------------------------------------------------
# Minimal valid 1-page PDF (no external files needed)
# Generated via pypdf so it matches the exact library used by the services.
# ---------------------------------------------------------------------------

def _make_pdf(tmp_path: Path, name: str = "test.pdf", pages: int = 3) -> Path:
    """Create a minimal multi-page PDF with selectable text."""
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import letter

    pdf_path = tmp_path / name
    c = rl_canvas.Canvas(str(pdf_path), pagesize=letter)
    for i in range(pages):
        c.drawString(72, 720, f"ClearSight test page {i + 1}")
        c.showPage()
    c.save()
    return pdf_path


def _make_image(tmp_path: Path, name: str = "test.png", format: str = "PNG") -> Path:
    """Create a simple test image."""
    from PIL import Image
    image_path = tmp_path / name
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(image_path, format=format)
    return image_path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    import api as api_module
    with TestClient(api_module.app, headers={"Authorization": f"Bearer {api_module.API_TOKEN}"}) as c:
        yield c


@pytest.fixture()
def sample_pdf(tmp_path):
    return _make_pdf(tmp_path, pages=3)


@pytest.fixture()
def two_pdfs(tmp_path):
    a = _make_pdf(tmp_path, "a.pdf", pages=2)
    b = _make_pdf(tmp_path, "b.pdf", pages=2)
    return a, b


@pytest.fixture()
def sample_image(tmp_path):
    return _make_image(tmp_path, "test.png", "PNG")


@pytest.fixture()
def two_images(tmp_path):
    img1 = _make_image(tmp_path, "img1.png", "PNG")
    img2 = _make_image(tmp_path, "img2.jpg", "JPEG")
    return img1, img2


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "tesseract" in body


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

def test_ocr_text_output(client, sample_pdf):
    """PDF with existing text should return a .txt file."""
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/ocr",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"output_format": "txt", "language": "eng"},
        )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    assert b"ClearSight" in r.content


def test_ocr_rejects_non_pdf(client):
    r = client.post(
        "/api/ocr",
        files={"file": ("test.txt", b"hello", "text/plain")},
        data={"output_format": "txt"},
    )
    assert r.status_code == 400


def test_ocr_searchable_pdf_output(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/ocr",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"output_format": "pdf"},
        )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

def test_merge_two_pdfs(client, two_pdfs):
    a, b = two_pdfs
    with open(a, "rb") as fa, open(b, "rb") as fb:
        r = client.post(
            "/api/merge",
            files=[
                ("files", ("a.pdf", fa, "application/pdf")),
                ("files", ("b.pdf", fb, "application/pdf")),
            ],
        )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"

    # Merged PDF should have 4 pages (2 + 2)
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(r.content))
    assert len(reader.pages) == 4


def test_merge_rejects_single_file(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/merge",
            files=[("files", ("test.pdf", f, "application/pdf"))],
        )
    assert r.status_code == 400


def test_merge_rejects_non_pdf(client, sample_pdf, tmp_path):
    txt = tmp_path / "note.txt"
    txt.write_text("not a pdf")
    with open(sample_pdf, "rb") as f, open(txt, "rb") as t:
        r = client.post(
            "/api/merge",
            files=[
                ("files", ("a.pdf", f, "application/pdf")),
                ("files", ("note.txt", t, "text/plain")),
            ],
        )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Split — range
# ---------------------------------------------------------------------------

def test_split_range(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/split/range",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"start_page": 1, "end_page": 2},
        )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"

    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(r.content))
    assert len(reader.pages) == 2


def test_split_range_invalid(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/split/range",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"start_page": 3, "end_page": 1},
        )
    assert r.status_code == 400


def test_split_range_out_of_bounds(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/split/range",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"start_page": 1, "end_page": 99},
        )
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# Split — individual pages
# ---------------------------------------------------------------------------

def test_split_into_pages(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/split/pages",
            files={"file": ("test.pdf", f, "application/pdf")},
        )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"

    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert len(names) == 3  # 3-page PDF → 3 files
    assert all(n.endswith(".pdf") for n in names)


# ---------------------------------------------------------------------------
# PDF Compress
# ---------------------------------------------------------------------------

def test_compress_pdf(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/compress",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"compression_level": "medium"},
        )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert "x-compression-stats" in r.headers
    
    stats = json.loads(r.headers["x-compression-stats"])
    assert "original_size" in stats
    assert "new_size" in stats
    assert "reduction_percentage" in stats


def test_compress_rejects_non_pdf(client, tmp_path):
    txt = tmp_path / "test.txt"
    txt.write_text("hello")
    with open(txt, "rb") as f:
        r = client.post(
            "/api/compress",
            files={"file": ("test.txt", f, "text/plain")},
            data={"compression_level": "medium"},
        )
    assert r.status_code == 400


def test_compress_rejects_invalid_level(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/compress",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"compression_level": "ultra-high"},
        )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# PDF to Images
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not poppler_available, reason="Poppler not installed")
def test_pdf_to_images(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/pdf-to-images",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"image_format": "PNG", "dpi": 150},
        )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert len(names) == 3
    assert all(n.endswith(".png") for n in names)


@pytest.mark.skipif(not poppler_available, reason="Poppler not installed")
def test_pdf_to_images_jpg(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/pdf-to-images",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"image_format": "JPG", "dpi": 150},
        )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert len(names) == 3
    assert all(n.endswith(".jpg") for n in names)


def test_pdf_to_images_rejects_invalid_format(client, sample_pdf):
    with open(sample_pdf, "rb") as f:
        r = client.post(
            "/api/pdf-to-images",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"image_format": "BMP"},
        )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Image to PDF
# ---------------------------------------------------------------------------

def test_image_to_pdf(client, two_images):
    img1, img2 = two_images
    with open(img1, "rb") as f1, open(img2, "rb") as f2:
        r = client.post(
            "/api/image-to-pdf",
            files=[
                ("files", ("img1.png", f1, "image/png")),
                ("files", ("img2.jpg", f2, "image/jpeg")),
            ],
            data={"page_size": "A4", "orientation": "Portrait", "margin": "Small"},
        )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(r.content))
    assert len(reader.pages) == 2


def test_image_to_pdf_rejects_unsupported_format(client, tmp_path):
    txt = tmp_path / "test.txt"
    txt.write_text("hello")
    with open(txt, "rb") as f:
        r = client.post(
            "/api/image-to-pdf",
            files=[("files", ("test.txt", f, "text/plain"))],
        )
    assert r.status_code == 422
