"""
ClearSight Docs — Local API Server
Wraps backend services in a FastAPI application.
Run with: uvicorn api:app --reload --port 8000

Request lifecycle:
  HTTP request
    → resolve_single_input / resolve_multiple_inputs  (validate, save to tmp dir)
    → service call  (raises on failure)
    → CleanupFileResponse  (streams file, deletes tmp dir in __call__ finally)
"""
import os
import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import shutil
import tempfile
import json
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from services.ocr_service import OCRService, OCRSettings, OutputFormat, AccuracyMode
from services.pdf_merge_service import PdfMergeService
from services.pdf_split_service import PdfSplitService
from services.pdf_compress_service import PdfCompressService
from services.pdf_to_images_service import PdfToImagesService
from services.image_to_pdf_service import ImageToPdfService
from services.pdf_delete_service import PdfDeleteService
from routers.bookmarks import router as bookmarks_router

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="ClearSight Docs API", version="2.0.0")
app.include_router(bookmarks_router, prefix="/bookmarks", tags=["bookmarks"])

import secrets
API_TOKEN = os.environ.get("CLEARSIGHT_API_TOKEN")
if not API_TOKEN:
    API_TOKEN = secrets.token_hex(32)
    print(f"WARN: CLEARSIGHT_API_TOKEN not set in environment. Using generated dev token: {API_TOKEN}")

async def verify_token(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token.")
    token = authorization.split(" ")[1]
    if not secrets.compare_digest(token, API_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid token.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_ocr           = OCRService()
_merge         = PdfMergeService()
_split         = PdfSplitService()
_compress      = PdfCompressService()
_pdf_to_images = PdfToImagesService()
_image_to_pdf  = ImageToPdfService()
_delete_pages  = PdfDeleteService()

_executor = ThreadPoolExecutor(max_workers=4)


class CleanupFileResponse(FileResponse):
    """
    FileResponse that deletes a temporary directory after streaming.
    The cleanup runs in the finally block of __call__ regardless of
    whether the client disconnects cleanly.
    """
    def __init__(self, *args, temp_dir: Path, **kwargs):
        super().__init__(*args, **kwargs)
        self.temp_dir = temp_dir

    async def __call__(self, scope, receive, send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            _cleanup_dir(self.temp_dir)


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, job_id: str, ws: WebSocket):
        await ws.accept()
        self.active[job_id] = ws

    def disconnect(self, job_id: str):
        self.active.pop(job_id, None)

    def is_connected(self, job_id: str) -> bool:
        return job_id in self.active

    async def send(self, job_id: str, data: dict) -> bool:
        ws = self.active.get(job_id)
        if ws is None:
            return False
        try:
            await ws.send_json(data)
            return True
        except Exception:
            self.disconnect(job_id)
            return False


_ws_manager = ConnectionManager()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_upload(upload: UploadFile, dest: Path) -> None:
    """Write an UploadFile to disk."""
    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)


def _temp_dir() -> Path:
    """Create and return a fresh temporary directory."""
    return Path(tempfile.mkdtemp(prefix="clearsight_"))


def _cleanup_dir(path: Path) -> None:
    """Remove a temporary directory, ignoring errors."""
    try:
        if path.exists():
            shutil.rmtree(path)
    except Exception as e:
        print(f"Failed to clean up temp directory {path}: {e}")


@contextmanager
def _managed_tmp(tmp: Path):
    """
    Context manager that cleans up a temp directory on any exception,
    re-raising HTTPExceptions as-is and wrapping all others as HTTP 500.
    Usage:
        with _managed_tmp(tmp):
            ... service calls ...
    """
    try:
        yield
    except Exception as e:
        _cleanup_dir(tmp)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))


def _validate_local_path(raw: str) -> Path:
    """
    Reject directory traversal attempts and resolve the path strictly.
    Returns the resolved Path on success, raises HTTPException on failure.
    """
    path_obj = Path(raw)
    if ".." in path_obj.parts or ".." in raw or "/../" in raw or "\\..\\" in raw:
        raise HTTPException(status_code=400, detail="Directory traversal not allowed.")
    try:
        resolved = path_obj.resolve(strict=True)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Local file not found: {raw}")
    if not resolved.is_file():
        raise HTTPException(status_code=400, detail=f"Local file not found: {raw}")
    return resolved


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

async def resolve_single_input(
    file: UploadFile | None = File(None),
    file_path: str | None = Form(None),
) -> tuple[Path, Path]:
    if not file and not file_path:
        raise HTTPException(status_code=400, detail="Either file upload or local file_path is required.")

    tmp = _temp_dir()
    try:
        if file_path:
            yield _validate_local_path(file_path), tmp
        else:
            if not file.filename:
                raise HTTPException(status_code=400, detail="Empty filename uploaded.")
            input_path = tmp / Path(file.filename).name
            _save_upload(file, input_path)
            yield input_path, tmp
    except Exception:
        _cleanup_dir(tmp)
        raise


async def resolve_multiple_inputs(
    files: list[UploadFile] | None = File(None),
    files_path: list[str] | None = Form(None),
) -> tuple[list[Path], Path]:
    if files_path is None:
        files_path = []
    if files is None:
        files = []

    resolved_files_path = []
    for fp in files_path:
        if not fp:
            continue
        try:
            decoded = json.loads(fp)
            if isinstance(decoded, list):
                resolved_files_path.extend([str(x) for x in decoded])
            else:
                resolved_files_path.append(str(decoded))
        except Exception:
            if "," in fp:
                resolved_files_path.extend([p.strip() for p in fp.split(",")])
            else:
                resolved_files_path.append(fp)

    if not files and not resolved_files_path:
        raise HTTPException(status_code=400, detail="Either files or files_path is required.")

    tmp = _temp_dir()
    try:
        input_paths = []
        if resolved_files_path:
            for p in resolved_files_path:
                input_paths.append(_validate_local_path(p))
        else:
            for i, upload in enumerate(files):
                if not upload.filename:
                    raise HTTPException(status_code=400, detail="Empty filename uploaded.")
                ext = Path(upload.filename).suffix
                dest = tmp / f"input_{i:03d}{ext}"
                _save_upload(upload, dest)
                input_paths.append(dest)

        yield input_paths, tmp
    except Exception:
        _cleanup_dir(tmp)
        raise


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "tesseract": _ocr.is_tesseract_available()}


# ---------------------------------------------------------------------------
# OCR  —  POST /api/ocr
# ---------------------------------------------------------------------------

@app.websocket("/ws/ocr/{job_id}")
async def ocr_websocket(websocket: WebSocket, job_id: str):
    await _ws_manager.connect(job_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        _ws_manager.disconnect(job_id)


@app.post("/api/ocr")
async def ocr_pdf(
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
    language: Annotated[str,  Form()] = "eng",
    output_format: Annotated[str,  Form()] = "txt",
    accuracy_mode: Annotated[str,  Form()] = "balanced",
    dpi:           Annotated[int,  Form()] = 300,
    force_ocr:     Annotated[bool, Form()] = False,
    include_page_separators: Annotated[bool, Form()] = False,
    job_id: Annotated[str, Form()] = "",
    _=Depends(verify_token),
):
    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    with _managed_tmp(tmp):
        output_ext  = "txt" if output_format == "txt" else "pdf"
        output_path = tmp / f"output.{output_ext}"

        settings = OCRSettings(
            language=language,
            output_format=OutputFormat.TEXT if output_format == "txt" else OutputFormat.SEARCHABLE_PDF,
            dpi=dpi,
            accuracy_mode=AccuracyMode(accuracy_mode),
            force_ocr=force_ocr,
            include_page_separators=include_page_separators,
        )

        loop = asyncio.get_running_loop()

        async def broadcast(current: int, total: int, message: str):
            await _ws_manager.send(job_id, {
                "current": current,
                "total": total,
                "message": message
            })

        def sync_callback(current: int, total: int, message: str):
            if not job_id:
                return
            if not _ws_manager.is_connected(job_id):
                return
            try:
                future = asyncio.run_coroutine_threadsafe(
                    broadcast(current, total, message), loop
                )
                future.result(timeout=1)
            except Exception:
                pass

        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    _executor,
                    lambda: _ocr.process_pdf(str(input_path), str(output_path), settings, sync_callback)
                ),
                timeout=300  # 5 minutes max per OCR job
            )
        except asyncio.TimeoutError:
            # The underlying thread cannot be forcefully killed (Python limitation),
            # but the asyncio timeout prevents new requests from waiting forever
            # and caps queue starvation to max_workers * timeout seconds
            raise HTTPException(status_code=504, detail="OCR processing timed out. The document may be too large or complex.")

        if job_id:
            await _ws_manager.send(job_id, {"current": -1, "total": -1, "message": "done"})
            _ws_manager.disconnect(job_id)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message)

        media = "text/plain" if output_format == "txt" else "application/pdf"
        return CleanupFileResponse(
            path=str(output_path),
            media_type=media,
            filename=f"{stem}_ocr.{output_ext}",
            temp_dir=tmp,
        )


# ---------------------------------------------------------------------------
# Merge  —  POST /api/merge
# ---------------------------------------------------------------------------

@app.post("/api/merge")
async def merge_pdfs(
    input_data: Annotated[tuple[list[Path], Path], Depends(resolve_multiple_inputs)],
    _=Depends(verify_token),
):
    input_paths, tmp = input_data

    for path_obj in input_paths:
        if not path_obj.name.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"'{path_obj.name}' is not a PDF.")

    if len(input_paths) < 2:
        raise HTTPException(status_code=400, detail="At least two PDF files are required.")

    with _managed_tmp(tmp):
        output_path = str(tmp / "merged.pdf")
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    _executor,
                    lambda: _merge.merge_pdfs([str(p) for p in input_paths], output_path)
                ),
                timeout=120
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Merge processing timed out.")

        return CleanupFileResponse(
            path=output_path,
            media_type="application/pdf",
            filename="merged.pdf",
            temp_dir=tmp,
        )


# ---------------------------------------------------------------------------
# Split by range  —  POST /api/split/range
# ---------------------------------------------------------------------------

@app.post("/api/split/range")
async def split_by_range(
    start_page: Annotated[int, Form(ge=1)],
    end_page:   Annotated[int, Form(ge=1)],
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
    _=Depends(verify_token),
):
    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    if end_page < start_page:
        raise HTTPException(status_code=400, detail="end_page must be >= start_page.")

    with _managed_tmp(tmp):
        output_path = tmp / "split.pdf"
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    _executor,
                    lambda: _split.split_by_range(str(input_path), str(output_path), start_page, end_page)
                ),
                timeout=120
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Split processing timed out.")

        return CleanupFileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=f"{stem}_p{start_page}-{end_page}.pdf",
            temp_dir=tmp,
        )


# ---------------------------------------------------------------------------
# Split into individual pages  —  POST /api/split/pages
# ---------------------------------------------------------------------------

@app.post("/api/split/pages")
async def split_into_pages(
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
    _=Depends(verify_token),
):
    """Split a PDF into individual single-page PDFs returned as a zip archive."""
    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    with _managed_tmp(tmp):
        pages_dir = tmp / "pages"
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    _executor,
                    lambda: _split.split_into_pages(str(input_path), str(pages_dir))
                ),
                timeout=120
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Split processing timed out.")

        zip_path = tmp / f"{stem}_pages.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for page_file in sorted(pages_dir.iterdir()):
                zf.write(page_file, page_file.name)

        return CleanupFileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename=f"{stem}_pages.zip",
            temp_dir=tmp,
        )


# ---------------------------------------------------------------------------
# Compress  —  POST /api/compress
# ---------------------------------------------------------------------------

@app.get("/api/compress/diagnose")
async def diagnose_pdf_endpoint(
    file_path: str,
    _=Depends(verify_token),
):
    input_path = _validate_local_path(file_path)
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, lambda: _compress.diagnose_pdf(str(input_path))),
            timeout=120
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Diagnose processing timed out.")
    return result

@app.post("/api/compress")
async def compress_pdf_endpoint(
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
    compression_level: Annotated[str, Form()] = "medium",
    _=Depends(verify_token),
):
    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    if compression_level not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="compression_level must be 'low', 'medium', or 'high'.")

    with _managed_tmp(tmp):
        output_path = tmp / "compressed.pdf"
        loop = asyncio.get_running_loop()
        # Scale timeout by file size and compression level.
        # Image recompression on large PDFs is CPU-bound and can take
        # several minutes. Low mode is fast; medium/high need more headroom.
        file_size_mb = input_path.stat().st_size / (1024 * 1024)
        if compression_level == "low":
            compress_timeout = max(60, file_size_mb * 0.5)
        else:
            compress_timeout = max(120, file_size_mb * 3)

        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    _executor,
                    lambda: _compress.compress_pdf(str(input_path), str(output_path), compression_level)
                ),
                timeout=compress_timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=f"Compress processing timed out after {compress_timeout:.0f}s. Try 'Low' compression for very large files."
            )

        stats = {
            "original_size": result["original_size"],
            "new_size": result["new_size"],
            "reduction_percentage": result["reduction_percentage"]
        }
        headers = {
            "X-Compression-Stats": json.dumps(stats),
            "Access-Control-Expose-Headers": "X-Compression-Stats"
        }

        return CleanupFileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=f"{stem}_compressed.pdf",
            headers=headers,
            temp_dir=tmp,
        )


# ---------------------------------------------------------------------------
# PDF to Images  —  POST /api/pdf-to-images
# ---------------------------------------------------------------------------

@app.post("/api/pdf-to-images")
async def pdf_to_images_endpoint(
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
    image_format: Annotated[str, Form()] = "PNG",
    dpi: Annotated[int, Form()] = 150,
    _=Depends(verify_token),
):
    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    if image_format.upper() not in ["PNG", "JPG"]:
        raise HTTPException(status_code=400, detail="image_format must be 'PNG' or 'JPG'.")

    with _managed_tmp(tmp):
        output_zip_path = tmp / f"{stem}_images.zip"
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    _executor,
                    lambda: _pdf_to_images.convert_pdf_to_images_zip(
                        str(input_path), str(output_zip_path), image_format.upper(), dpi
                    )
                ),
                timeout=120
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="PDF to Images processing timed out.")

        return CleanupFileResponse(
            path=str(output_zip_path),
            media_type="application/zip",
            filename=f"{stem}_images.zip",
            temp_dir=tmp,
        )


# ---------------------------------------------------------------------------
# Image to PDF  —  POST /api/image-to-pdf
# ---------------------------------------------------------------------------

@app.post("/api/image-to-pdf")
async def image_to_pdf_endpoint(
    input_data: Annotated[tuple[list[Path], Path], Depends(resolve_multiple_inputs)],
    page_size: Annotated[str, Form()] = "A4",
    orientation: Annotated[str, Form()] = "Portrait",
    margin: Annotated[str, Form()] = "Small",
    _=Depends(verify_token),
):
    input_paths, tmp = input_data

    for path_obj in input_paths:
        if path_obj.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            raise HTTPException(status_code=422, detail="Only JPG, JPEG, and PNG images are supported.")

    with _managed_tmp(tmp):
        output_path = tmp / "output.pdf"
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    _executor,
                    lambda: _image_to_pdf.convert_images_to_pdf(
                        [str(p) for p in input_paths], str(output_path), page_size, orientation, margin
                    )
                ),
                timeout=120
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Image to PDF processing timed out.")

        return CleanupFileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="images_combined.pdf",
            temp_dir=tmp,
        )


# ---------------------------------------------------------------------------
# Delete Pages  —  POST /api/delete-pages
# ---------------------------------------------------------------------------

@app.post("/api/delete-pages")
async def delete_pdf_pages(
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
    pages_to_delete: Annotated[str, Form()] = "[]",
    _=Depends(verify_token),
):
    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    try:
        pages_list = json.loads(pages_to_delete)
        if not isinstance(pages_list, list) or not all(isinstance(x, int) for x in pages_list):
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=400, detail="pages_to_delete must be a JSON array of integers.")

    with _managed_tmp(tmp):
        output_path = tmp / "deleted.pdf"
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    _executor,
                    lambda: _delete_pages.delete_pages(str(input_path), str(output_path), pages_list)
                ),
                timeout=120
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Delete processing timed out.")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return CleanupFileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=f"{stem}_deleted.pdf",
            temp_dir=tmp,
        )