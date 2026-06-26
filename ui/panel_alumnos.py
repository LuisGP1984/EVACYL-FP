"""
Panel "Alumnos" de un módulo: lista única de alumnado para todo el
módulo (compartida por todas sus evaluaciones parciales y FINAL).
Permite añadir uno a uno, pegar directamente desde Excel (Ctrl+V) o
importar un archivo .xlsx.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.database import BaseDatosModulo, Modulo
from core.importacion import (
    filas_desde_excel,
    filas_desde_texto_pegado,
    normalizar_filas_alumnos,
)
from core.plantillas import generar_plantilla_alumnos
from ui.widgets_comunes import BotonAyuda, TablaConBorrado

TEXTO_AYUDA = (
    "En esta pestaña gestionas el alumnado del módulo (una sola lista, compartida por "
    "todas sus evaluaciones parciales y FINAL).\n\n"
    "Puedes añadirlo de varias formas:\n"
    "• A mano, con el botón «➕ Añadir alumno/a» y escribiendo en la tabla.\n"
    "• Copiando celdas en Excel (Apellidos y Nombre) y pegándolas aquí con "
    "Ctrl+V o el botón «📋 Pegar desde Excel».\n"
    "• Importando un archivo .xlsx con el botón «📂 Importar archivo .xlsx…». "
    "Si no sabes qué formato debe tener, descarga primero la plantilla de "
    "ejemplo con «⬇️ Descargar plantilla de ejemplo…».\n\n"
    "Si un alumno o alumna se incorpora más adelante (en una evaluación posterior a la "
    "1ª), indícalo en la columna «Se incorpora en»: no contará en las evaluaciones "
    "anteriores a su incorporación."
)


class PanelAlumnos(QWidget):
    COLUMNAS = ["Apellidos", "Nombre", "Se incorpora en"]

    def __init__(self, base_datos: BaseDatosModulo, modulo: Modulo):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo
        self._actualizando_desde_codigo = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        fila_titulo = QHBoxLayout()
        titulo = QLabel("👥 Alumnado del módulo")
        titulo.setObjectName("subtitulo")
        fila_titulo.addWidget(titulo)
        fila_titulo.addStretch()
        fila_titulo.addWidget(BotonAyuda("Ayuda — Alumnado", TEXTO_AYUDA))
        layout.addLayout(fila_titulo)

        ayuda = QLabel(
            "Esta lista es única para todo el módulo. Todas las evaluaciones parciales y "
            "FINAL la heredan automáticamente. Si un alumno se incorpora más adelante, "
            "indícalo en la columna “Se incorpora en”: no contará en las evaluaciones anteriores."
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

        atajo_pegar = QShortcut(QKeySequence.StandardKey.Paste, self.tabla)
        atajo_pegar.activated.connect(self.pegar_desde_portapapeles)

        fila_botones = QHBoxLayout()

        boton_anadir = QPushButton("➕ Añadir alumno/a")
        boton_anadir.clicked.connect(self.anadir_alumno)
        fila_botones.addWidget(boton_anadir)

        boton_pegar = QPushButton("📋 Pegar desde Excel (Ctrl+V)")
        boton_pegar.setObjectName("botonSecundario")
        boton_pegar.clicked.connect(self.pegar_desde_portapapeles)
        fila_botones.addWidget(boton_pegar)

        boton_importar = QPushButton("📂 Importar archivo .xlsx…")
        boton_importar.setObjectName("botonSecundario")
        boton_importar.clicked.connect(self.importar_desde_archivo)
        fila_botones.addWidget(boton_importar)

        boton_plantilla = QPushButton("⬇️ Descargar plantilla de ejemplo…")
        boton_plantilla.setObjectName("botonSecundario")
        boton_plantilla.clicked.connect(self.descargar_plantilla)
        fila_botones.addWidget(boton_plantilla)

        boton_eliminar = QPushButton("🗑️ Eliminar seleccionado/a")
        boton_eliminar.setObjectName("botonPeligro")
        boton_eliminar.clicked.connect(self.eliminar_alumno_seleccionado)
        fila_botones.addWidget(boton_eliminar)

        self._ultima_captura_eliminacion = None
        self.boton_deshacer = QPushButton("↩️ Deshacer")
        self.boton_deshacer.setObjectName("botonSecundario")
        self.boton_deshacer.setEnabled(False)
        self.boton_deshacer.clicked.connect(self.deshacer_ultima_eliminacion)
        fila_botones.addWidget(self.boton_deshacer)

        fila_botones.addStretch()
        layout.addLayout(fila_botones)

        self.refrescar()

    # -- refresco de la tabla ------------------------------------------------

    def refrescar(self):
        self._actualizando_desde_codigo = True
        alumnos = self.base_datos.listar_alumnos(self.modulo.id)
        evaluaciones_parciales = self.base_datos.listar_evaluaciones_parciales(self.modulo.id)

        self.tabla.setRowCount(len(alumnos))
        for fila, alumno in enumerate(alumnos):
            item_apellidos = QTableWidgetItem(alumno.apellidos)
            item_apellidos.setData(Qt.ItemDataRole.UserRole, alumno.id)
            item_nombre = QTableWidgetItem(alumno.nombre)
            self.tabla.setItem(fila, 0, item_apellidos)
            self.tabla.setItem(fila, 1, item_nombre)

            combo = QComboBox()
            for evaluacion in evaluaciones_parciales:
                combo.addItem(evaluacion.nombre, evaluacion.orden)
            indice_actual = max(0, min(alumno.orden_alta - 1, combo.count() - 1))
            combo.setCurrentIndex(indice_actual)
            combo.currentIndexChanged.connect(
                lambda _indice, alumno_id=alumno.id, combo=combo: self._cambiar_orden_alta(
                    alumno_id, combo.currentData()
                )
            )
            self.tabla.setCellWidget(fila, 2, combo)
        self._actualizando_desde_codigo = False

    def _cambiar_orden_alta(self, alumno_id: int, orden_alta: int):
        self.base_datos.actualizar_orden_alta_alumno(alumno_id, orden_alta)

    def _al_cambiar_celda(self, item: QTableWidgetItem):
        if self._actualizando_desde_codigo:
            return
        fila = item.row()
        item_apellidos = self.tabla.item(fila, 0)
        item_nombre = self.tabla.item(fila, 1)
        if item_apellidos is None:
            return
        alumno_id = item_apellidos.data(Qt.ItemDataRole.UserRole)
        if alumno_id is None:
            return
        apellidos = item_apellidos.text() if item_apellidos else ""
        nombre = item_nombre.text() if item_nombre else ""
        self.base_datos.actualizar_alumno(alumno_id, apellidos, nombre)

    # -- acciones -------------------------------------------------------

    def anadir_alumno(self):
        self.base_datos.agregar_alumno(self.modulo.id, "", "")
        self.refrescar()

    def eliminar_alumno_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Sin selección", "Selecciona primero una fila.")
            return
        item_apellidos = self.tabla.item(fila, 0)
        alumno_id = item_apellidos.data(Qt.ItemDataRole.UserRole) if item_apellidos else None
        if alumno_id is None:
            return
        nombre_completo = f"{item_apellidos.text()}".strip() or "este alumno/a"
        self._ultima_captura_eliminacion = self.base_datos.eliminar_alumno_con_deshacer(alumno_id)
        self.boton_deshacer.setEnabled(self._ultima_captura_eliminacion is not None)
        self.boton_deshacer.setText(f"↩️ Deshacer eliminación de «{nombre_completo}»")
        self.refrescar()

    def deshacer_ultima_eliminacion(self):
        if self._ultima_captura_eliminacion is None:
            return
        self.base_datos.restaurar_eliminacion(self._ultima_captura_eliminacion)
        self._ultima_captura_eliminacion = None
        self.boton_deshacer.setEnabled(False)
        self.boton_deshacer.setText("↩️ Deshacer")
        self.refrescar()

    def pegar_desde_portapapeles(self):
        texto = QApplication.clipboard().text()
        if not texto.strip():
            QMessageBox.information(
                self, "Portapapeles vacío", "Copia primero las celdas en Excel y vuelve a intentarlo."
            )
            return
        filas = filas_desde_texto_pegado(texto)
        alumnos_nuevos = normalizar_filas_alumnos(filas)
        self._importar_lista(alumnos_nuevos)

    def importar_desde_archivo(self):
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self, "Selecciona el archivo Excel con el alumnado", filter="Excel (*.xlsx)"
        )
        if not ruta_archivo:
            return
        try:
            filas = filas_desde_excel(ruta_archivo)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "No se pudo leer el archivo", str(exc))
            return
        alumnos_nuevos = normalizar_filas_alumnos(filas)
        self._importar_lista(alumnos_nuevos)

    def _importar_lista(self, alumnos_nuevos: list[tuple[str, str]]):
        if not alumnos_nuevos:
            QMessageBox.information(
                self, "Nada que importar", "No se ha reconocido ningún alumno en los datos."
            )
            return
        insertados = self.base_datos.agregar_alumnos_en_lote(self.modulo.id, alumnos_nuevos)
        self.refrescar()
        QMessageBox.information(self, "Importación completada", f"Se han añadido {insertados} alumnos/as.")

    def descargar_plantilla(self):
        ruta_texto, _ = QFileDialog.getSaveFileName(
            self, "Guardar plantilla de alumnos", "plantilla_alumnos.xlsx", filter="Excel (*.xlsx)"
        )
        if not ruta_texto:
            return
        ruta = Path(ruta_texto)
        if ruta.suffix.lower() != ".xlsx":
            ruta = ruta.with_suffix(".xlsx")
        try:
            generar_plantilla_alumnos(ruta)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "No se pudo generar la plantilla", str(exc))
            return
        QMessageBox.information(
            self,
            "Plantilla guardada",
            f"Archivo guardado en:\n{ruta}\n\n"
            "Tiene dos columnas: Apellidos y Nombre, con algunas filas de ejemplo. "
            "Sustitúyelas por tu alumnado real y luego usa «Importar archivo .xlsx…».",
        )
