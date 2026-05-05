[Setup]
AppName=Budżet Domowy
AppVersion=1.5.3
; Instalacja w AppData użytkownika w folderze Heisenberg\BudgetApp
DefaultDirName={userappdata}\KlapkiSzatana\BudgetApp
DefaultGroupName=Budżet Domowy
UninstallDisplayIcon={app}\budget-app.exe
Compression=lzma
SolidCompression=yes
OutputDir=user_setup
OutputBaseFilename=BudgetApp_Setup
LicenseFile=LICENSE
PrivilegesRequired=lowest

[Files]
; Kopiuje całą zawartość folderu wyjściowego PyInstallera
Source: "dist\budget-app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Zmieniono na {userdesktop} oraz dodano skrót w menu Start
Name: "{userdesktop}\Budżet Domowy"; Filename: "{app}\budget-app.exe"; Tasks: desktopicon
Name: "{userprograms}\Budżet Domowy"; Filename: "{app}\budget-app.exe"

[Tasks]
Name: "desktopicon"; Description: "Stwórz skrót na pulpicie"; GroupDescription: "Dodatkowe:"; Flags: unchecked

[Run]
Filename: "{app}\budget-app.exe"; Description: "Uruchom Budżet Domowy po zakończeniu"; Flags: nowait postinstall skipifsilent
