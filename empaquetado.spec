# -*- mode: python ; coding: utf-8 -*-
#
# Archivo de configuración de PyInstaller para "EVACYL FP". Incluye
# automáticamente las carpetas recursos/ (imagen de fondo, logo, icono)
# y datos_curriculares/ dentro del ejecutable, para que funcione igual
# en cualquier ordenador sin necesitar esos archivos sueltos al lado.
#
# Uso (desde la carpeta del proyecto, en Windows, con el entorno ya
# preparado: pip install -r requirements.txt y además pyinstaller):
#
#   pyinstaller empaquetado.spec
#
# El resultado queda en dist\EVACYL_FP\

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('recursos', 'recursos'),
        ('datos_curriculares', 'datos_curriculares'),
    ],
    hiddenimports=[
        # reportlab y python-docx cargan algunos submódulos de forma
        # dinámica; se declaran explícitamente para que PyInstaller no
        # los deje fuera del .exe (causaría un error solo al generar
        # un informe, no al simplemente abrir la aplicación).
        'reportlab.pdfbase._fontdata',
        'reportlab.graphics.barcode',
        'docx',
        'docx.oxml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EVACYL_FP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='recursos/icono_app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EVACYL_FP',
)
