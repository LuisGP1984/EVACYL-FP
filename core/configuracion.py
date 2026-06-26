"""
Configuración persistente muy simple de la aplicación: de momento, solo
recuerda la ruta de la carpeta general del docente entre ejecuciones,
para no tener que volver a seleccionarla cada vez que se abre la app.

Se guarda en la carpeta de datos del usuario del sistema operativo (en
Windows, dentro de %APPDATA%\\EVACYL_FP), independiente de la carpeta de EVACYL (LOMLOE),, no junto al
propio programa: si la app está instalada en "Archivos de programa", el
usuario normal no tiene permiso de escritura ahí, así que guardar la
configuración junto al ejecutable fallaría en una instalación real.
"""

from __future__ import annotations

import os
from pathlib import Path

NOMBRE_CARPETA_CONFIG = "EVACYL_FP"
NOMBRE_ARCHIVO_CONFIG = "config_app.txt"


def _carpeta_datos_usuario() -> Path:
    """Carpeta de datos de aplicación del usuario actual, multiplataforma:
    %APPDATA% en Windows, ~/.config en Linux/macOS si APPDATA no existe.
    """
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / NOMBRE_CARPETA_CONFIG


RUTA_ARCHIVO_CONFIG = _carpeta_datos_usuario() / NOMBRE_ARCHIVO_CONFIG


def leer_carpeta_docente() -> Path | None:
    """Devuelve la última carpeta de docente guardada, o None si no hay
    ninguna guardada o la carpeta ya no existe en disco.
    """
    if not RUTA_ARCHIVO_CONFIG.exists():
        return None
    try:
        texto = RUTA_ARCHIVO_CONFIG.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not texto:
        return None
    ruta = Path(texto)
    return ruta if ruta.exists() and ruta.is_dir() else None


def guardar_carpeta_docente(ruta: str | Path) -> None:
    try:
        RUTA_ARCHIVO_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        RUTA_ARCHIVO_CONFIG.write_text(str(ruta), encoding="utf-8")
    except OSError:
        pass  # si no se puede guardar, simplemente se volverá a preguntar la próxima vez
