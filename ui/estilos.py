"""
Estilos visuales de EVACYL FP: paleta roja-naranja-amarilla (la identidad
visual de este proyecto, hermano de EVACYL pero pensado para Formación
Profesional) aplicada de forma centralizada con una hoja de estilos Qt
(QSS, parecido a CSS).

A diferencia de EVACYL (que siempre tiene exactamente 6 pestañas fijas:
Alumnos, Criterios, 1EVA, 2EVA, 3EVA, FINAL), en EVACYL FP el número de
evaluaciones parciales de un módulo es configurable por el docente al
crearlo. Por eso el color de cada pestaña de evaluación no se busca en
una lista fija, sino que se genera interpolando entre el rojo y el
amarillo según la posición de esa evaluación entre todas las que tenga
el módulo (ver color_pestana_evaluacion()).
"""

from __future__ import annotations

PALETA = {
    "rojo_muy_oscuro": "#2B0A03",
    "rojo_oscuro": "#7A1B08",
    "rojo_medio": "#E22B10",
    "naranja": "#E68415",
    "amarillo": "#F2C817",
    "naranja_claro": "#F6CFA0",
    "naranja_muy_claro": "#FDF3E7",
    "blanco": "#FFFFFF",
    "gris_texto_atenuado": "#8A7A6E",
    "acento_frio": "#0D1F4D",
    "acento_frio_claro": "#E4E9F5",
}

COLOR_COLUMNA_IDENTIDAD = "#FBE3D6"
COLOR_COLUMNA_DATOS = "#FFFFFF"
COLOR_COLUMNA_RESULTADO = "#FBD9A8"

COLOR_CABECERA_IDENTIDAD = "#E22B10"
COLOR_CABECERA_DATOS = "#E68415"
COLOR_CABECERA_RESULTADO = "#7A1B08"

COLOR_CABECERA_IDENTIDAD_GRIS = "#8C7B6E"
COLOR_CABECERA_DATOS_NARANJA = "#E68415"
COLOR_CABECERA_CRITERIO_ROJO = "#E22B10"
COLOR_CELDA_IDENTIDAD_GRIS_CLARO = "#EEE7E1"


def color_pestana_evaluacion(indice: int, total: int) -> str:
    """Genera un color interpolado entre rojo y amarillo para la
    evaluación de posición "indice" (0-based) sobre un total de
    evaluaciones parciales.
    """
    if total <= 1:
        t = 0.0
    else:
        t = indice / (total - 1)
    rojo = (0xE2, 0x2B, 0x10)
    amarillo = (0xF2, 0xC8, 0x17)
    r = round(rojo[0] + (amarillo[0] - rojo[0]) * t)
    g = round(rojo[1] + (amarillo[1] - rojo[1]) * t)
    b = round(rojo[2] + (amarillo[2] - rojo[2]) * t)
    return f"#{r:02X}{g:02X}{b:02X}"


COLOR_PESTANA_ALUMNOS = "#B5443A"
COLOR_PESTANA_RA = "#C9622A"
COLOR_PESTANA_FINAL = "#7A1B08"


HOJA_ESTILOS = f"""
QWidget {{
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    color: #2B1B12;
}}

QMainWindow {{
    background-color: {PALETA['naranja_muy_claro']};
}}

QLabel#titulo {{
    font-size: 22px;
    font-weight: bold;
    color: {PALETA['rojo_oscuro']};
}}

QLabel#subtitulo {{
    font-size: 16px;
    font-weight: 600;
    color: {PALETA['rojo_medio']};
}}

QWidget#panelSobreFondo {{
    background-color: rgba(255, 255, 255, 235);
    border-radius: 14px;
}}

QWidget#fondoTransparente {{
    background-color: transparent;
}}

QPushButton {{
    background-color: {PALETA['rojo_medio']};
    color: {PALETA['blanco']};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {PALETA['rojo_oscuro']};
}}

QPushButton:pressed {{
    background-color: {PALETA['rojo_muy_oscuro']};
}}

QPushButton#botonSecundario {{
    background-color: {PALETA['blanco']};
    color: {PALETA['rojo_medio']};
    border: 1px solid {PALETA['rojo_medio']};
}}

QPushButton#botonSecundario:hover {{
    background-color: {PALETA['naranja_claro']};
}}

QPushButton#botonPeligro {{
    background-color: {PALETA['blanco']};
    color: #B23B3B;
    border: 1px solid #B23B3B;
}}

QPushButton#botonPeligro:hover {{
    background-color: #FBEAEA;
}}

QPushButton#botonAyuda {{
    background-color: {PALETA['acento_frio_claro']};
    color: {PALETA['acento_frio']};
    border: 1px solid {PALETA['acento_frio']};
    border-radius: 14px;
    padding: 4px 12px;
    font-weight: 600;
}}

QPushButton#botonAyuda:hover {{
    background-color: {PALETA['acento_frio']};
    color: {PALETA['blanco']};
}}

QPushButton#botonSeccionPlegable {{
    background-color: {PALETA['naranja_muy_claro']};
    color: {PALETA['rojo_oscuro']};
    border: 1px solid {PALETA['naranja_claro']};
    border-radius: 6px;
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
}}

QPushButton#botonSeccionPlegable:hover {{
    background-color: {PALETA['naranja_claro']};
}}

QTableWidget {{
    background-color: {PALETA['blanco']};
    alternate-background-color: {PALETA['naranja_muy_claro']};
    gridline-color: {PALETA['naranja_claro']};
    border: 1px solid {PALETA['naranja_claro']};
    border-radius: 4px;
}}

QHeaderView::section {{
    background-color: {PALETA['rojo_medio']};
    color: {PALETA['blanco']};
    padding: 6px;
    border: none;
    font-weight: bold;
}}

QTabWidget::pane {{
    border: 1px solid {PALETA['naranja_claro']};
    border-radius: 4px;
    background-color: {PALETA['naranja_muy_claro']};
}}

QTabBar::tab {{
    background-color: {PALETA['naranja_claro']};
    color: {PALETA['rojo_muy_oscuro']};
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {PALETA['rojo_medio']};
    color: {PALETA['blanco']};
    font-weight: bold;
}}

QListWidget {{
    background-color: {PALETA['blanco']};
    border: 1px solid {PALETA['naranja_claro']};
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {PALETA['rojo_medio']};
    color: {PALETA['blanco']};
}}

QLineEdit, QInputDialog QLineEdit {{
    background-color: {PALETA['blanco']};
    border: 1px solid {PALETA['naranja_claro']};
    border-radius: 4px;
    padding: 4px;
}}
"""


def hoja_estilos_pestanas_modulo(numero_evaluaciones_parciales: int) -> str:
    """Genera el QSS para colorear cada pestaña fija de un módulo:
    Alumnos, RA y Criterios, las N evaluaciones parciales (con color
    interpolado rojo->amarillo según su posición) y FINAL.
    """
    colores = [COLOR_PESTANA_ALUMNOS, COLOR_PESTANA_RA]
    for indice in range(numero_evaluaciones_parciales):
        colores.append(color_pestana_evaluacion(indice, numero_evaluaciones_parciales))
    colores.append(COLOR_PESTANA_FINAL)

    reglas = []
    for indice, color in enumerate(colores):
        reglas.append(
            f"QTabBar::tab:nth-child({indice + 1}) {{ background-color: {color}; "
            f"color: {PALETA['blanco']}; }}"
        )
    return "\n".join(reglas)
