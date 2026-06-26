; Script de Inno Setup para "EVACYL FP".
;
; Qué hace: toma la carpeta que genera PyInstaller en dist\EVACYL_FP y
; construye un instalador .exe normal de Windows: con asistente de
; instalación, icono propio, acceso directo en el menú de inicio y en el
; escritorio (opcional), y un desinstalador que aparece en
; "Aplicaciones y características" de Windows.
;
; Uso: abrir este archivo con Inno Setup (botón derecho -> Compile, o
; Ctrl+F9 dentro del programa). El instalador resultante queda en la
; carpeta "instalador_salida" junto a este script.
;
; IMPORTANTE: este script asume que ya se ha ejecutado antes
;   pyinstaller empaquetado.spec
; y que por tanto existe la carpeta dist\EVACYL_FP con el ejecutable y
; todos sus archivos dentro.
;
; NOTA sobre el AppId: es un identificador único distinto del de EVACYL
; (el proyecto hermano para Primaria/Secundaria/Bachillerato), a
; propósito: así Windows trata ambas aplicaciones como completamente
; independientes (instalación, actualización y desinstalación de una no
; afectan a la otra), aunque se instalen en el mismo ordenador.

#define MiApp "EVACYL FP"
#define MiVersion "1.0"
#define MiAutor "Luis González Posada"
#define MiCarpetaDist "dist\EVACYL_FP"

[Setup]
AppId={{E466B26C-DABD-49ED-8148-851BFA8F35AB}
AppName={#MiApp}
AppVersion={#MiVersion}
AppPublisher={#MiAutor}
DefaultDirName={autopf}\{#MiApp}
DefaultGroupName={#MiApp}
DisableProgramGroupPage=yes
OutputDir=instalador_salida
OutputBaseFilename=Instalador_EVACYL_FP
Compression=lzma
SolidCompression=yes
SetupIconFile=recursos\icono_app.ico
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "{#MiCarpetaDist}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MiApp}"; Filename: "{app}\EVACYL_FP.exe"
Name: "{group}\Desinstalar {#MiApp}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MiApp}"; Filename: "{app}\EVACYL_FP.exe"; Tasks: escritorio

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Accesos directos adicionales:"

[Run]
Filename: "{app}\EVACYL_FP.exe"; Description: "Abrir {#MiApp} ahora"; Flags: nowait postinstall skipifsilent
