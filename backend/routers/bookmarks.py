"""
Bookmarks API Router.
"""
import os
import secrets
import shutil
import tempfile
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import fitz
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from services.bookmark_service import BookmarkNode, BookmarkService

# ---------------------------------------------------------------------------
# Auth / Verification
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _cleanup_dir(path: Path) -> None:
    """Remove a temporary directory, ignoring errors."""
    try:
        if path.exists():
            shutil.rmtree(path)
    except Exception as e:
        print(f"Failed to clean up temp directory {path}: {e}")

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

def _validate_output_path(raw: str) -> Path:
    """
    Check for directory traversal and ensure it ends with .pdf.
    Also ensures the parent directory exists.
    """
    path_obj = Path(raw)
    if ".." in path_obj.parts or ".." in raw or "/../" in raw or "\\..\\" in raw:
        raise HTTPException(status_code=400, detail="Directory traversal not allowed.")
    if not raw.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Output path must end with .pdf")
    try:
        path_obj.parent.resolve(strict=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Parent directory does not exist")
    return path_obj

# ---------------------------------------------------------------------------
# Router & Models
# ---------------------------------------------------------------------------

router = APIRouter()
_bookmark_svc = BookmarkService()
_executor = ThreadPoolExecutor(max_workers=2)

class WriteBookmarksRequest(BaseModel):
    source_path: str
    output_path: str
    bookmarks: list[BookmarkNode]

class ExtractRequest(BaseModel):
    path: str

@router.get("/read")
async def read_bookmarks(path: str, _=Depends(verify_token)):
    source_path = _validate_local_path(path)
    
    doc = None
    try:
        doc = fitz.open(str(source_path))
        page_count = len(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open PDF: {e}")
    finally:
        if doc is not None:
            doc.close()
            
    bookmarks = _bookmark_svc.get_bookmarks(str(source_path))
    return JSONResponse({
        "bookmarks": [b.model_dump() for b in bookmarks],
        "page_count": page_count
    })

@router.post("/write")
async def write_bookmarks(request: WriteBookmarksRequest, _=Depends(verify_token)):
    source_path = _validate_local_path(request.source_path)
    output_path = _validate_output_path(request.output_path)
    
    tmp = Path(tempfile.mkdtemp(prefix="clearsight_bm_"))
    tmp_output = tmp / output_path.name
    
    loop = asyncio.get_running_loop()
    try:
        await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                lambda: _bookmark_svc.write_bookmarks(
                    str(source_path), request.bookmarks, str(tmp_output)
                )
            ),
            timeout=60
        )
    except asyncio.TimeoutError:
        _cleanup_dir(tmp)
        raise HTTPException(status_code=504, detail="Write bookmarks timed out.")
    except Exception as e:
        _cleanup_dir(tmp)
        raise HTTPException(status_code=500, detail=str(e))
        
    return CleanupFileResponse(
        path=str(tmp_output),
        media_type="application/pdf",
        filename=output_path.name,
        temp_dir=tmp
    )

@router.post("/extract")
async def extract_bookmarks(body: ExtractRequest, _=Depends(verify_token)):
    validated = _validate_local_path(body.path)

    # Get page count
    try:
        doc = fitz.open(str(validated))
        page_count = len(doc)
    finally:
        doc.close()

    # Run heuristic in executor (CPU-bound, can take seconds on large PDFs)
    loop = asyncio.get_running_loop()
    try:
        bookmarks, has_text_layer = await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                lambda: _bookmark_svc.enrich_bookmarks(str(validated))
            ),
            timeout=120
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504,
            detail="Heading extraction timed out.")

    if not has_text_layer:
        return JSONResponse({
            "bookmarks": [],
            "is_generated": False,
            "needs_ocr": True,
            "page_count": page_count
        })

    return JSONResponse({
        "bookmarks": [b.model_dump() for b in bookmarks],
        "is_generated": True,
        "needs_ocr": False,
        "page_count": page_count
    })
