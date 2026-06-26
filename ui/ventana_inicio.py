"""
Ventana para elegir o crear un curso académico DENTRO de la carpeta del
docente ya seleccionada (ver ventana_carpeta_docente.py). Cada curso
académico es una subcarpeta (ej. "2025-2026") que contiene su propio
curso.db.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.database import BaseDatosModulo
from core.respaldo import crear_copia_seguridad
from ui.ventana_curso import VentanaCurso
from ui.widgets_comunes import BotonAyuda, VentanaConFondo

NOMBRE_ARCHIVO_BD = "curso.db"

TEXTO_AYUDA_CURSOS_ACADEMICOS = (
    "Un <b>curso académico</b> (por ejemplo, «2025-2026») agrupa todas las materias que "
    "impartes durante ese año. Cada curso académico vive en su propia subcarpeta dentro "
    "de tu carpeta de trabajo, con todos sus datos guardados en tu ordenador (nunca en "
    "internet).\n\n"
    "Pulsa «➕ Crear curso académico nuevo» para empezar uno (solo necesitas darle un "
    "nombre), o selecciona uno de la lista y pulsa «🔍 Abrir curso seleccionado» — también "
    "puedes hacer doble clic sobre él."
)


def _cursos_existentes(carpeta_docente: Path) -> list[Path]:
    """Subcarpetas de la carpeta del docente que contienen un curso.db,
    ordenadas alfabéticamente (lo que normalmente las ordena por año).
    """
    if not carpeta_docente.exists():
        return []
    candidatos = [
        subcarpeta
        for subcarpeta in carpeta_docente.iterdir()
        if subcarpeta.is_dir() and (subcarpeta / NOMBRE_ARCHIVO_BD).exists()
    ]
    return sorted(candidatos, key=lambda p: p.name)


class VentanaInicio(VentanaConFondo):
    """Pantalla de cursos académicos: lista los que ya existen dentro de
    la carpeta del docente y permite crear uno nuevo o abrir uno de la
    lista, sin volver a pedir la carpeta general cada vez.
    """

    def __init__(self, carpeta_docente: Path):
        super().__init__()
        self.carpeta_docente = carpeta_docente
        self.setWindowTitle("EVACYL FP — Cursos académicos")
        self._accion_ir_a_inicio = None

        contenedor = QWidget()
        contenedor.setObjectName("fondoTransparente")
        self.setCentralWidget(contenedor)
        layout_exterior = QVBoxLayout(contenedor)
        layout_exterior.setContentsMargins(40, 30, 40, 30)
        layout_exterior.setSpacing(12)

        fila_superior = QHBoxLayout()
        boton_inicio = QPushButton("🏠 Inicio")
        boton_inicio.setObjectName("botonSecundario")
        boton_inicio.clicked.connect(self._ir_a_inicio)
        fila_superior.addWidget(boton_inicio)
        fila_superior.addStretch()
        layout_exterior.addLayout(fila_superior)

        panel = QWidget()
        panel.setObjectName("panelSobreFondo")
        panel.setMaximumWidth(560)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        layout_exterior.addWidget(panel)
        layout_exterior.addStretch()

        etiqueta_carpeta = QLabel(f"📁 {carpeta_docente}")
        etiqueta_carpeta.setWordWrap(True)
        etiqueta_carpeta.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(etiqueta_carpeta)

        fila_titulo = QHBoxLayout()
        titulo = QLabel("📚 Tus cursos académicos")
        titulo.setObjectName("titulo")
        fila_titulo.addWidget(titulo)
        fila_titulo.addStretch()
        fila_titulo.addWidget(BotonAyuda("Ayuda — Cursos académicos", TEXTO_AYUDA_CURSOS_ACADEMICOS))
        layout.addLayout(fila_titulo)

        self.lista_cursos = QListWidget()
        self.lista_cursos.setMaximumHeight(160)
        self.lista_cursos.itemDoubleClicked.connect(self.abrir_curso_seleccionado)
        layout.addWidget(self.lista_cursos)

        boton_abrir = QPushButton("🔍 Abrir curso seleccionado")
        boton_abrir.clicked.connect(self.abrir_curso_seleccionado)
        layout.addWidget(boton_abrir)

        boton_crear = QPushButton("➕ Crear curso académico nuevo")
        boton_crear.setObjectName("botonSecundario")
        boton_crear.clicked.connect(self.crear_curso_nuevo)
        layout.addWidget(boton_crear)

        self.ventana_curso: VentanaCurso | None = None

        self._refrescar_lista()

    def conectar_ir_a_inicio(self, funcion_callback):
        """Define qué hacer al pulsar "Inicio" desde esta pantalla, y se
        propaga también a la VentanaCurso que se cree desde aquí."""
        self._accion_ir_a_inicio = funcion_callback

    def _ir_a_inicio(self):
        if self._accion_ir_a_inicio is not None:
            self._accion_ir_a_inicio()
        self.close()

    # -- lista de cursos -------------------------------------------------

    def _refrescar_lista(self):
        self.lista_cursos.clear()
        cursos = _cursos_existentes(self.carpeta_docente)
        if not cursos:
            item = QListWidgetItem("(Todavía no tienes ningún curso creado aquí)")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.lista_cursos.addItem(item)
            return
        for carpeta_curso in cursos:
            item = QListWidgetItem(f"📅 {carpeta_curso.name}")
            item.setData(Qt.ItemDataRole.UserRole, carpeta_curso)
            self.lista_cursos.addItem(item)

    # -- acciones -------------------------------------------------------

    def crear_curso_nuevo(self):
        nombre, ok = QInputDialog.getText(
            self, "Nuevo curso académico", "Nombre del curso (ejemplo: 2025-2026):"
        )
        if not ok or not nombre.strip():
            return
        nombre = nombre.strip()
        carpeta_curso = self.carpeta_docente / nombre
        ruta_bd = carpeta_curso / NOMBRE_ARCHIVO_BD

        if ruta_bd.exists():
            respuesta = QMessageBox.question(
                self,
                "Ese curso ya existe",
                f"Ya existe un curso llamado «{nombre}» en tu carpeta. ¿Quieres abrirlo?",
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                return
        else:
            try:
                carpeta_curso.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                QMessageBox.critical(self, "No se pudo crear el curso", str(exc))
                return

        self._abrir_ventana_curso(ruta_bd)

    def abrir_curso_seleccionado(self):
        item = self.lista_cursos.currentItem()
        if item is None:
            QMessageBox.information(self, "Sin selección", "Selecciona primero un curso de la lista.")
            return
        carpeta_curso = item.data(Qt.ItemDataRole.UserRole)
        if carpeta_curso is None:
            return
        self._abrir_ventana_curso(carpeta_curso / NOMBRE_ARCHIVO_BD)

    def _abrir_ventana_curso(self, ruta_bd: Path):
        if ruta_bd.exists():
            crear_copia_seguridad(ruta_bd)  # protege el estado anterior antes de tocar nada

        try:
            base_datos = BaseDatosModulo(ruta_bd)
        except Exception as exc:  # noqa: BLE001 - mostramos cualquier fallo al docente
            QMessageBox.critical(self, "No se pudo abrir el curso", str(exc))
            return

        self.ventana_curso = VentanaCurso(base_datos, ruta_bd)
        self.ventana_curso.conectar_ir_a_inicio(self._accion_ir_a_inicio)
        self.ventana_curso.showMaximized()
        self.close()
