"""
ClearSight Docs — Local API Server
Wraps backend services in a FastAPI application.
Run with: uvicorn api:app --reload --port 8000
"""
import os
import shutil
import tempfile
import json
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
import asyncio
import uuid
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

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="ClearSight Docs API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
    Custom FileResponse that cleans up a temporary directory
    after the response has been fully streamed to the client.
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
        """Return True only if a live socket is registered for this job."""
        return job_id in self.active

    async def send(self, job_id: str, data: dict) -> bool:
        """
        Send a JSON message to the registered socket.

        Returns True on success, False if the socket is gone.
        Disconnects silently on any send error so callers don't
        need to handle exceptions.
        """
        ws = self.active.get(job_id)
        if ws is None:
            return False
        try:
            await ws.send_json(data)
            return True
        except Exception:
            # Socket is broken — clean up so we stop trying
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
    """Clean up temporary directory."""
    try:
        if path.exists():
            shutil.rmtree(path)
    except Exception as e:
        print(f"Failed to clean up temp directory {path}: {e}")


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
            path_obj = Path(file_path)
            # Prevent directory traversal
            if ".." in path_obj.parts or ".." in file_path or "/../" in file_path or "\\..\\" in file_path:
                raise HTTPException(status_code=400, detail="Directory traversal not allowed.")
            
            try:
                resolved_path = path_obj.resolve(strict=True)
            except Exception:
                raise HTTPException(status_code=400, detail=f"Local file not found: {file_path}")
            
            if not resolved_path.is_file():
                raise HTTPException(status_code=400, detail=f"Local file not found: {file_path}")
            
            yield resolved_path, tmp
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
                path_obj = Path(p)
                if ".." in path_obj.parts or ".." in p or "/../" in p or "\\..\\" in p:
                    raise HTTPException(status_code=400, detail="Directory traversal not allowed.")
                
                try:
                    resolved_path = path_obj.resolve(strict=True)
                except Exception:
                    raise HTTPException(status_code=400, detail=f"Local file not found: {p}")
                
                if not resolved_path.is_file():
                    raise HTTPException(status_code=400, detail=f"Local file not found: {p}")
                
                input_paths.append(resolved_path)
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
        # Keep the socket alive.  When the client disconnects
        # (navigation, tab close, panel reset) WebSocketDisconnect
        # is raised here, which causes the finally block to run.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass  # Expected — client left
    except Exception:
        pass  # Any other transport error
    finally:
        # Always clean up so sync_callback stops broadcasting
        _ws_manager.disconnect(job_id)

@app.post("/api/ocr")
async def ocr_pdf(
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
    language: Annotated[str,  Form()] = "eng",
    output_format: Annotated[str,  Form()] = "txt",   # "txt" | "pdf"
    accuracy_mode: Annotated[str,  Form()] = "balanced",  # "fast" | "balanced" | "accurate"
    dpi:           Annotated[int,  Form()] = 300,
    force_ocr:     Annotated[bool, Form()] = False,
    include_page_separators: Annotated[bool, Form()] = False,
    job_id: Annotated[str, Form()] = "",
):
    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    try:
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

        loop = asyncio.get_event_loop()

        async def broadcast(current: int, total: int, message: str):
            await _ws_manager.send(job_id, {
                "current": current,
                "total": total,
                "message": message
            })

        def sync_callback(current: int, total: int, message: str):
            if not job_id:
                return
            # Skip immediately if the socket is already gone —
            # avoids scheduling a coroutine that will fail and
            # avoids the 2-second timeout penalty per page.
            if not _ws_manager.is_connected(job_id):
                return
            try:
                future = asyncio.run_coroutine_threadsafe(
                    broadcast(current, total, message), loop
                )
                # Short timeout: if the event loop is busy or the
                # socket broke just now, don't block the OCR thread.
                future.result(timeout=1)
            except Exception:
                # Socket gone or loop overloaded — just keep going.
                pass

        result = await loop.run_in_executor(
            _executor,
            lambda: _ocr.process_pdf(str(input_path), str(output_path), settings, sync_callback)
        )

        if job_id:
            await _ws_manager.send(job_id, {"current": -1, "total": -1, "message": "done"})
            _ws_manager.disconnect(job_id)   # ← free the slot

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message)

        media = "text/plain" if output_format == "txt" else "application/pdf"
        return CleanupFileResponse(
            path=str(output_path),
            media_type=media,
            filename=f"{stem}_ocr.{output_ext}",
            temp_dir=tmp,
        )

    except Exception as e:
        _cleanup_dir(tmp)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Merge  —  POST /api/merge
# ---------------------------------------------------------------------------

@app.post("/api/merge")
async def merge_pdfs(
    input_data: Annotated[tuple[list[Path], Path], Depends(resolve_multiple_inputs)],
):
    input_paths, tmp = input_data

    for path_obj in input_paths:
        if not path_obj.name.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"'{path_obj}' is not a PDF.")

    if len(input_paths) < 2:
        raise HTTPException(status_code=400, detail="At least two PDF files are required.")

    try:
        input_str_paths = [str(p) for p in input_paths]
        output_path = str(tmp / "merged.pdf")
        success = _merge.merge_pdfs(input_str_paths, output_path)

        if not success:
            raise HTTPException(status_code=500, detail="Merge failed.")

        return CleanupFileResponse(
            path=output_path,
            media_type="application/pdf",
            filename="merged.pdf",
            temp_dir=tmp,
        )

    except Exception as e:
        _cleanup_dir(tmp)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Split by range  —  POST /api/split/range
# ---------------------------------------------------------------------------

@app.post("/api/split/range")
async def split_by_range(
    start_page: Annotated[int, Form(ge=1)],
    end_page:   Annotated[int, Form(ge=1)],
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
):
    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    if end_page < start_page:
        raise HTTPException(status_code=400, detail="end_page must be >= start_page.")

    try:
        output_path = tmp / "split.pdf"
        success = _split.split_by_range(
            str(input_path), str(output_path), start_page, end_page
        )

        if not success:
            raise HTTPException(status_code=500, detail="Split failed — check page range.")

        return CleanupFileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=f"{stem}_p{start_page}-{end_page}.pdf",
            temp_dir=tmp,
        )

    except Exception as e:
        _cleanup_dir(tmp)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Split into individual pages  —  POST /api/split/pages
# ---------------------------------------------------------------------------

@app.post("/api/split/pages")
async def split_into_pages(
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
):
    """Split a PDF into individual single-page PDFs returned as a zip archive."""
    import zipfile

    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    try:
        pages_dir  = tmp / "pages"
        success = _split.split_into_pages(str(input_path), str(pages_dir))

        if not success:
            raise HTTPException(status_code=500, detail="Split failed.")

        # Zip up the individual pages
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

    except Exception as e:
        _cleanup_dir(tmp)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Compress  —  POST /api/compress
# ---------------------------------------------------------------------------

@app.post("/api/compress")
async def compress_pdf_endpoint(
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
    compression_level: Annotated[str, Form()] = "medium",
):
    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    if compression_level not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="compression_level must be 'low', 'medium', or 'high'.")

    try:
        output_path = tmp / "compressed.pdf"
        result = _compress.compress_pdf(str(input_path), str(output_path), compression_level)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Compression failed.")

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

    except Exception as e:
        _cleanup_dir(tmp)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# PDF to Images  —  POST /api/pdf-to-images
# ---------------------------------------------------------------------------

@app.post("/api/pdf-to-images")
async def pdf_to_images_endpoint(
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
    image_format: Annotated[str, Form()] = "PNG",
    dpi: Annotated[int, Form()] = 150,
):
    input_path, tmp = input_data
    if not input_path.name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    stem = input_path.stem

    if image_format.upper() not in ["PNG", "JPG"]:
        raise HTTPException(status_code=400, detail="image_format must be 'PNG' or 'JPG'.")

    try:
        output_zip_path = tmp / f"{stem}_images.zip"
        success = _pdf_to_images.convert_pdf_to_images_zip(
            str(input_path), str(output_zip_path), image_format.upper(), dpi
        )

        if not success:
            raise HTTPException(status_code=500, detail="Conversion to images failed.")

        return CleanupFileResponse(
            path=str(output_zip_path),
            media_type="application/zip",
            filename=f"{stem}_images.zip",
            temp_dir=tmp,
        )

    except Exception as e:
        _cleanup_dir(tmp)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Image to PDF  —  POST /api/image-to-pdf
# ---------------------------------------------------------------------------

@app.post("/api/image-to-pdf")
async def image_to_pdf_endpoint(
    input_data: Annotated[tuple[list[Path], Path], Depends(resolve_multiple_inputs)],
    page_size: Annotated[str, Form()] = "A4",
    orientation: Annotated[str, Form()] = "Portrait",
    margin: Annotated[str, Form()] = "Small",
):
    input_paths, tmp = input_data

    for path_obj in input_paths:
        ext = path_obj.suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png"]:
            raise HTTPException(status_code=422, detail="Only JPG, JPEG, and PNG images are supported.")

    try:
        image_paths = [str(p) for p in input_paths]
        output_path = tmp / "output.pdf"
        success = _image_to_pdf.convert_images_to_pdf(
            image_paths, str(output_path), page_size, orientation, margin
        )

        if not success:
            raise HTTPException(status_code=500, detail="Conversion to PDF failed.")

        return CleanupFileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="images_combined.pdf",
            temp_dir=tmp,
        )

    except Exception as e:
        _cleanup_dir(tmp)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Delete Pages  —  POST /api/delete-pages
# ---------------------------------------------------------------------------

@app.post("/api/delete-pages")
async def delete_pdf_pages(
    input_data: Annotated[tuple[Path, Path], Depends(resolve_single_input)],
    pages_to_delete: Annotated[str, Form()] = "[]",
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

    try:
        output_path = tmp / "deleted.pdf"
        success = _delete_pages.delete_pages(str(input_path), str(output_path), pages_list)

        if not success:
            raise HTTPException(status_code=500, detail="Delete pages failed.")

        return CleanupFileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=f"{stem}_deleted.pdf",
            temp_dir=tmp,
        )

    except Exception as e:
        _cleanup_dir(tmp)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
