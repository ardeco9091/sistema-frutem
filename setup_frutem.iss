; --- DEFINICIONES DEL PROYECTO ---
#define MyAppName "Sistema FrutEm"
#define MyAppVersion "1.0"
#define MyAppPublisher "Frut&Em Dev Team"
; El nombre exacto que le pusimos en el build.py
#define MyAppExeName "Sistema_FrutEm_V79.exe" 

; --- RUTA RAIZ DEL PROYECTO (La que me pasaste) ---
#define ProjectRoot "C:\Users\ardec\Desktop\Sistema_FrutEm_FINAL_V20\Sistema_FrutEmV20"
; --- RUTA DONDE ESTÁN LOS ARCHIVOS COMPILADOS (Carpeta dist generada por build.py) ---
#define BuildDir ProjectRoot + "\dist\Sistema_FrutEm_V79"

[Setup]
; Identificador único (No lo cambies si ya instalaste versiones previas para que las detecte)
AppId={{82782782-E6F7-4321-ABCD-6789ABCDEF01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Ruta por defecto: C:\Archivos de Programa\Sistema FrutEm
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Pedir admin para poder escribir en Archivos de Programa
PrivilegesRequired=admin
; Carpeta donde aparecerá el instalador generado (Output dentro de tu carpeta)
OutputDir={#ProjectRoot}\Output
OutputBaseFilename=Instalador_FrutEm_v1
; Icono del instalador
SetupIconFile={#ProjectRoot}\iconos\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; --- AQUI OCURRE LA MAGIA: Usamos la variable BuildDir ---

; 1. EL EJECUTABLE
Source: "{#BuildDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; 2. BASE DE DATOS Y CONFIG (CON PERMISOS DE ESCRITURA PARA USUARIOS NORMALES)
; Esto evita que el programa falle si no se ejecuta como Administrador
Source: "{#BuildDir}\sistema_rrhh_full.db"; DestDir: "{app}"; Flags: ignoreversion; Permissions: users-modify
Source: "{#BuildDir}\config.json"; DestDir: "{app}"; Flags: ignoreversion; Permissions: users-modify

; 3. LA DLL DE HIKVISION (CRÍTICO)
Source: "{#BuildDir}\HCNetSDK.dll"; DestDir: "{app}"; Flags: ignoreversion

; 4. CARPETA DE ICONOS Y FOTOS
; Copiamos todo el contenido recursivamente
Source: "{#BuildDir}\iconos\*"; DestDir: "{app}\iconos"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#BuildDir}\fotos_empleados\*"; DestDir: "{app}\fotos_empleados"; Flags: ignoreversion recursesubdirs createallsubdirs

; 5. CUALQUIER OTRA COSA QUE HAYA QUEDADO EN DIST (Librerías de Python, etc.)
; Excluimos lo que ya copiamos explícitamente para no duplicar trabajo, aunque Inno es listo.
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "\iconos,\fotos_empleados,sistema_rrhh_full.db,config.json,HCNetSDK.dll,{#MyAppExeName}"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Ejecutar al terminar la instalación
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent