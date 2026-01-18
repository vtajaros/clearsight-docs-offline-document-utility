"""
Tesseract OCR Portable Preparation Script
==========================================

This script helps prepare a portable version of Tesseract OCR for bundling
with the ClearSight Docs application.

The script can:
1. Copy an existing Tesseract installation to a portable folder
2. Download Tesseract from official sources (manual step required)

Usage:
    python prepare_tesseract.py

After running, you'll have a 'tesseract-portable' folder ready for bundling.
"""

import os
import sys
import shutil
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
PORTABLE_DIR = PROJECT_DIR / "tesseract-portable"

# Common Tesseract installation paths on Windows
TESSERACT_INSTALL_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR"),
    Path(os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR")),
    Path(r"C:\Tesseract-OCR"),
]

# Essential files to copy for a minimal portable Tesseract
ESSENTIAL_FILES = [
    "tesseract.exe",
    "*.dll",  # All DLLs are needed
]

# Essential tessdata files (language data)
# Add more languages as needed
ESSENTIAL_TESSDATA = [
    "eng.traineddata",     # English
    "osd.traineddata",     # Orientation and script detection
    # Uncomment or add languages you need:
    # "fra.traineddata",   # French
    # "deu.traineddata",   # German
    # "spa.traineddata",   # Spanish
    # "ita.traineddata",   # Italian
    # "por.traineddata",   # Portuguese
    # "chi_sim.traineddata",  # Chinese Simplified
    # "chi_tra.traineddata",  # Chinese Traditional
    # "jpn.traineddata",   # Japanese
    # "kor.traineddata",   # Korean
    # "ara.traineddata",   # Arabic
    # "rus.traineddata",   # Russian
]


def find_tesseract_installation():
    """Find an existing Tesseract installation."""
    for path in TESSERACT_INSTALL_PATHS:
        tesseract_exe = path / "tesseract.exe"
        if tesseract_exe.exists():
            print(f"[FOUND] Tesseract installation at: {path}")
            return path
    return None


def copy_tesseract_files(source_dir: Path, dest_dir: Path):
    """Copy essential Tesseract files to portable directory."""
    
    # Create destination directory
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nCopying files from {source_dir} to {dest_dir}...")
    
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
        
        # Copy only essential language files (to reduce size)
        copied_langs = 0
        for lang_file in ESSENTIAL_TESSDATA:
            src_lang = src_tessdata / lang_file
            if src_lang.exists():
                shutil.copy2(src_lang, dest_tessdata / lang_file)
                copied_langs += 1
                print(f"  [OK] tessdata/{lang_file}")
            else:
                print(f"  [WARN] tessdata/{lang_file} not found (optional)")
        
        # Also copy any config files
        for config in src_tessdata.glob("*.config"):
            shutil.copy2(config, dest_tessdata / config.name)
        
        # Copy configs folder if it exists
        src_configs = src_tessdata / "configs"
        if src_configs.exists():
            shutil.copytree(src_configs, dest_tessdata / "configs", dirs_exist_ok=True)
            print(f"  [OK] tessdata/configs/")
        
        print(f"  [OK] {copied_langs} language files")
    else:
        print(f"  [WARN] tessdata folder not found")
        return False
    
    return True


def calculate_folder_size(path: Path) -> int:
    """Calculate total size of a folder in bytes."""
    total = 0
    for file in path.rglob("*"):
        if file.is_file():
            total += file.stat().st_size
    return total


def format_size(size_bytes: int) -> str:
    """Format size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    print("=" * 70)
    print("Tesseract OCR Portable Preparation Script")
    print("=" * 70)
    print()
    
    # Check if portable folder already exists
    if PORTABLE_DIR.exists():
        tesseract_exe = PORTABLE_DIR / "tesseract.exe"
        if tesseract_exe.exists():
            size = calculate_folder_size(PORTABLE_DIR)
            print(f"[INFO] Portable Tesseract already exists at:")
            print(f"       {PORTABLE_DIR}")
            print(f"       Size: {format_size(size)}")
            print()
            
            response = input("Do you want to recreate it? [y/N]: ").strip().lower()
            if response != 'y':
                print("\nKeeping existing portable Tesseract.")
                return 0
            
            print("\nRemoving existing portable folder...")
            shutil.rmtree(PORTABLE_DIR)
    
    # Find existing Tesseract installation
    print("\nSearching for Tesseract installation...")
    source_dir = find_tesseract_installation()
    
    if source_dir:
        print("\nPreparing portable Tesseract...")
        if copy_tesseract_files(source_dir, PORTABLE_DIR):
            size = calculate_folder_size(PORTABLE_DIR)
            print()
            print("=" * 70)
            print("SUCCESS! Portable Tesseract created.")
            print("=" * 70)
            print(f"\nLocation: {PORTABLE_DIR}")
            print(f"Size: {format_size(size)}")
            print()
            print("Next steps:")
            print("1. Run 'build_installer.bat' to create the installer")
            print("2. The installer will automatically bundle Tesseract")
            return 0
        else:
            print("\n[ERROR] Failed to copy some essential files.")
            return 1
    
    else:
        print()
        print("=" * 70)
        print("Tesseract OCR NOT FOUND")
        print("=" * 70)
        print()
        print("Tesseract is not installed on this system.")
        print()
        print("To install Tesseract OCR:")
        print()
        print("Option 1: Download from UB Mannheim (recommended)")
        print("  https://github.com/UB-Mannheim/tesseract/wiki")
        print("  Download: tesseract-ocr-w64-setup-5.x.x.exe (64-bit)")
        print("         or tesseract-ocr-w32-setup-5.x.x.exe (32-bit)")
        print()
        print("Option 2: Use winget (Windows Package Manager)")
        print("  winget install UB-Mannheim.TesseractOCR")
        print()
        print("Option 3: Use Chocolatey")
        print("  choco install tesseract")
        print()
        print("After installing, run this script again to create")
        print("the portable version for bundling.")
        print()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
