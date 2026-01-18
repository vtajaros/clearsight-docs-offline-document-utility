@echo off
REM ============================================================================
REM ClearSight Docs - Complete Installer Build Script
REM ============================================================================
REM This script:
REM   1. Builds the Python application with PyInstaller
REM   2. Bundles Tesseract OCR with the application
REM   3. Creates a Windows installer using Inno Setup
REM
REM Prerequisites:
REM   - Python 3.x with virtual environment at ..\.venv
REM   - PyInstaller (will be installed if missing)
REM   - Inno Setup 6 installed at default location or in PATH
REM   - Tesseract OCR folder at ..\tesseract-portable (or modify TESSERACT_DIR below)
REM
REM ============================================================================

setlocal EnableDelayedExpansion

REM ============================================================================
REM CONFIGURATION - Modify these paths as needed
REM ============================================================================

REM Application info
set APP_NAME=ClearSight Docs
set APP_VERSION=1.5.0
set APP_PUBLISHER=vtajaros
set APP_EXE_NAME=ClearSightDocs.exe

REM Paths (relative to this script's location in installer\ folder)
set PROJECT_DIR=%~dp0..
set VENV_DIR=%PROJECT_DIR%\..\.venv
set DIST_DIR=%PROJECT_DIR%\dist
set BUILD_DIR=%PROJECT_DIR%\build
set INSTALLER_DIR=%~dp0

REM Tesseract OCR path - modify if your Tesseract is elsewhere
set TESSERACT_DIR=%PROJECT_DIR%\tesseract-portable
REM Alternative: Use the tesseract-5.5.2 folder that exists in your project
REM set TESSERACT_DIR=%PROJECT_DIR%\tesseract-5.5.2

REM Poppler path - for PDF to image conversion (used by OCR)
set POPPLER_DIR=%PROJECT_DIR%\poppler-portable

REM Inno Setup path - modify if installed elsewhere
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_SETUP% set INNO_SETUP="C:\Program Files\Inno Setup 6\ISCC.exe"

REM ============================================================================
REM STEP 0: Check prerequisites
REM ============================================================================

echo ============================================================================
echo   %APP_NAME% - Installer Build Script
echo ============================================================================
echo.

cd /d "%PROJECT_DIR%"

REM Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found. Please run this script from the installer folder.
    echo Expected project directory: %PROJECT_DIR%
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at %VENV_DIR%
    echo Please create it first with: python -m venv %VENV_DIR%
    pause
    exit /b 1
)

echo [OK] Project directory found: %PROJECT_DIR%
echo [OK] Virtual environment found: %VENV_DIR%
echo.

REM ============================================================================
REM STEP 1: Install/Update PyInstaller
REM ============================================================================

echo [STEP 1] Checking PyInstaller installation...
"%VENV_DIR%\Scripts\pip.exe" show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    "%VENV_DIR%\Scripts\pip.exe" install pyinstaller
) else (
    echo [OK] PyInstaller is installed
)
echo.

REM ============================================================================
REM STEP 2: Generate application icon if needed
REM ============================================================================

echo [STEP 2] Checking application icon...
if not exist "%PROJECT_DIR%\app_icon.ico" (
    echo Generating application icon...
    "%VENV_DIR%\Scripts\python.exe" "%PROJECT_DIR%\create_icon.py"
) else (
    echo [OK] Application icon exists
)
echo.

REM ============================================================================
REM STEP 3: Prepare Tesseract OCR for bundling
REM ============================================================================

echo [STEP 3] Checking Tesseract OCR for bundling...

REM Check if we have a portable Tesseract
if exist "%TESSERACT_DIR%\tesseract.exe" (
    echo [OK] Tesseract found at: %TESSERACT_DIR%
    set BUNDLE_TESSERACT=1
) else (
    REM Check standard installation
    if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        echo [INFO] System Tesseract found. Creating portable copy...
        set TESSERACT_DIR=C:\Program Files\Tesseract-OCR
        set BUNDLE_TESSERACT=1
    ) else (
        echo [WARNING] Tesseract not found. OCR features will require separate installation.
        set BUNDLE_TESSERACT=0
    )
)
echo.

REM ============================================================================
REM STEP 4: Clean previous builds
REM ============================================================================

echo [STEP 4] Cleaning previous builds...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%DIST_DIR%" 2>nul
echo [OK] Build directories cleaned
echo.

REM ============================================================================
REM STEP 5: Build with PyInstaller
REM ============================================================================

echo [STEP 5] Building application with PyInstaller...
echo This may take several minutes...
echo.

cd /d "%PROJECT_DIR%"

REM Use the spec file for building
"%VENV_DIR%\Scripts\pyinstaller.exe" --clean --noconfirm "%INSTALLER_DIR%\ClearSightDocs_Installer.spec"

if not exist "%DIST_DIR%\%APP_EXE_NAME%" (
    echo.
    echo ERROR: PyInstaller build failed!
    echo Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo [OK] PyInstaller build completed successfully
echo.

REM ============================================================================
REM STEP 6: Copy Tesseract OCR to distribution
REM ============================================================================

if "%BUNDLE_TESSERACT%"=="1" (
    echo [STEP 6] Bundling Tesseract OCR...
    
    set TESSERACT_DEST=%DIST_DIR%\tesseract
    mkdir "!TESSERACT_DEST!" 2>nul
    
    REM Copy Tesseract executable and DLLs
    copy "%TESSERACT_DIR%\tesseract.exe" "!TESSERACT_DEST!\" >nul 2>&1
    copy "%TESSERACT_DIR%\*.dll" "!TESSERACT_DEST!\" >nul 2>&1
    
    REM Copy tessdata folder (language data)
    if exist "%TESSERACT_DIR%\tessdata" (
        xcopy "%TESSERACT_DIR%\tessdata" "!TESSERACT_DEST!\tessdata\" /E /I /Q >nul 2>&1
    )
    
    echo [OK] Tesseract OCR bundled
) else (
    echo [STEP 6] Skipping Tesseract bundling (not found)
)
echo.

REM ============================================================================
REM STEP 6b: Copy Poppler to distribution
REM ============================================================================

set BUNDLE_POPPLER=0
if exist "%POPPLER_DIR%\bin\pdftoppm.exe" (
    echo [STEP 6b] Bundling Poppler...
    
    set POPPLER_DEST=%DIST_DIR%\poppler
    mkdir "!POPPLER_DEST!" 2>nul
    mkdir "!POPPLER_DEST!\bin" 2>nul
    
    REM Copy Poppler binaries
    xcopy "%POPPLER_DIR%\bin\*" "!POPPLER_DEST!\bin\" /E /I /Q >nul 2>&1
    
    echo [OK] Poppler bundled
    set BUNDLE_POPPLER=1
) else (
    echo [STEP 6b] Skipping Poppler bundling (not found at %POPPLER_DIR%)
    echo          Run prepare_dependencies.py to download Poppler
)
echo.

REM ============================================================================
REM STEP 7: Create Windows Installer with Inno Setup
REM ============================================================================

echo [STEP 7] Creating Windows Installer...

REM Check if Inno Setup is available
if exist %INNO_SETUP% (
    echo Using Inno Setup at: %INNO_SETUP%
    %INNO_SETUP% "%INSTALLER_DIR%\ClearSightDocs.iss"
    
    if exist "%INSTALLER_DIR%\Output\ClearSightDocs_Setup.exe" (
        echo.
        echo ============================================================================
        echo   BUILD SUCCESSFUL!
        echo ============================================================================
        echo.
        echo Installer created at:
        echo   %INSTALLER_DIR%\Output\ClearSightDocs_Setup.exe
        echo.
        echo Standalone executable at:
        echo   %DIST_DIR%\%APP_EXE_NAME%
        echo.
    ) else (
        echo.
        echo [WARNING] Inno Setup build may have failed.
        echo Check the output above for errors.
    )
) else (
    echo.
    echo [WARNING] Inno Setup not found at expected locations.
    echo.
    echo To create the Windows installer:
    echo   1. Download Inno Setup from: https://jrsoftware.org/isinfo.php
    echo   2. Install it (default location is fine)
    echo   3. Run this script again, OR
    echo   4. Open %INSTALLER_DIR%\ClearSightDocs.iss in Inno Setup and compile
    echo.
    echo The standalone executable is still available at:
    echo   %DIST_DIR%\%APP_EXE_NAME%
)

echo.
pause
