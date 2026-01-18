; ============================================================================
; ClearSight Docs - Inno Setup Installer Script
; ============================================================================
;
; This script creates a professional Windows installer for ClearSight Docs.
;
; Prerequisites:
;   - Inno Setup 6.x (download from https://jrsoftware.org/isinfo.php)
;   - PyInstaller-built executable in ..\dist\ClearSightDocs.exe
;   - Tesseract OCR files in ..\dist\tesseract\ (optional, for OCR features)
;
; To compile:
;   1. Open this file in Inno Setup Compiler
;   2. Click Build > Compile (or press Ctrl+F9)
;   3. The installer will be created in the Output\ subfolder
;
; ============================================================================

; ============================================================================
; APPLICATION INFORMATION - Modify these for your application
; ============================================================================

#define MyAppName "ClearSight Docs"
#define MyAppVersion "1.5.0"
#define MyAppPublisher "vtajaros"
#define MyAppURL "https://github.com/vtajaros/clearsight-docs"
#define MyAppExeName "ClearSightDocs.exe"
#define MyAppDescription "PDF Toolkit - Convert, Merge, Split, OCR and more"

; Source directories (relative to this .iss file)
#define SourceDir "..\dist"
#define TesseractDir "..\dist\tesseract"
#define PopplerDir "..\dist\poppler"

; ============================================================================
; INSTALLER CONFIGURATION
; ============================================================================

[Setup]
; Unique identifier for this application (generate new GUID for your app)
; To generate: Tools > Generate GUID in Inno Setup
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Default installation directory
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; Allow user to change installation directory
DisableDirPage=no
DisableProgramGroupPage=yes

; Installer output settings
OutputDir=Output
OutputBaseFilename=ClearSightDocs_Setup
SetupIconFile=..\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression settings (lzma2 gives best compression)
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Installer appearance
WizardStyle=modern
WizardSizePercent=110

; Minimum Windows version (Windows 7 SP1 / Windows Server 2008 R2 SP1)
MinVersion=6.1sp1

; Architecture support
; ArchitecturesAllowed: which architectures the installer can run on
; ArchitecturesInstallIn64BitMode: install 64-bit components when on 64-bit Windows
ArchitecturesAllowed=x64compatible x86compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Privileges: admin required for Program Files installation
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; ============================================================================
; LANGUAGES
; ============================================================================

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; Add more languages as needed:
; Name: "french"; MessagesFile: "compiler:Languages\French.isl"
; Name: "german"; MessagesFile: "compiler:Languages\German.isl"
; Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

; ============================================================================
; INSTALLER TASKS (User-selectable options)
; ============================================================================

[Tasks]
; Desktop shortcut (checked by default)
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

; Quick Launch shortcut (unchecked by default, for older Windows)
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

; ============================================================================
; FILES TO INSTALL
; ============================================================================

[Files]
; Main application executable
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Application icon (for shortcuts and uninstaller)
Source: "..\app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

; Tesseract OCR files (if bundled)
; The wildcard pattern will skip if directory doesn't exist
Source: "{#TesseractDir}\*"; DestDir: "{app}\tesseract"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; Poppler PDF utilities (if bundled) - required for OCR functionality
Source: "{#PopplerDir}\*"; DestDir: "{app}\poppler"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; Additional data files (add as needed)
; Source: "..\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

; ============================================================================
; SHORTCUTS
; ============================================================================

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Comment: "{#MyAppDescription}"

; Start Menu uninstall shortcut  
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\app_icon.ico"

; Desktop shortcut (if task selected)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon; Comment: "{#MyAppDescription}"

; Quick Launch shortcut (if task selected)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

; ============================================================================
; REGISTRY ENTRIES
; ============================================================================

[Registry]
; Set environment variable for Tesseract (application-specific, not system-wide)
; The app will look for Tesseract in its own directory first
Root: HKCU; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "TesseractPath"; ValueData: "{app}\tesseract"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "PopplerPath"; ValueData: "{app}\poppler\bin"; Flags: uninsdeletekey

; Optional: Add to system PATH (uncomment if needed)
; Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\tesseract"; Check: NeedsAddPath('{app}\tesseract')

; ============================================================================
; RUN AFTER INSTALLATION
; ============================================================================

[Run]
; Option to run application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; ============================================================================
; UNINSTALL
; ============================================================================

[UninstallDelete]
; Clean up any files created during runtime
Type: filesandordirs; Name: "{app}\tesseract\tessdata"
Type: dirifempty; Name: "{app}\tesseract"
Type: filesandordirs; Name: "{app}\poppler"
Type: dirifempty; Name: "{app}"

; ============================================================================
; CUSTOM CODE (Pascal Script)
; ============================================================================

[Code]
// Function to check if a path is already in the system PATH
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  // Look for the path with leading and trailing semicolon
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

// Check for 64-bit Windows
function Is64BitInstallMode: Boolean;
begin
  Result := ProcessorArchitecture = paX64;
end;

// Show custom message on installation
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Any post-installation tasks can go here
    // For example, you could copy additional config files
  end;
end;

// Customize the "Ready to Install" page
function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  S: String;
begin
  S := '';
  
  if MemoDirInfo <> '' then
    S := S + MemoDirInfo + NewLine + NewLine;
    
  if MemoGroupInfo <> '' then
    S := S + MemoGroupInfo + NewLine + NewLine;
    
  if MemoTasksInfo <> '' then
    S := S + MemoTasksInfo + NewLine + NewLine;
  
  // Add information about bundled components
  S := S + 'Bundled Components:' + NewLine;
  S := S + Space + 'ClearSight Docs application' + NewLine;
  
  if DirExists(ExpandConstant('{#TesseractDir}')) then
    S := S + Space + 'Tesseract OCR engine' + NewLine
  else
    S := S + Space + 'Tesseract OCR (not bundled - OCR features may not work)' + NewLine;
  
  if DirExists(ExpandConstant('{#PopplerDir}')) then
    S := S + Space + 'Poppler PDF utilities' + NewLine
  else
    S := S + Space + 'Poppler (not bundled - some features may be limited)' + NewLine;
  
  Result := S;
end;
