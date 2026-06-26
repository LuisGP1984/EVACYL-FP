"""
Ventana de un curso: muestra el listado de módulos dentro del curso.db
abierto, y permite crear módulos nuevos (indicando cuántas evaluaciones
parciales tiene cada uno), renombrarlos, eliminarlos o entrar en uno de
ellos para trabajar con sus Resultados de Aprendizaje y evaluaciones.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.database import BaseDatosModulo, Modulo
from core.respaldo import listar_copias_seguridad, restaurar_copia_seguridad
from ui.ventana_modulo import VentanaModulo
from ui.widgets_comunes import BotonAyuda, VentanaConFondo

TEXTO_AYUDA_CURSO = (
    "Un <b>módulo</b> agrupa todo lo necesario para evaluar un módulo profesional "
    "concreto: su alumnado, sus Resultados de Aprendizaje (RA) con sus criterios, y sus "
    "evaluaciones parciales más una FINAL que las combina.\n\n"
    "Al crear un módulo, indicas cuántas evaluaciones parciales tiene (2, 3, o las que "
    "correspondan según tu programación); la FINAL se añade siempre automáticamente.\n\n"
    "Pulsa «➕ Crear nuevo módulo» para empezar uno, o haz doble clic en un módulo de la "
    "lista para entrar en él."
)


class DialogoNuevoModulo(QDialog):
    """Pide el nombre del módulo y cuántas evaluaciones parciales tiene."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo módulo")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        formulario = QFormLayout()

        self.campo_nombre = QLineEdit()
        formulario.addRow("Nombre del módulo:", self.campo_nombre)

        self.spin_evaluaciones = QSpinBox()
        self.spin_evaluaciones.setRange(1, 6)
        self.spin_evaluaciones.setValue(2)
        formulario.addRow("Evaluaciones parciales:", self.spin_evaluaciones)

        layout.addLayout(formulario)

        explicacion = QLabel(
            "Se crearán automáticamente esas evaluaciones parciales (1ª, 2ª...) más una "
            "evaluación FINAL que las combinará."
        )
        explicacion.setWordWrap(True)
        explicacion.setStyleSheet("color: #8A7A6E; font-size: 12px;")
        layout.addWidget(explicacion)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def datos(self) -> tuple[str, int]:
        return self.campo_nombre.text().strip(), self.spin_evaluaciones.value()


class DialogoCopiasSeguridad(QDialog):
    """Lista las copias de seguridad disponibles para este curso y
    permite restaurar la seleccionada.
    """

    def __init__(self, ruta_bd: Path, parent=None):
        super().__init__(parent)
        self.ruta_bd = ruta_bd
        self.copia_a_restaurar: Path | None = None

        self.setWindowTitle("🛡️ Copias de seguridad de este curso")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)

        explicacion = QLabel(
            "Cada vez que abres este curso, se guarda automáticamente una copia de "
            "seguridad antes de tocar nada. Si algo ha ido mal, puedes volver a una copia "
            "anterior aquí.\n\n"
            "Al restaurar, el estado actual también se guarda como una copia más, así que "
            "no se pierde nada de forma irreversible."
        )
        explicacion.setWordWrap(True)
        layout.addWidget(explicacion)

        self.lista = QListWidget()
        copias = listar_copias_seguridad(ruta_bd)
        if not copias:
            item = QListWidgetItem("(Todavía no hay copias de seguridad de este curso)")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.lista.addItem(item)
        else:
            for copia in copias:
                partes = copia.stem.replace("curso_", "").split("_")
                if len(partes) >= 2:
                    fecha_legible = f"{partes[0]} a las {partes[1].replace('-', ':')}"
                else:
                    fecha_legible = copia.stem
                item = QListWidgetItem(f"📅 {fecha_legible}")
                item.setData(1, copia)
                self.lista.addItem(item)
        layout.addWidget(self.lista)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Restaurar esta copia")
        botones.accepted.connect(self._al_aceptar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _al_aceptar(self):
        item = self.lista.currentItem()
        if item is None:
            QMessageBox.information(self, "Sin selección", "Selecciona primero una copia de la lista.")
            return
        copia = item.data(1)
        if copia is None:
            return
        respuesta = QMessageBox.question(
            self,
            "Confirmar restauración",
            "Esto sustituirá los datos actuales del curso por los de esta copia de "
            "seguridad. El estado actual también quedará guardado como copia, por si "
            "necesitas deshacer esto. ¿Continuar?",
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        self.copia_a_restaurar = copia
        self.accept()


class VentanaCurso(VentanaConFondo):
    def __init__(self, base_datos: BaseDatosModulo, ruta_bd: Path):
        super().__init__()
        self.base_datos = base_datos
        self.ruta_bd = ruta_bd
        self._accion_ir_a_inicio = None

        self.setWindowTitle(f"Curso — {ruta_bd.parent.name}")
        self.resize(560, 420)

        contenedor = QWidget()
        contenedor.setObjectName("fondoTransparente")
        self.setCentralWidget(contenedor)
        layout_exterior = QVBoxLayout(contenedor)
        layout_exterior.setContentsMargins(24, 24, 24, 24)

        fila_superior = QHBoxLayout()
        boton_inicio = QPushButton("🏠 Inicio")
        boton_inicio.setObjectName("botonSecundario")
        boton_inicio.clicked.connect(self._ir_a_inicio)
        fila_superior.addWidget(boton_inicio)

        boton_copias = QPushButton("🛡️ Copias de seguridad")
        boton_copias.setObjectName("botonSecundario")
        boton_copias.clicked.connect(self.abrir_copias_seguridad)
        fila_superior.addWidget(boton_copias)

        fila_superior.addStretch()
        layout_exterior.addLayout(fila_superior)

        panel = QWidget()
        panel.setObjectName("panelSobreFondo")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout_exterior.addWidget(panel)

        etiqueta_ruta = QLabel(f"Archivo del curso: {ruta_bd}")
        etiqueta_ruta.setStyleSheet("color: gray;")
        layout.addWidget(etiqueta_ruta)

        fila_titulo = QHBoxLayout()
        titulo = QLabel("📚 Módulos")
        titulo.setObjectName("subtitulo")
        fila_titulo.addWidget(titulo)
        fila_titulo.addStretch()
        fila_titulo.addWidget(BotonAyuda("Ayuda — Módulos", TEXTO_AYUDA_CURSO))
        layout.addLayout(fila_titulo)

        self.lista_modulos = QListWidget()
        self.lista_modulos.itemDoubleClicked.connect(self.entrar_en_modulo_seleccionado)
        layout.addWidget(self.lista_modulos)

        fila_botones = QWidget()
        layout_botones = QVBoxLayout(fila_botones)
        layout_botones.setContentsMargins(0, 0, 0, 0)

        boton_crear = QPushButton("➕ Crear nuevo módulo")
        boton_crear.clicked.connect(self.crear_modulo)
        layout_botones.addWidget(boton_crear)

        boton_entrar = QPushButton("🔍 Entrar en el módulo seleccionado")
        boton_entrar.clicked.connect(self.entrar_en_modulo_seleccionado)
        layout_botones.addWidget(boton_entrar)

        boton_renombrar = QPushButton("✏️ Renombrar módulo seleccionado")
        boton_renombrar.clicked.connect(self.renombrar_modulo_seleccionado)
        layout_botones.addWidget(boton_renombrar)

        boton_eliminar = QPushButton("🗑️ Eliminar módulo seleccionado")
        boton_eliminar.clicked.connect(self.eliminar_modulo_seleccionado)
        layout_botones.addWidget(boton_eliminar)

        layout.addWidget(fila_botones)

        self.ventanas_modulo_abiertas: list[VentanaModulo] = []

        self.refrescar_lista_modulos()

    def conectar_ir_a_inicio(self, funcion_callback):
        self._accion_ir_a_inicio = funcion_callback

    def _ir_a_inicio(self):
        for ventana_modulo in self.ventanas_modulo_abiertas:
            ventana_modulo.close()
        if self._accion_ir_a_inicio is not None:
            self._accion_ir_a_inicio()
        self.close()

    # -- helpers -------------------------------------------------------

    def refrescar_lista_modulos(self):
        self.lista_modulos.clear()
        for modulo in self.base_datos.listar_modulos():
            item = QListWidgetItem(f"{modulo.nombre}  ({modulo.numero_evaluaciones_parciales} evaluaciones)")
            item.setData(1, modulo.id)
            self.lista_modulos.addItem(item)

    def _modulo_seleccionado(self) -> Modulo | None:
        item = self.lista_modulos.currentItem()
        if item is None:
            QMessageBox.information(self, "Sin selección", "Selecciona primero un módulo.")
            return None
        modulo_id = item.data(1)
        for modulo in self.base_datos.listar_modulos():
            if modulo.id == modulo_id:
                return modulo
        return None

    # -- acciones -------------------------------------------------------

    def crear_modulo(self):
        dialogo = DialogoNuevoModulo(self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        nombre, numero_evaluaciones = dialogo.datos()
        if not nombre:
            QMessageBox.warning(self, "Falta el nombre", "El módulo necesita un nombre.")
            return
        try:
            self.base_datos.crear_modulo(nombre, numero_evaluaciones)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "No se pudo crear el módulo", str(exc))
            return
        self.refrescar_lista_modulos()

    def entrar_en_modulo_seleccionado(self):
        modulo = self._modulo_seleccionado()
        if modulo is None:
            return
        ventana_modulo = VentanaModulo(self.base_datos, modulo)
        ventana_modulo.conectar_ir_a_inicio(self._ir_a_inicio)
        ventana_modulo.showMaximized()
        self.ventanas_modulo_abiertas.append(ventana_modulo)

    def renombrar_modulo_seleccionado(self):
        modulo = self._modulo_seleccionado()
        if modulo is None:
            return
        nuevo_nombre, ok = QInputDialog.getText(
            self, "Renombrar módulo", "Nuevo nombre:", text=modulo.nombre
        )
        if not ok or not nuevo_nombre.strip():
            return
        try:
            self.base_datos.renombrar_modulo(modulo.id, nuevo_nombre)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "No se pudo renombrar", str(exc))
            return
        self.refrescar_lista_modulos()

    def eliminar_modulo_seleccionado(self):
        modulo = self._modulo_seleccionado()
        if modulo is None:
            return
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"Esto borrará el módulo «{modulo.nombre}» y TODOS sus datos "
            "(alumnado, RA, criterios, notas de todas sus evaluaciones). "
            "Esta acción no se puede deshacer.\n\n¿Continuar?",
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        self.base_datos.eliminar_modulo(modulo.id)
        self.refrescar_lista_modulos()

    def abrir_copias_seguridad(self):
        dialogo = DialogoCopiasSeguridad(self.ruta_bd, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        copia_elegida = dialogo.copia_a_restaurar
        if copia_elegida is None:
            return

        ok = restaurar_copia_seguridad(copia_elegida, self.ruta_bd)
        if not ok:
            QMessageBox.critical(
                self, "No se pudo restaurar", "No se pudo completar la restauración de la copia."
            )
            return

        for ventana_modulo in self.ventanas_modulo_abiertas:
            ventana_modulo.close()
        self.base_datos.cerrar()

        nueva_base_datos = BaseDatosModulo(self.ruta_bd)
        nueva_ventana = VentanaCurso(nueva_base_datos, self.ruta_bd)
        nueva_ventana.conectar_ir_a_inicio(self._accion_ir_a_inicio)
        nueva_ventana.showMaximized()
        self._ventana_recargada_tras_restaurar = nueva_ventana
        QMessageBox.information(
            nueva_ventana, "Restauración completada", "Se ha restaurado la copia de seguridad seleccionada."
        )
        self.close()
