[Setup]
AppName=Budżet Domowy
AppVersion=2.0.0
AppVerName=BudgetApp 2.0.0
AppPublisher=KlapkiSzatana
AppPublisherURL=https://github.com/KlapkiSzatana/budget-app
AppSupportURL=https://github.com/KlapkiSzatana/budget-app/issues
AppUpdatesURL=https://github.com/KlapkiSzatana/budget-app/releases
AppCopyright=© 2026 KlapkiSzatana
DefaultDirName={userappdata}\KlapkiSzatana\BudgetApp
DefaultGroupName=Budżet Domowy
UninstallDisplayIcon={app}\budget-app.exe
UninstallDisplayName=BudgetApp 2.0.0 - Zarządzanie Budżetem Domowym
Compression=lzma
SolidCompression=yes
OutputDir=user_setup
OutputBaseFilename=BudgetApp_Setup
LicenseFile=LICENSE
PrivilegesRequired=lowest
VersionInfoVersion=2.0.0.0
VersionInfoCompany=KlapkiSzatana
VersionInfoDescription=Aplikacja do zarządzania budżetem domowym
VersionInfoCopyright=Copyright © 2026 KlapkiSzatana

[Files]
Source: "dist\budget-app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\Budżet Domowy"; Filename: "{app}\budget-app.exe"; Tasks: desktopicon
Name: "{userprograms}\Budżet Domowy"; Filename: "{app}\budget-app.exe"

[Tasks]
Name: "desktopicon"; Description: "Stwórz skrót na pulpicie"; GroupDescription: "Dodatkowe:"; Flags: unchecked

[Run]
Filename: "{app}\budget-app.exe"; Description: "Uruchom Budżet Domowy po zakończeniu"; Flags: nowait postinstall skipifsilent
