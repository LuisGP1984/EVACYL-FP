"""
Copias de seguridad automáticas de curso.db.

Cada vez que se abre un curso, se guarda una copia con marca de fecha y
hora en una subcarpeta "copias_seguridad" junto al propio curso.db, antes
de tocar nada. Así, si el archivo se corrompe durante la sesión (un
corte de luz, un USB que se desconecta a medio guardar...), siempre hay
una versión reciente y sana a la que volver.

Para no acumular copias indefinidamente, se conservan solo las N más
recientes (por defecto 15): cada vez que se crea una copia nueva, se
borran las más antiguas que sobrepasen ese límite.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

NOMBRE_CARPETA_COPIAS = "copias_seguridad"
MAXIMO_COPIAS_POR_CURSO = 15


def crear_copia_seguridad(ruta_curso_db: str | Path) -> Path | None:
    """Copia el curso.db indicado a su subcarpeta de copias de seguridad,
    con un nombre que incluye fecha y hora. Devuelve la ruta de la copia
    creada, o None si no se pudo crear (por ejemplo, por falta de
    permisos) — un fallo aquí no debe impedir que el docente trabaje, así
    que los errores se ignoran silenciosamente y simplemente no habrá
    copia esta vez.
    """
    ruta_curso_db = Path(ruta_curso_db)
    if not ruta_curso_db.exists():
        return None

    carpeta_copias = ruta_curso_db.parent / NOMBRE_CARPETA_COPIAS
    try:
        carpeta_copias.mkdir(exist_ok=True)
        marca_tiempo = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        ruta_copia = carpeta_copias / f"curso_{marca_tiempo}.db"
        shutil.copy2(ruta_curso_db, ruta_copia)
        _purgar_copias_antiguas(carpeta_copias)
        return ruta_copia
    except OSError:
        return None


def _purgar_copias_antiguas(carpeta_copias: Path, maximo: int = MAXIMO_COPIAS_POR_CURSO):
    try:
        copias = sorted(carpeta_copias.glob("curso_*.db"), key=lambda p: p.name)
    except OSError:
        return
    sobrantes = len(copias) - maximo
    if sobrantes <= 0:
        return
    for copia_antigua in copias[:sobrantes]:
        try:
            copia_antigua.unlink()
        except OSError:
            pass  # si no se puede borrar una copia vieja, no es crítico


def listar_copias_seguridad(ruta_curso_db: str | Path) -> list[Path]:
    """Devuelve las copias de seguridad existentes para un curso.db,
    de la más reciente a la más antigua.
    """
    ruta_curso_db = Path(ruta_curso_db)
    carpeta_copias = ruta_curso_db.parent / NOMBRE_CARPETA_COPIAS
    if not carpeta_copias.exists():
        return []
    return sorted(carpeta_copias.glob("curso_*.db"), key=lambda p: p.name, reverse=True)


def restaurar_copia_seguridad(ruta_copia: str | Path, ruta_curso_db: str | Path) -> bool:
    """Sustituye curso.db por el contenido de una copia de seguridad
    elegida. Antes de sobrescribir, guarda el curso.db actual como una
    copia de seguridad más (por si la restauración fuera un error y haya
    que volver atrás). Devuelve True si todo fue bien.
    """
    ruta_copia = Path(ruta_copia)
    ruta_curso_db = Path(ruta_curso_db)
    if not ruta_copia.exists():
        return False
    try:
        crear_copia_seguridad(ruta_curso_db)  # conserva el estado actual antes de sobrescribir
        shutil.copy2(ruta_copia, ruta_curso_db)
        return True
    except OSError:
        return False
