; Inno Setup script — skeleton for v1 Windows installer (see design doc §5.5).
; Install Inno Setup from https://jrsoftware.org/isinfo.php then compile this .iss
;
; BEFORE compiling:
;   1. Build a payload folder containing: python runtime, app sources, streamlit, deps, shortcuts.
;      (The portable bundle script is one way to produce inputs; the final layout may differ.)
;   2. Update the #define MyAppSource below to point at that folder.
;
#define MyAppName "The Archivist"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "The Archivist Project"
#define MyAppExeName "Launch-Archivist-UI.bat"
; Payload root (must contain python/, app/ or equivalent + launcher):
#define MyAppSource "..\dist\InstallerPayload"

[Setup]
AppId={{7971D1F8-AB2F-499C-A312-5B97D87E3744}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=ArchivistSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Optional: launch after install — uncomment when a real launcher exists:
; Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
