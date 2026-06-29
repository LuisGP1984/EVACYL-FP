"""
Panel "🔗 Trazabilidad": muestra en pantalla, sin necesitar exportar a
Excel, qué instrumento de evaluación evalúa cada criterio (en una
evaluación parcial) o en qué evaluación parcial se evaluó cada
criterio (en FINAL). Usa las mismas funciones de cálculo que la
exportación a Excel, así que siempre coincide con lo que se ve en el
archivo exportado.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.database import BaseDatosModulo, Evaluacion, Modulo
from ui.widgets_comunes import BotonAyuda

COLOR_SI = QColor("#FBD9C8")
COLOR_NO = QColor("#F2F2F2")

TEXTO_AYUDA_TRAZABILIDAD_EVALUACION = (
    "Esta tabla muestra, para cada criterio (filas) y cada instrumento de evaluación de "
    "esta evaluación parcial (columnas), si ese instrumento evalúa ese criterio y con qué "
    "peso.\n\n"
    "El peso se calcula automáticamente: es el peso del criterio en su RA, redistribuido "
    "entre los criterios de ese mismo RA marcados en ese instrumento. No se puede editar a "
    "mano.\n\n"
    "Es la misma información que aparece en la hoja «Criterios» del Excel exportado, pero "
    "aquí la puedes consultar directamente sin tener que exportar nada."
)

TEXTO_AYUDA_TRAZABILIDAD_FINAL = (
    "Esta tabla muestra, para cada criterio (filas) y cada evaluación parcial (columnas), "
    "si ese criterio tuvo alguna nota calculada en esa evaluación. La última columna "
    "cuenta en cuántas evaluaciones se trabajó cada criterio."
)


class PanelTrazabilidadEvaluacion(QWidget):
    """Trazabilidad criterio <-> instrumento, para una evaluación parcial."""

    def __init__(self, base_datos: BaseDatosModulo, modulo: Modulo, evaluacion: Evaluacion):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo
        self.evaluacion = evaluacion

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        fila_titulo = QHBoxLayout()
        titulo = QLabel("🔗 Trazabilidad: criterio ↔ instrumento")
        titulo.setObjectName("subtitulo")
        fila_titulo.addWidget(titulo)
        fila_titulo.addStretch()
        fila_titulo.addWidget(BotonAyuda("Ayuda — Trazabilidad", TEXTO_AYUDA_TRAZABILIDAD_EVALUACION))
        layout.addLayout(fila_titulo)

        self.tabla = QTableWidget()
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

        self.refrescar()

    def refrescar(self):
        criterios_con_ra, instrumentos, pesos = self.base_datos.trazabilidad_criterios_instrumentos(
            self.evaluacion.id, self.modulo.id
        )

        encabezados = ["Criterio"] + [instrumento.nombre for instrumento in instrumentos]
        self.tabla.setColumnCount(len(encabezados))
        self.tabla.setHorizontalHeaderLabels(encabezados)
        self.tabla.setRowCount(len(criterios_con_ra))

        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(0, 90)
        for col in range(1, len(encabezados)):
            cabecera.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        for fila, (ra, criterio) in enumerate(criterios_con_ra):
            codigo = self.base_datos.codigo_criterio(ra, criterio)
            item_criterio = QTableWidgetItem(codigo)
            self.tabla.setItem(fila, 0, item_criterio)
            for col, instrumento in enumerate(instrumentos, start=1):
                peso = pesos.get((criterio.id, instrumento.id))
                if peso is None:
                    item = QTableWidgetItem("No")
                    item.setBackground(COLOR_NO)
                else:
                    item = QTableWidgetItem(f"Sí ({peso:.1f}%)")
                    item.setBackground(COLOR_SI)
                self.tabla.setItem(fila, col, item)

    def showEvent(self, event: QShowEvent):
        """Cada vez que este panel pasa a mostrarse en pantalla (al
        entrar a la sub-pestaña Trazabilidad), se vuelve a leer la
        base de datos. Esto es más fiable que depender únicamente de
        la señal currentChanged del QTabWidget padre, que en algún
        caso límite podría no dispararse y dejar la tabla con un
        snapshot desactualizado de la última vez que se vio.
        """
        super().showEvent(event)
        self.refrescar()


class PanelTrazabilidadFinal(QWidget):
    """Trazabilidad criterio <-> evaluación parcial, para FINAL."""

    def __init__(self, base_datos: BaseDatosModulo, modulo: Modulo):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        fila_titulo = QHBoxLayout()
        titulo = QLabel("🔗 Trazabilidad: criterio ↔ evaluación")
        titulo.setObjectName("subtitulo")
        fila_titulo.addWidget(titulo)
        fila_titulo.addStretch()
        fila_titulo.addWidget(BotonAyuda("Ayuda — Trazabilidad", TEXTO_AYUDA_TRAZABILIDAD_FINAL))
        layout.addLayout(fila_titulo)

        self.tabla = QTableWidget()
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

        self.refrescar()

    def refrescar(self):
        criterios_con_ra, evaluaciones, evaluado = self.base_datos.trazabilidad_criterios_evaluaciones(
            self.modulo.id
        )

        encabezados = ["Criterio"] + [ev.nombre for ev in evaluaciones] + ["Nº evaluaciones"]
        self.tabla.setColumnCount(len(encabezados))
        self.tabla.setHorizontalHeaderLabels(encabezados)
        self.tabla.setRowCount(len(criterios_con_ra))

        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(0, 90)
        for col in range(1, len(encabezados)):
            cabecera.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        for fila, (ra, criterio) in enumerate(criterios_con_ra):
            codigo = self.base_datos.codigo_criterio(ra, criterio)
            item_criterio = QTableWidgetItem(codigo)
            self.tabla.setItem(fila, 0, item_criterio)
            contador = 0
            for col, evaluacion in enumerate(evaluaciones, start=1):
                evaluado_aqui = evaluado.get((criterio.id, evaluacion.id), False)
                if evaluado_aqui:
                    contador += 1
                item = QTableWidgetItem("Sí" if evaluado_aqui else "No")
                item.setBackground(COLOR_SI if evaluado_aqui else COLOR_NO)
                self.tabla.setItem(fila, col, item)
            col_contador = len(evaluaciones) + 1
            item_contador = QTableWidgetItem(str(contador))
            fuente = item_contador.font()
            fuente.setBold(True)
            item_contador.setFont(fuente)
            self.tabla.setItem(fila, col_contador, item_contador)

    def showEvent(self, event: QShowEvent):
        """Mismo motivo que en PanelTrazabilidadEvaluacion: refrescar
        al mostrarse es más fiable que depender solo de currentChanged.
        """
        super().showEvent(event)
        self.refrescar()
