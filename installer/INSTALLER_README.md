# ClearSight Docs - Windows Installer Build Guide

This folder contains all the scripts and configuration needed to create a Windows installer for ClearSight Docs.

## 📋 Prerequisites

Before building the installer, ensure you have:

1. **Python 3.x** with your virtual environment set up (`.venv` folder)
2. **PyInstaller** (will be installed automatically by the build script)
3. **Inno Setup 6** (for creating the Windows installer)
   - Download from: https://jrsoftware.org/isinfo.php
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6`
4. **Tesseract OCR** (for OCR features)
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Or use: `winget install UB-Mannheim.TesseractOCR`

## 📁 Files in this Folder

| File | Description |
|------|-------------|
| `build_installer.bat` | Main build script - runs everything |
| `ClearSightDocs_Installer.spec` | PyInstaller configuration |
| `ClearSightDocs.iss` | Inno Setup installer script |
| `prepare_tesseract.py` | Prepares portable Tesseract for bundling |
| `INSTALLER_README.md` | This file |

## 🚀 Quick Start

### Step 1: Prepare Tesseract OCR (First Time Only)

```batch
cd installer
python prepare_tesseract.py
```

This creates a `tesseract-portable` folder with the essential Tesseract files.

### Step 2: Build the Installer

```batch
cd installer
build_installer.bat
```

The script will:
1. Build the executable with PyInstaller
2. Bundle Tesseract OCR (if prepared)
3. Create the Windows installer with Inno Setup

### Step 3: Find Your Files

After successful build:
- **Standalone EXE**: `..\dist\ClearSightDocs.exe`
- **Windows Installer**: `Output\ClearSightDocs_Setup.exe`

## 🔧 Customization

### Changing Application Info

Edit the top of `ClearSightDocs.iss`:

```inno
#define MyAppName "ClearSight Docs"
#define MyAppVersion "1.5.0"
#define MyAppPublisher "Your Name"
```

### Adding More Languages (OCR)

Edit `prepare_tesseract.py` and uncomment the languages you need:

```python
ESSENTIAL_TESSDATA = [
    "eng.traineddata",     # English (always included)
    "osd.traineddata",     # Required
    "fra.traineddata",     # French (uncomment to include)
    "deu.traineddata",     # German
    # ... add more as needed
]
```

Then run `prepare_tesseract.py` again.

### Adding Data Files

Edit `ClearSightDocs_Installer.spec`:

```python
datas = [
    # Add your files here
    (os.path.join(project_dir, 'my_folder'), 'my_folder'),
]
```

And `ClearSightDocs.iss`:

```inno
[Files]
Source: "..\my_folder\*"; DestDir: "{app}\my_folder"; Flags: recursesubdirs
```

### Changing Installation Directory

Edit `ClearSightDocs.iss`:

```inno
DefaultDirName={autopf}\{#MyAppName}
; {autopf} = C:\Program Files or C:\Program Files (x86)
; Change to {localappdata}\{#MyAppName} for per-user install
```

## 📊 Build Output Structure

After building, the `dist` folder will contain:

```
dist/
├── ClearSightDocs.exe      # Main application (single file)
└── tesseract/              # Bundled Tesseract OCR
    ├── tesseract.exe
    ├── *.dll
    └── tessdata/
        ├── eng.traineddata
        └── osd.traineddata
```

The installer will package all of this into a single `.exe` installer.

## 🔍 Troubleshooting

### "Tesseract not found" during build

1. Install Tesseract OCR from the official sources
2. Run `prepare_tesseract.py` to create the portable version
3. Run the build script again

### "Inno Setup not found"

1. Download and install Inno Setup 6 from https://jrsoftware.org/isinfo.php
2. Install to default location, or edit `INNO_SETUP` variable in `build_installer.bat`

### PyInstaller errors

1. Make sure all dependencies are installed: `pip install -r requirements.txt`
2. Check for missing hidden imports in the `.spec` file
3. Try running with `--debug all` flag for more information

### Application crashes after installation

1. Check if Tesseract is properly bundled (look in install folder)
2. Verify the `TESSDATA_PREFIX` is being set correctly
3. Run the EXE from command line to see error messages

## 🏗️ How It Works

### PyInstaller Phase

PyInstaller bundles:
- Your Python code
- All imported Python modules
- Required DLLs and binaries
- Data files specified in the spec

The result is a single `.exe` file that contains everything except Tesseract.

### Tesseract Bundling

Tesseract is bundled separately because:
- It's a large binary (50-100MB with language data)
- It's easier to update independently
- Users can add more language files after installation

### Inno Setup Phase

Inno Setup creates a professional installer that:
- Shows a wizard interface
- Installs to Program Files
- Creates Start Menu and Desktop shortcuts
- Sets up uninstaller
- Writes registry entries for the app to find Tesseract

## 📝 Registry Entries

The installer creates these registry entries:

```
HKCU\Software\ClearSight Docs
├── InstallPath     = C:\Program Files\ClearSight Docs
└── TesseractPath   = C:\Program Files\ClearSight Docs\tesseract
```

The application reads these to find bundled Tesseract.

## 🔐 Code Signing (Optional)

For distribution, you may want to code sign your installer:

1. Obtain a code signing certificate
2. Add to `ClearSightDocs.iss`:

```inno
[Setup]
SignTool=signtool $f
SignedUninstaller=yes
```

3. Or sign manually after building:

```batch
signtool sign /a /t http://timestamp.digicert.com Output\ClearSightDocs_Setup.exe
```

## 📦 Distribution Checklist

Before distributing:

- [ ] Test on clean Windows 11 machine (or VM)
- [ ] Verify all features work without Python installed
- [ ] Check OCR works with bundled Tesseract
- [ ] Verify shortcuts are created correctly
- [ ] Test uninstallation removes all files
- [ ] Consider code signing for trust

## 🆘 Support

If you encounter issues:

1. Check the Troubleshooting section above
2. Review PyInstaller output for warnings
3. Test the standalone EXE before creating installer
4. Check Windows Event Viewer for crash logs
