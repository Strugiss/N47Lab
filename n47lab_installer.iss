; N47Lab CAD — Inno Setup Script
; ============================================================================
; Per compilare: ISCC.exe n47lab_installer.iss
; ============================================================================

#define MyAppName "N47Lab CAD"
#define MyAppVersion "1.0.6"
#define MyAppPublisher "N47Lab"
#define MyAppURL "https://www.paypal.com/donate/?hosted_button_id=BC8Q8DEFUE9LJ"
#define MyAppEmail "2injob.at2@gmail.com"
#define MyAppExeName "n47lab.exe"
#define MyAppIcon "build\N47Lab.ico"

[Setup]
AppId={{B8A3F2E1-4D7C-4A9E-8F6B-2C1D5E7A9F3B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppContact={#MyAppEmail}
DefaultDirName={autopf}\N47Lab
DefaultGroupName=N47Lab
AllowNoIcons=yes
LicenseFile=build\license.txt
InfoBeforeFile=build\preinstall.txt
InfoAfterFile=build\postinstall.txt
SetupIconFile={#MyAppIcon}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} v{#MyAppVersion}
PrivilegesRequired=admin
OutputDir=dist
OutputBaseFilename=N47Lab_v{#MyAppVersion}_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
DisableWelcomePage=no
DisableProgramGroupPage=yes

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion 64bit
Source: "build\N47Lab.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\preinstall.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\postinstall.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\N47Lab CAD"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\N47Lab.ico"; Comment: "N47Lab CAD v{#MyAppVersion}"
Name: "{group}\Disinstalla N47Lab"; Filename: "{uninstallexe}"; IconFilename: "{app}\N47Lab.ico"
Name: "{autodesktop}\N47Lab CAD"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\N47Lab.ico"; Tasks: desktopicon; Comment: "N47Lab CAD v{#MyAppVersion}"

[Tasks]
Name: "desktopicon"; Description: "Crea collegamento sul desktop"; GroupDescription: "Collegamenti:"; Flags: checkedonce

[Registry]
; .n47 file association
Root: HKCR; Subkey: ".n47"; ValueType: string; ValueName: ""; ValueData: "N47Lab.Document"; Flags: uninsdeletekeyifempty
Root: HKCR; Subkey: ".n47"; ValueType: string; ValueName: "Content Type"; ValueData: "application/x-n47lab"; Flags: uninsdeletekeyifempty
Root: HKCR; Subkey: "N47Lab.Document"; ValueType: string; ValueName: ""; ValueData: "Documento N47Lab"; Flags: uninsdeletekey
Root: HKCR; Subkey: "N47Lab.Document\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\N47Lab.ico,0"; Flags: uninsdeletekey
Root: HKCR; Subkey: "N47Lab.Document\Shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey
Root: HKCR; Subkey: "N47Lab.Document\Shell\open\DropTarget"; ValueType: string; ValueName: "DropTargetCLSID"; ValueData: "{{86C86720-42A0-1069-A2E8-08002B30309D}"; Flags: uninsdeletekey
Root: HKCR; Subkey: ".n47\OpenWithProgids"; ValueType: string; ValueName: "N47Lab.Document"; ValueData: ""; Flags: uninsdeletekeyifempty

; Context menu for .stl
Root: HKCR; Subkey: "SystemFileAssociations\.stl\shell\Apri con N47Lab"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\N47Lab.ico,0"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.stl\shell\Apri con N47Lab"; ValueType: string; ValueName: ""; ValueData: "Apri con N47Lab"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.stl\shell\Apri con N47Lab\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.stl\shell\Invia a N47Lab"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\N47Lab.ico,0"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.stl\shell\Invia a N47Lab"; ValueType: string; ValueName: ""; ValueData: "Invia a N47Lab per la stampa 3D"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.stl\shell\Invia a N47Lab\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --send-to-printer ""%1"""; Flags: uninsdeletekey

; Context menu for .obj
Root: HKCR; Subkey: "SystemFileAssociations\.obj\shell\Apri con N47Lab"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\N47Lab.ico,0"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.obj\shell\Apri con N47Lab"; ValueType: string; ValueName: ""; ValueData: "Apri con N47Lab"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.obj\shell\Apri con N47Lab\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.obj\shell\Invia a N47Lab"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\N47Lab.ico,0"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.obj\shell\Invia a N47Lab"; ValueType: string; ValueName: ""; ValueData: "Invia a N47Lab per la stampa 3D"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.obj\shell\Invia a N47Lab\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --send-to-printer ""%1"""; Flags: uninsdeletekey

; Context menu for .3mf
Root: HKCR; Subkey: "SystemFileAssociations\.3mf\shell\Apri con N47Lab"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\N47Lab.ico,0"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.3mf\shell\Apri con N47Lab"; ValueType: string; ValueName: ""; ValueData: "Apri con N47Lab"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.3mf\shell\Apri con N47Lab\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.3mf\shell\Invia a N47Lab"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\N47Lab.ico,0"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.3mf\shell\Invia a N47Lab"; ValueType: string; ValueName: ""; ValueData: "Invia a N47Lab per la stampa 3D"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.3mf\shell\Invia a N47Lab\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --send-to-printer ""%1"""; Flags: uninsdeletekey

; Context menu for .ply
Root: HKCR; Subkey: "SystemFileAssociations\.ply\shell\Apri con N47Lab"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\N47Lab.ico,0"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.ply\shell\Apri con N47Lab"; ValueType: string; ValueName: ""; ValueData: "Apri con N47Lab"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.ply\shell\Apri con N47Lab\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey

; Uninstall info
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: string; ValueName: "DisplayName"; ValueData: "N47Lab CAD v{#MyAppVersion}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#MyAppVersion}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: string; ValueName: "Publisher"; ValueData: "{#MyAppPublisher}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\N47Lab.ico,0"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: string; ValueName: "UninstallString"; ValueData: """{app}\unins000.exe"""
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: string; ValueName: "URLInfoAbout"; ValueData: "{#MyAppURL}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: string; ValueName: "HelpLink"; ValueData: "mailto:{#MyAppEmail}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: dword; ValueName: "EstimatedSize"; ValueData: 800000
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: dword; ValueName: "NoModify"; ValueData: 1
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\N47Lab"; ValueType: dword; ValueName: "NoRepair"; ValueData: 1

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Avvia N47Lab CAD"; Flags: nowait postinstall skipifsilent shellexec; WorkingDir: "{app}"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    Exec('taskkill', '/f /im n47lab.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
