"""Shared Poppler path resolver — used by ocr_service and pdf_to_images_service."""
import os
import shutil
import sys


def _resolve_poppler_path() -> str | None:
    """Return the Poppler bin directory, or None to let pdf2image auto-detect."""
    if getattr(sys, 'frozen', False):
        bundled = os.path.join(sys._MEIPASS, 'poppler', 'bin')
        if os.path.isdir(bundled):
            return bundled

    env_path = os.environ.get('POPPLER_PATH')
    if env_path and os.path.isdir(env_path):
        return env_path

    if shutil.which('pdftoppm'):
        return None

    win_fallback = r"C:\poppler\Library\bin"
    if os.path.isdir(win_fallback):
        return win_fallback

    return None


POPPLER_PATH: str | None = _resolve_poppler_path()
