"""
Dependencies Preparation Script for ClearSight Docs
====================================================

This script helps prepare portable versions of external dependencies:
- Tesseract OCR (for text recognition)
- Poppler (for PDF to image conversion, used by OCR)

These are bundled with the installer so users don't need to install them.

Usage:
    python prepare_dependencies.py

After running, you'll have:
- 'tesseract-portable' folder with Tesseract OCR
- 'poppler-portable' folder with Poppler utilities
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import tempfile
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
TESSERACT_PORTABLE_DIR = PROJECT_DIR / "tesseract-portable"
POPPLER_PORTABLE_DIR = PROJECT_DIR / "poppler-portable"

# Tesseract installation paths
TESSERACT_INSTALL_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR"),
    Path(os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR")),
    Path(r"C:\Tesseract-OCR"),
]

# Poppler download URL (from poppler-windows releases)
# Update this URL when new versions are released
POPPLER_DOWNLOAD_URL = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.02.0-0/Release-24.02.0-0.zip"

# Essential tessdata files
ESSENTIAL_TESSDATA = [
    "eng.traineddata",     # English
    "osd.traineddata",     # Orientation and script detection
    # Add more languages as needed:
    # "fra.traineddata",   # French
    # "deu.traineddata",   # German
    # "spa.traineddata",   # Spanish
]


def format_size(size_bytes: int) -> str:
    """Format size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def calculate_folder_size(path: Path) -> int:
    """Calculate total size of a folder in bytes."""
    total = 0
    for file in path.rglob("*"):
        if file.is_file():
            total += file.stat().st_size
    return total


def find_tesseract_installation():
    """Find an existing Tesseract installation."""
    for path in TESSERACT_INSTALL_PATHS:
        tesseract_exe = path / "tesseract.exe"
        if tesseract_exe.exists():
            print(f"[FOUND] Tesseract installation at: {path}")
            return path
    return None


def copy_tesseract_files(source_dir: Path, dest_dir: Path) -> bool:
    """Copy essential Tesseract files to portable directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nCopying Tesseract from {source_dir}...")
    
    # Copy executable
    src_exe = source_dir / "tesseract.exe"
    if src_exe.exists():
        shutil.copy2(src_exe, dest_dir / "tesseract.exe")
        print(f"  [OK] tesseract.exe")
    else:
        print(f"  [ERROR] tesseract.exe not found!")
        return False
    
    # Copy all DLLs
    dll_count = 0
    for dll in source_dir.glob("*.dll"):
        shutil.copy2(dll, dest_dir / dll.name)
        dll_count += 1
    print(f"  [OK] {dll_count} DLL files")
    
    # Copy tessdata folder
    src_tessdata = source_dir / "tessdata"
    dest_tessdata = dest_dir / "tessdata"
    
    if src_tessdata.exists():
        dest_tessdata.mkdir(exist_ok=True)
        
        copied_langs = 0
        for lang_file in ESSENTIAL_TESSDATA:
            src_lang = src_tessdata / lang_file
            if src_lang.exists():
                shutil.copy2(src_lang, dest_tessdata / lang_file)
                copied_langs += 1
                print(f"  [OK] tessdata/{lang_file}")
        
        # Copy configs
        src_configs = src_tessdata / "configs"
        if src_configs.exists():
            shutil.copytree(src_configs, dest_tessdata / "configs", dirs_exist_ok=True)
        
        print(f"  [OK] {copied_langs} language files")
    else:
        print(f"  [WARN] tessdata folder not found")
        return False
    
    return True


def prepare_tesseract() -> bool:
    """Prepare portable Tesseract OCR."""
    print("\n" + "=" * 60)
    print("TESSERACT OCR")
    print("=" * 60)
    
    if TESSERACT_PORTABLE_DIR.exists():
        if (TESSERACT_PORTABLE_DIR / "tesseract.exe").exists():
            size = calculate_folder_size(TESSERACT_PORTABLE_DIR)
            print(f"[INFO] Tesseract already prepared ({format_size(size)})")
            response = input("Recreate? [y/N]: ").strip().lower()
            if response != 'y':
                return True
            shutil.rmtree(TESSERACT_PORTABLE_DIR)
    
    source_dir = find_tesseract_installation()
    
    if source_dir:
        if copy_tesseract_files(source_dir, TESSERACT_PORTABLE_DIR):
            size = calculate_folder_size(TESSERACT_PORTABLE_DIR)
            print(f"\n[SUCCESS] Tesseract prepared ({format_size(size)})")
            return True
        return False
    
    print("\n[NOT FOUND] Tesseract is not installed.")
    print("\nInstall from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("Or use: winget install UB-Mannheim.TesseractOCR")
    return False


def download_file(url: str, dest_path: Path, desc: str = "Downloading") -> bool:
    """Download a file with progress indicator."""
    print(f"\n{desc}...")
    print(f"  URL: {url}")
    
    try:
        def progress_hook(block_count, block_size, total_size):
            downloaded = block_count * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                print(f"\r  Progress: {percent:.1f}% ({format_size(downloaded)}/{format_size(total_size)})", end="")
        
        urllib.request.urlretrieve(url, dest_path, progress_hook)
        print()  # New line after progress
        return True
    except Exception as e:
        print(f"\n  [ERROR] Download failed: {e}")
        return False


def prepare_poppler() -> bool:
    """Prepare portable Poppler utilities."""
    print("\n" + "=" * 60)
    print("POPPLER (PDF utilities)")
    print("=" * 60)
    
    if POPPLER_PORTABLE_DIR.exists():
        if (POPPLER_PORTABLE_DIR / "bin" / "pdftoppm.exe").exists():
            size = calculate_folder_size(POPPLER_PORTABLE_DIR)
            print(f"[INFO] Poppler already prepared ({format_size(size)})")
            response = input("Recreate? [y/N]: ").strip().lower()
            if response != 'y':
                return True
            shutil.rmtree(POPPLER_PORTABLE_DIR)
    
    print("\nPoppler is required for PDF to image conversion (used by OCR).")
    print("It will be downloaded from GitHub releases.")
    
    response = input("\nDownload Poppler? [Y/n]: ").strip().lower()
    if response == 'n':
        print("[SKIP] Poppler not downloaded. OCR may have limited functionality.")
        return False
    
    # Download to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "poppler.zip"
        
        if not download_file(POPPLER_DOWNLOAD_URL, zip_path, "Downloading Poppler"):
            return False
        
        print("\nExtracting...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Extract to temp first
                zf.extractall(temp_dir)
            
            # Find the extracted folder (it's usually named poppler-XX.XX.X)
            extracted_dirs = [d for d in Path(temp_dir).iterdir() 
                           if d.is_dir() and d.name.startswith('poppler')]
            
            if extracted_dirs:
                # Move to destination
                shutil.move(str(extracted_dirs[0]), str(POPPLER_PORTABLE_DIR))
                
                # Verify
                if (POPPLER_PORTABLE_DIR / "Library" / "bin" / "pdftoppm.exe").exists():
                    # Reorganize - move Library/bin to just bin for easier access
                    lib_bin = POPPLER_PORTABLE_DIR / "Library" / "bin"
                    dest_bin = POPPLER_PORTABLE_DIR / "bin"
                    shutil.move(str(lib_bin), str(dest_bin))
                    
                    size = calculate_folder_size(POPPLER_PORTABLE_DIR)
                    print(f"\n[SUCCESS] Poppler prepared ({format_size(size)})")
                    return True
                elif (POPPLER_PORTABLE_DIR / "bin" / "pdftoppm.exe").exists():
                    size = calculate_folder_size(POPPLER_PORTABLE_DIR)
                    print(f"\n[SUCCESS] Poppler prepared ({format_size(size)})")
                    return True
            
            print("[ERROR] Could not find Poppler executables in archive")
            return False
            
        except Exception as e:
            print(f"[ERROR] Extraction failed: {e}")
            return False


def main():
    print("=" * 70)
    print("ClearSight Docs - Dependencies Preparation")
    print("=" * 70)
    
    tesseract_ok = prepare_tesseract()
    poppler_ok = prepare_poppler()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Tesseract OCR: {'[READY]' if tesseract_ok else '[NOT READY]'}")
    print(f"  Poppler:       {'[READY]' if poppler_ok else '[NOT READY]'}")
    
    if tesseract_ok or poppler_ok:
        print("\nNext step: Run build_installer.bat to create the installer")
    
    print()
    return 0 if tesseract_ok else 1


if __name__ == "__main__":
    sys.exit(main())
