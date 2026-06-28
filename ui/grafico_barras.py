"""
Widget de gráfico de barras simple, dibujado a mano con QPainter (sin
depender de QtCharts ni de ninguna librería externa, para no arriesgar
una dependencia que pudiera no estar disponible).

Soporta dos modos:
  - Un solo alumno: una barra por instrumento/evaluación, coloreada con
    el degradado rojo-verde según la nota (establecer_datos).
  - Varios alumnos agrupados: por cada instrumento/evaluación, un grupo
    de barras, una por alumno, para comparar a todo el grupo de un
    vistazo (establecer_datos_agrupados). Cada alumno tiene un color de
    contorno fijo (para identificarlo en todos los grupos), y el
    relleno sigue el degradado rojo-verde según su nota.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from core.calificacion import color_hex_nota

# Paleta de colores de contorno para distinguir alumnos en el modo
# agrupado (se repite cíclicamente si hay más alumnos que colores).
_COLORES_ALUMNOS = [
    "#0F6FB9", "#0DAB6C", "#E8A33D", "#9B59B6", "#E74C3C",
    "#1ABC9C", "#34495E", "#D35400", "#2980B9", "#27AE60",
]


class GraficoBarras(QWidget):
    """Gráfico de barras verticales, escala fija 0-10. Usar
    establecer_datos() para una sola serie (un alumno), o
    establecer_datos_agrupados() para varias series (varios alumnos).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        self._etiquetas: list[str] = []
        self._valores: list[float | None] = []
        self._titulo = ""
        self._modo_agrupado = False
        self._nombres_series: list[str] = []
        self._valores_por_serie: list[list[float | None]] = []

    def establecer_datos(self, etiquetas: list[str], valores: list[float | None], titulo: str = ""):
        """Modo de un solo alumno: etiquetas y valores deben tener la
        misma longitud. Un valor None se dibuja como barra vacía con un
        aviso de "sin nota".
        """
        self._modo_agrupado = False
        self._etiquetas = etiquetas
        self._valores = valores
        self._titulo = titulo
        self.update()

    def establecer_datos_agrupados(
        self,
        etiquetas: list[str],
        nombres_series: list[str],
        valores_por_serie: list[list[float | None]],
        titulo: str = "",
    ):
        """Modo de varios alumnos agrupados: etiquetas son los grupos
        (instrumentos o evaluaciones); nombres_series son los alumnos;
        valores_por_serie[i] es la lista de valores del alumno i, uno
        por etiqueta (misma longitud que etiquetas).
        """
        self._modo_agrupado = True
        self._etiquetas = etiquetas
        self._nombres_series = nombres_series
        self._valores_por_serie = valores_por_serie
        self._titulo = titulo
        self.update()

    def paintEvent(self, evento):  # noqa: N802 - nombre impuesto por Qt
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        ancho_total = self.width()
        alto_total = self.height()

        margen_izquierdo = 38
        margen_derecho = 16
        margen_superior = 36 if self._titulo else 16
        margen_inferior = 46
        margen_inferior_leyenda = 26 if self._modo_agrupado and self._nombres_series else 0

        area = QRectF(
            margen_izquierdo,
            margen_superior,
            ancho_total - margen_izquierdo - margen_derecho,
            alto_total - margen_superior - margen_inferior - margen_inferior_leyenda,
        )

        # -- título --
        if self._titulo:
            painter.setPen(QColor("#0D3D6B"))
            fuente_titulo = QFont()
            fuente_titulo.setBold(True)
            fuente_titulo.setPointSize(11)
            painter.setFont(fuente_titulo)
            painter.drawText(
                QRectF(0, 6, ancho_total, 24), Qt.AlignmentFlag.AlignCenter, self._titulo
            )

        if not self._etiquetas:
            painter.setPen(QColor("#7E96A8"))
            painter.drawText(area, Qt.AlignmentFlag.AlignCenter, "Sin datos para mostrar")
            return

        # -- líneas guía horizontales (0, 5, 10) y sus etiquetas --
        painter.setPen(QPen(QColor("#D7E3EA"), 1))
        fuente_ejes = QFont()
        fuente_ejes.setPointSize(8)
        painter.setFont(fuente_ejes)
        for valor_guia in (0, 2.5, 5, 7.5, 10):
            y = area.bottom() - (valor_guia / 10.0) * area.height()
            painter.drawLine(int(area.left()), int(y), int(area.right()), int(y))
            painter.setPen(QColor("#5B6B82"))
            painter.drawText(
                QRectF(0, y - 8, margen_izquierdo - 6, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{valor_guia:g}",
            )
            painter.setPen(QPen(QColor("#D7E3EA"), 1))

        fuente_etiquetas = QFont()
        fuente_etiquetas.setPointSize(8)
        painter.setFont(fuente_etiquetas)

        if self._modo_agrupado:
            self._dibujar_barras_agrupadas(painter, area)
        else:
            self._dibujar_barras_simples(painter, area)

        # -- leyenda de colores por alumno (solo en modo agrupado) --
        if self._modo_agrupado and self._nombres_series:
            y_leyenda = area.bottom() + margen_inferior + 4
            x_actual = area.left()
            fuente_leyenda = QFont()
            fuente_leyenda.setPointSize(8)
            painter.setFont(fuente_leyenda)
            for indice, nombre in enumerate(self._nombres_series):
                color = QColor(_COLORES_ALUMNOS[indice % len(_COLORES_ALUMNOS)])
                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(QRectF(x_actual, y_leyenda, 10, 10))
                painter.setPen(QColor("#0D3D6B"))
                ancho_texto = painter.fontMetrics().horizontalAdvance(nombre) + 8
                painter.drawText(
                    QRectF(x_actual + 14, y_leyenda - 3, ancho_texto, 16),
                    Qt.AlignmentFlag.AlignVCenter,
                    nombre,
                )
                x_actual += 14 + ancho_texto + 12
                if x_actual > area.right() - 40:
                    x_actual = area.left()
                    y_leyenda += 16

    def _dibujar_barras_simples(self, painter: QPainter, area: QRectF):
        n = len(self._etiquetas)
        ancho_hueco = area.width() / n
        ancho_barra = ancho_hueco * 0.55

        for indice, (etiqueta, valor) in enumerate(zip(self._etiquetas, self._valores)):
            centro_x = area.left() + ancho_hueco * indice + ancho_hueco / 2
            x_barra = centro_x - ancho_barra / 2

            if valor is None:
                rect_vacio = QRectF(x_barra, area.bottom() - 6, ancho_barra, 6)
                painter.setPen(QPen(QColor("#B7C4CE"), 1, Qt.PenStyle.DashLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect_vacio)
            else:
                altura_barra = (max(0.0, min(10.0, valor)) / 10.0) * area.height()
                rect_barra = QRectF(x_barra, area.bottom() - altura_barra, ancho_barra, altura_barra)
                color_hex = color_hex_nota(valor) or "9FD9D0"
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(f"#{color_hex}"))
                painter.drawRoundedRect(rect_barra, 3, 3)

                painter.setPen(QColor("#0D3D6B"))
                texto_valor = f"{valor:.1f}".rstrip("0").rstrip(".")
                painter.drawText(
                    QRectF(x_barra - 10, rect_barra.top() - 16, ancho_barra + 20, 14),
                    Qt.AlignmentFlag.AlignCenter,
                    texto_valor,
                )

            painter.setPen(QColor("#0D3D6B"))
            painter.drawText(
                QRectF(centro_x - ancho_hueco / 2, area.bottom() + 6, ancho_hueco, 36),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                etiqueta,
            )

    def _dibujar_barras_agrupadas(self, painter: QPainter, area: QRectF):
        n_grupos = len(self._etiquetas)
        n_series = len(self._nombres_series)
        if n_series == 0:
            painter.setPen(QColor("#7E96A8"))
            painter.drawText(area, Qt.AlignmentFlag.AlignCenter, "Sin alumnado para mostrar")
            return

        ancho_grupo = area.width() / n_grupos
        ancho_barra = (ancho_grupo * 0.8) / n_series

        for indice_grupo, etiqueta in enumerate(self._etiquetas):
            inicio_grupo = area.left() + ancho_grupo * indice_grupo + ancho_grupo * 0.1

            for indice_serie in range(n_series):
                valor = (
                    self._valores_por_serie[indice_serie][indice_grupo]
                    if indice_grupo < len(self._valores_por_serie[indice_serie])
                    else None
                )
                x_barra = inicio_grupo + ancho_barra * indice_serie
                color_contorno = QColor(_COLORES_ALUMNOS[indice_serie % len(_COLORES_ALUMNOS)])

                if valor is None:
                    rect_vacio = QRectF(x_barra, area.bottom() - 5, max(ancho_barra - 2, 1), 5)
                    painter.setPen(QPen(color_contorno, 1, Qt.PenStyle.DashLine))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRect(rect_vacio)
                else:
                    altura_barra = (max(0.0, min(10.0, valor)) / 10.0) * area.height()
                    rect_barra = QRectF(
                        x_barra, area.bottom() - altura_barra, max(ancho_barra - 2, 1), altura_barra
                    )
                    color_hex = color_hex_nota(valor) or "9FD9D0"
                    painter.setPen(QPen(color_contorno, 2))
                    painter.setBrush(QColor(f"#{color_hex}"))
                    painter.drawRoundedRect(rect_barra, 2, 2)

            painter.setPen(QColor("#0D3D6B"))
            painter.drawText(
                QRectF(area.left() + ancho_grupo * indice_grupo, area.bottom() + 6, ancho_grupo, 36),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                etiqueta,
            )
