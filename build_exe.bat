@echo off
echo ==========================================
echo   ClearSight Docs - Build Executable
echo ==========================================
echo.

REM Check if we're in the right directory
if not exist "main.py" (
    echo ERROR: main.py not found. Please run this script from the pdf-toolkit directory.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "..\.venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\.venv\Scripts\activate.bat
)

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Generate icon if it doesn't exist
if not exist "app_icon.ico" (
    echo Generating application icon...
    python create_icon.py
)

echo.
echo Building executable...
echo This may take a few minutes...
echo.

REM Clean previous build
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build using the spec file
pyinstaller --clean --noconfirm ClearSightDocs.spec

echo.
if exist "dist\ClearSightDocs.exe" (
    echo ==========================================
    echo   BUILD SUCCESSFUL!
    echo ==========================================
    echo.
    echo Executable created at:
    echo   dist\ClearSightDocs.exe
    echo.
    echo You can now distribute this file.
    echo.
) else (
    echo ==========================================
    echo   BUILD FAILED
    echo ==========================================
    echo Please check the error messages above.
)

pause
