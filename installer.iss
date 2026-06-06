; Inno Setup Script for MyShopERP
[Setup]
AppName=T&S PowerTech ERP
AppVersion=1.0
DefaultDirName={autopf}\MyShopERP
DefaultGroupName=T&S PowerTech ERP
OutputDir=dist
OutputBaseFilename=MyShopERP_Setup
SetupIconFile=logo.ico
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy the main executable
Source: "dist\MyShopERP\MyShopERP.exe"; DestDir: "{app}"; Flags: ignoreversion
; Copy all other files and folders recursively
Source: "dist\MyShopERP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\T&S PowerTech ERP"; Filename: "{app}\MyShopERP.exe"; IconFilename: "{app}\_internal\logo.ico"
Name: "{group}\{cm:UninstallProgram,T&S PowerTech ERP}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\T&S PowerTech ERP"; Filename: "{app}\MyShopERP.exe"; Tasks: desktopicon; IconFilename: "{app}\_internal\logo.ico"

[Run]
Filename: "{app}\MyShopERP.exe"; Description: "{cm:LaunchProgram,T&S PowerTech ERP}"; Flags: nowait postinstall skipifsilent
