"""
Resolución de rutas a la carpeta raíz del proyecto, compatible tanto con
la ejecución normal (python main.py) como con la aplicación ya empaquetada
con PyInstaller.

Por qué hace falta esto: cuando PyInstaller empaqueta la app, el atributo
__file__ de los módulos deja de apuntar a una ruta útil (apunta a una
carpeta temporal de extracción), así que Path(__file__).parent ya no
sirve para encontrar recursos/ o datos_curriculares/.

Además, en el modo --onedir que usa este proyecto (ver empaquetado.spec,
con COLLECT), los datos NO quedan junto al .exe sino dentro de una
subcarpeta "_internal" (en versiones recientes de PyInstaller) o
directamente junto al .exe (en versiones antiguas). PyInstaller expone
esa ubicación real de los datos en el atributo sys._MEIPASS, que es la
forma oficial y fiable de encontrarlos, en vez de calcularla a mano a
partir de sys.executable.
"""

from __future__ import annotations

import sys
from pathlib import Path


def ruta_raiz_proyecto() -> Path:
    """Carpeta desde la que se deben resolver recursos/ y
    datos_curriculares/. (El archivo de configuración del usuario usa su
    propia ubicación en core/configuracion.py, no esta función).
    """
    if getattr(sys, "frozen", False):
        # Empaquetado con PyInstaller: sys._MEIPASS es la carpeta donde
        # PyInstaller ha colocado de verdad los datos incluidos vía
        # COLLECT/datas (sea "_internal" en modo --onedir reciente, o la
        # carpeta de extracción temporal en modo --onefile).
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    # Ejecución normal: este archivo vive en core/, así que subimos un nivel.
    return Path(__file__).resolve().parent.parent
