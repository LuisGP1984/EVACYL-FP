"""
Panel "Evaluaciones" de la pestaña FINAL. FINAL no tiene instrumentos
propios: usa las evaluaciones parciales del módulo como si fueran
instrumentos, cada una con un peso editable (por defecto igual entre
todas). El cálculo se redistribuye dinámicamente entre las evaluaciones
que sí tienen nota para cada alumno y criterio.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.database import BaseDatosModulo, Modulo
from ui.widgets_comunes import TablaConBorrado

ICONOS_NUMERICOS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]


class PanelEvaluacionesFinal(QWidget):
    COLUMNAS = ["Evaluación", "Peso"]

    def __init__(self, base_datos: BaseDatosModulo, modulo: Modulo):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo
        self._actualizando_desde_codigo = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        titulo = QLabel("⚖️ Evaluaciones que componen la nota FINAL")
        titulo.setObjectName("subtitulo")
        layout.addWidget(titulo)

        ayuda = QLabel(
            "Por defecto, todas las evaluaciones parciales de este módulo pesan lo mismo "
            "(media simple). Puedes cambiar estos pesos, por ejemplo para dar más "
            "importancia a la evaluación más reciente (evaluación continua). Si para un "
            "criterio concreto algún alumno solo tiene nota en una de las evaluaciones, esa "
            "evaluación se queda automáticamente con el 100% del peso para ese criterio "
            "(redistribución dinámica, igual que con los instrumentos de evaluación normales)."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color: #8A7A6E;")
        layout.addWidget(ayuda)

        self.tabla = TablaConBorrado()
        self.tabla.setColumnCount(len(self.COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(self.COLUMNAS)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.itemChanged.connect(self._al_cambiar_celda)
        layout.addWidget(self.tabla)

        layout.addStretch()

        self.refrescar()

    def refrescar(self):
        self._actualizando_desde_codigo = True
        evaluaciones = self.base_datos.listar_evaluaciones_parciales(self.modulo.id)
        pesos = self.base_datos.obtener_pesos_evaluaciones_final(self.modulo.id)
        self.tabla.setRowCount(len(evaluaciones))
        for fila, evaluacion in enumerate(evaluaciones):
            icono = ICONOS_NUMERICOS[evaluacion.orden - 1] if evaluacion.orden <= 6 else ""
            item_nombre = QTableWidgetItem(f"{icono} {evaluacion.nombre}".strip())
            item_nombre.setFlags(item_nombre.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_nombre.setData(Qt.ItemDataRole.UserRole, evaluacion.id)
            item_peso = QTableWidgetItem(str(pesos.get(evaluacion.id, 1.0)))
            self.tabla.setItem(fila, 0, item_nombre)
            self.tabla.setItem(fila, 1, item_peso)
        self._actualizando_desde_codigo = False

    def _al_cambiar_celda(self, item: QTableWidgetItem):
        if self._actualizando_desde_codigo:
            return
        fila = item.row()
        item_nombre = self.tabla.item(fila, 0)
        item_peso = self.tabla.item(fila, 1)
        if item_nombre is None:
            return
        evaluacion_id = item_nombre.data(Qt.ItemDataRole.UserRole)
        texto_peso = item_peso.text() if item_peso else "1"
        try:
            peso = float(texto_peso.replace(",", ".")) if texto_peso.strip() != "" else 1.0
        except ValueError:
            QMessageBox.warning(self, "Peso no válido", "El peso debe ser un número. Se usará 1.")
            peso = 1.0
        self.base_datos.actualizar_peso_evaluacion_final(self.modulo.id, evaluacion_id, peso)
        self.refrescar()
