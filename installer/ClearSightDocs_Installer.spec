# -*- mode: python ; coding: utf-8 -*-
"""
ClearSight Docs - PyInstaller Spec File for Installer Build
============================================================================

This spec file creates a single-file executable with all dependencies bundled.
It's designed to work with the Inno Setup installer script.

Usage:
    pyinstaller --clean --noconfirm ClearSightDocs_Installer.spec

Configuration Notes:
    - Modify 'app_name' and paths as needed
    - Add any additional data files to 'datas' list
    - Add hidden imports if you get ModuleNotFoundError at runtime
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ============================================================================
# CONFIGURATION
# ============================================================================

# Get the directory containing this spec file
spec_dir = os.path.dirname(os.path.abspath(SPEC))

# Project root is one level up from installer folder
project_dir = os.path.dirname(spec_dir)

app_name = 'ClearSightDocs'
main_script = os.path.join(project_dir, 'main.py')
icon_file = os.path.join(project_dir, 'app_icon.ico')

# ============================================================================
# DATA FILES
# ============================================================================

# Files and folders to bundle with the executable
# Format: (source_path, destination_folder_in_bundle)
datas = [
    # Application icon
    (icon_file, '.'),
    
    # UI folder - contains all page definitions
    (os.path.join(project_dir, 'ui'), 'ui'),
    
    # Services folder - contains all service modules  
    (os.path.join(project_dir, 'services'), 'services'),
    
    # Utils folder - utility modules
    (os.path.join(project_dir, 'utils'), 'utils'),
]

# Add tessdata folder if it exists in the project
tessdata_path = os.path.join(project_dir, 'tessdata')
if os.path.exists(tessdata_path):
    datas.append((tessdata_path, 'tessdata'))

# ============================================================================
# HIDDEN IMPORTS
# ============================================================================

# Modules that PyInstaller doesn't detect automatically
hidden_imports = [
    # PySide6 modules
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    
    # PDF libraries
    'fitz',           # PyMuPDF
    'pymupdf',
    'pypdf',
    
    # Image processing
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    
    # OCR
    'pytesseract',
    
    # Standard library modules sometimes missed
    'queue',
    'threading',
    'subprocess',
    'tempfile',
    'shutil',
    'json',
    'pathlib',
    
    # docx for Word export
    'docx',
    'docx.shared',
    'docx.enum.text',
    
    # XML processing (needed by docx)
    'lxml',
    'lxml.etree',
    'lxml._elementpath',
]

# ============================================================================
# EXCLUDED MODULES
# ============================================================================

# Modules to exclude (reduces file size)
excludes = [
    'matplotlib',
    'numpy.testing',
    'scipy',
    'pandas',
    'tkinter',
    'PyQt5',
    'PyQt6',
    'test',
    'unittest',
]

# ============================================================================
# BUILD CONFIGURATION
# ============================================================================

block_cipher = None

a = Analysis(
    [main_script],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                    # Enable UPX compression if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,               # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,            # Auto-detect architecture (x64/x86)
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file if os.path.exists(icon_file) else None,
    version=os.path.join(spec_dir, 'version_info.txt'),  # Windows version info
    uac_admin=False,             # Don't require admin by default
)
