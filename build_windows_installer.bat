@echo off
REM ============================================================================
REM ClearSight Docs - Quick Build Script
REM ============================================================================
REM This script provides a quick way to build the installer from the project root.
REM For advanced options, use installer\build_installer.bat directly.
REM ============================================================================

echo.
echo ============================================================================
echo   ClearSight Docs - Building Windows Installer
echo ============================================================================
echo.

cd /d "%~dp0"

REM Check if installer folder exists
if not exist "installer\build_installer.bat" (
    echo ERROR: installer\build_installer.bat not found!
    echo Please ensure you're running this from the project root.
    pause
    exit /b 1
)

REM Run the main installer build script
call "installer\build_installer.bat"
