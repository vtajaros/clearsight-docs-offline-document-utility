@echo off
REM PDF Toolkit Launcher for Windows
REM This script runs the PDF Toolkit application

echo ========================================
echo    PDF Toolkit - Document Utility
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher
    echo.
    pause
    exit /b 1
)

echo Starting PDF Toolkit...
echo.

REM Run the application
python main.py

REM If the application exits with an error
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    echo Please check the error messages above.
    echo.
    pause
)
