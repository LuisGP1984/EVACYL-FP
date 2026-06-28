"""
Widget "🩺 Estado de la evaluación": muestra de un vistazo todas las
incidencias detectadas (pesos sin sumar 100%, instrumentos sin
criterios, alumnado sin nota...) al entrar en una evaluación parcial o
en FINAL. Pensado para no tener que descubrir estos problemas poco a
poco, navegando por cada pestaña.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.salud_modulo import IncidenciaSalud, SEVERIDAD_ERROR

COLOR_FONDO_OK = "#D7F2E3"
COLOR_TEXTO_OK = "#0D6B3F"
COLOR_FONDO_AVISO = "#FDF3E7"
COLOR_TEXTO_AVISO = "#7A1B08"
COLOR_FONDO_ERROR = "#FBE3D6"
COLOR_TEXTO_ERROR = "#7A1B08"
COLOR_BORDE_ERROR = "#E22B10"
COLOR_BORDE_AVISO = "#E68415"


class PanelSaludEvaluacion(QWidget):
    """Lista compacta de incidencias. Llamar a actualizar(incidencias)
    cada vez que se quiera refrescar (normalmente al entrar en la
    pestaña, o tras cualquier cambio relevante).
    """

    def __init__(self):
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 8)
        self._layout.setSpacing(6)
        self._etiquetas: list[QLabel] = []

    def actualizar(self, incidencias: list[IncidenciaSalud]):
        for etiqueta in self._etiquetas:
            etiqueta.deleteLater()
        self._etiquetas.clear()

        if not incidencias:
            etiqueta = QLabel("✅ Todo correcto: no se ha detectado ninguna incidencia en esta evaluación.")
            etiqueta.setWordWrap(True)
            etiqueta.setStyleSheet(
                f"background-color: {COLOR_FONDO_OK}; color: {COLOR_TEXTO_OK}; "
                "border-radius: 6px; padding: 8px;"
            )
            self._layout.addWidget(etiqueta)
            self._etiquetas.append(etiqueta)
            return

        for incidencia in incidencias:
            if incidencia.severidad == SEVERIDAD_ERROR:
                icono = "🛑"
                color_fondo = COLOR_FONDO_ERROR
                color_texto = COLOR_TEXTO_ERROR
                color_borde = COLOR_BORDE_ERROR
            else:
                icono = "⚠️"
                color_fondo = COLOR_FONDO_AVISO
                color_texto = COLOR_TEXTO_AVISO
                color_borde = COLOR_BORDE_AVISO

            etiqueta = QLabel(f"{icono} {incidencia.mensaje}")
            etiqueta.setWordWrap(True)
            etiqueta.setStyleSheet(
                f"background-color: {color_fondo}; color: {color_texto}; "
                f"border-left: 4px solid {color_borde}; border-radius: 6px; padding: 8px;"
            )
            self._layout.addWidget(etiqueta)
            self._etiquetas.append(etiqueta)
