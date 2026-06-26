"""
Ventana para elegir la carpeta general del docente: el lugar donde se
guardarán, dentro, todos sus cursos académicos (cada uno en su propia
subcarpeta con varios módulos). Esta carpeta solo se pide una vez; a
partir de ahí, la app la recuerda y pasa directamente a elegir/crear el
curso académico.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.configuracion import guardar_carpeta_docente, leer_carpeta_docente
from ui.widgets_comunes import VentanaConFondo


class VentanaCarpetaDocente(VentanaConFondo):
    """Pantalla para elegir la carpeta general del docente. Si ya hay una
    guardada de una sesión anterior, se ofrece seguir usándola sin volver
    a preguntar.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carpeta de trabajo")
        self._accion_continuar = None  # recibe la carpeta elegida como argumento

        contenedor = QWidget()
        contenedor.setObjectName("fondoTransparente")
        self.setCentralWidget(contenedor)
        layout_exterior = QVBoxLayout(contenedor)
        layout_exterior.setAlignment(Qt.AlignmentFlag.AlignCenter)

        panel = QWidget()
        panel.setObjectName("panelSobreFondo")
        panel.setMaximumWidth(560)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(14)
        layout_exterior.addWidget(panel)

        titulo = QLabel("📁 Tu carpeta de trabajo")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        explicacion = QLabel(
            "Elige (o crea) una carpeta donde la aplicación guardará todos tus cursos "
            "académicos. Dentro de ella se creará una subcarpeta por cada curso (por "
            "ejemplo, «2025-2026»), y dentro de cada curso, tus módulos. Solo se pregunta "
            "una vez: la próxima vez que abras la aplicación, se recordará."
        )
        explicacion.setWordWrap(True)
        explicacion.setStyleSheet("color: #8A7A6E;")
        layout.addWidget(explicacion)

        carpeta_recordada = leer_carpeta_docente()
        if carpeta_recordada is not None:
            aviso = QLabel(f"📂 Última carpeta usada:\n{carpeta_recordada}")
            aviso.setWordWrap(True)
            aviso.setStyleSheet(
                "background-color: #FDF3E7; color: #7A1B08; border-radius: 6px; padding: 10px;"
            )
            layout.addWidget(aviso)

            boton_continuar = QPushButton("✅ Seguir usando esta carpeta")
            boton_continuar.setMinimumHeight(40)
            boton_continuar.clicked.connect(lambda: self._continuar_con(carpeta_recordada))
            layout.addWidget(boton_continuar)

        boton_elegir = QPushButton("📂 Elegir otra carpeta…")
        if carpeta_recordada is not None:
            boton_elegir.setObjectName("botonSecundario")
        boton_elegir.setMinimumHeight(40)
        boton_elegir.clicked.connect(self.elegir_carpeta)
        layout.addWidget(boton_elegir)

        self._carpeta_recordada = carpeta_recordada

    def conectar_continuar(self, funcion_callback):
        """funcion_callback recibe la carpeta elegida (Path) como argumento."""
        self._accion_continuar = funcion_callback

    def elegir_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(
            self, "Elige o crea tu carpeta de trabajo (por ejemplo, con tu nombre)"
        )
        if not carpeta:
            return
        self._continuar_con(Path(carpeta))

    def _continuar_con(self, carpeta: Path):
        guardar_carpeta_docente(carpeta)
        if self._accion_continuar is not None:
            self._accion_continuar(carpeta)
