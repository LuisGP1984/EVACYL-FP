"""
Panel "📈 Estadísticas" de una evaluación parcial o de FINAL: una tabla
con la media, máxima y mínima de las notas del grupo en cada Resultado
de Aprendizaje (RA), y un gráfico de barras con la nota de cada alumno
en el RA que se elija.

A diferencia de EVACYL (centrado en el desglose cualitativo
IN/SU/BI/NT/SB), aquí se prioriza la nota NUMÉRICA por RA, que es la
unidad de seguimiento principal del profesorado de FP.
"""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.calificacion import color_hex_nota
from core.estadisticas import calcular_estadisticas_por_ra
from ui.grafico_barras import GraficoBarras
from ui.widgets_comunes import BotonAyuda

TEXTO_AYUDA_ESTADISTICAS = (
    "Esta pestaña resume las calificaciones del grupo por Resultado de Aprendizaje:\n\n"
    "• La tabla de arriba muestra, para cada RA, la nota media, la más alta y la más baja "
    "del grupo, junto con cuántos alumnos tienen ya nota en ese RA.\n\n"
    "• El gráfico de abajo muestra la nota de cada alumno en el RA que elijas en el "
    "desplegable. Las barras discontinuas indican que ese alumno todavía no tiene nota "
    "en ese RA."
)


def _formatear(valor: float | None) -> str:
    if valor is None:
        return "—"
    return f"{valor:.2f}".replace(".", ",")


class PanelEstadisticas(QWidget):
    """Panel de estadísticas por RA. Quien lo use debe proporcionar:
      - obtener_ras() -> list[ResultadoAprendizaje]
      - obtener_notas_ra() -> {(ra_id, alumno_id): nota|None}
      - obtener_lista_alumnos() -> [(alumno_id, etiqueta), ...]
    """

    def __init__(
        self,
        titulo: str,
        obtener_ras,
        obtener_notas_ra,
        obtener_lista_alumnos,
    ):
        super().__init__()
        self._obtener_ras = obtener_ras
        self._obtener_notas_ra = obtener_notas_ra
        self._obtener_lista_alumnos = obtener_lista_alumnos

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        fila_titulo = QHBoxLayout()
        etiqueta_titulo = QLabel(titulo)
        etiqueta_titulo.setObjectName("subtitulo")
        fila_titulo.addWidget(etiqueta_titulo)
        fila_titulo.addStretch()
        fila_titulo.addWidget(BotonAyuda("Ayuda — Estadísticas", TEXTO_AYUDA_ESTADISTICAS))
        layout.addLayout(fila_titulo)

        self.tabla_resumen = QTableWidget()
        self.tabla_resumen.setColumnCount(5)
        self.tabla_resumen.setHorizontalHeaderLabels(["RA", "Media", "Máxima", "Mínima", "Con nota"])
        self.tabla_resumen.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_resumen.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_resumen.setMaximumHeight(220)
        layout.addWidget(self.tabla_resumen)

        fila_selector = QHBoxLayout()
        fila_selector.addWidget(QLabel("Ver notas de cada alumno en:"))
        self.combo_ra = QComboBox()
        self.combo_ra.currentIndexChanged.connect(self._actualizar_grafico)
        fila_selector.addWidget(self.combo_ra)
        fila_selector.addStretch()
        layout.addLayout(fila_selector)

        self.grafico = GraficoBarras()
        layout.addWidget(self.grafico)

        self.refrescar()

    def refrescar(self):
        ras = self._obtener_ras()
        notas_ra = self._obtener_notas_ra()
        lista_alumnos = self._obtener_lista_alumnos()
        ids_alumnos = [alumno_id for alumno_id, _etiqueta in lista_alumnos]

        estadisticas = calcular_estadisticas_por_ra(ras, notas_ra, ids_alumnos)

        self.tabla_resumen.setRowCount(len(estadisticas))
        for fila, estadistica in enumerate(estadisticas):
            item_ra = QTableWidgetItem(f"RA{estadistica.numero_ra}")
            item_media = QTableWidgetItem(_formatear(estadistica.media))
            item_maxima = QTableWidgetItem(_formatear(estadistica.maxima))
            item_minima = QTableWidgetItem(_formatear(estadistica.minima))
            item_con_nota = QTableWidgetItem(
                f"{estadistica.total_con_nota} / {estadistica.total_con_nota + estadistica.total_sin_nota}"
            )
            if estadistica.media is not None:
                color_hex = color_hex_nota(estadistica.media)
                if color_hex:
                    color = QColor(f"#{color_hex}")
                    item_media.setBackground(color)
            self.tabla_resumen.setItem(fila, 0, item_ra)
            self.tabla_resumen.setItem(fila, 1, item_media)
            self.tabla_resumen.setItem(fila, 2, item_maxima)
            self.tabla_resumen.setItem(fila, 3, item_minima)
            self.tabla_resumen.setItem(fila, 4, item_con_nota)

        seleccion_actual = self.combo_ra.currentData()
        self.combo_ra.blockSignals(True)
        self.combo_ra.clear()
        for ra in ras:
            self.combo_ra.addItem(f"RA{ra.numero}" + (f" — {ra.descripcion}" if ra.descripcion else ""), ra.id)
        if seleccion_actual is not None:
            indice = self.combo_ra.findData(seleccion_actual)
            if indice >= 0:
                self.combo_ra.setCurrentIndex(indice)
        self.combo_ra.blockSignals(False)

        self._ras_actuales = ras
        self._notas_ra_actuales = notas_ra
        self._lista_alumnos_actual = lista_alumnos

        self._actualizar_grafico()

    def _actualizar_grafico(self, _indice: int = -1):
        ra_id = self.combo_ra.currentData()
        if ra_id is None or not hasattr(self, "_lista_alumnos_actual"):
            self.grafico.establecer_datos([], [], "")
            return

        ra_seleccionado = next((ra for ra in self._ras_actuales if ra.id == ra_id), None)
        if ra_seleccionado is None:
            self.grafico.establecer_datos([], [], "")
            return

        etiquetas = []
        valores = []
        for alumno_id, etiqueta in self._lista_alumnos_actual:
            etiquetas.append(etiqueta)
            valores.append(self._notas_ra_actuales.get((ra_id, alumno_id)))

        self.grafico.establecer_datos(etiquetas, valores, f"Notas de todo el alumnado en RA{ra_seleccionado.numero}")
