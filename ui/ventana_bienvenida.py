"""
Pantalla de bienvenida: se muestra al arrancar la aplicación, antes de
la pantalla de crear/abrir curso. Presenta el logo y nombre de la
aplicación (EVACYL FP), el autor, su contacto, la licencia de uso, y la
colaboración del IES Virgen de la Calle.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.rutas_app import ruta_raiz_proyecto
from ui.estilos import PALETA
from ui.widgets_comunes import VentanaConFondo

NOMBRE_APLICACION = "EVACYL FP"
ESLOGAN_APLICACION = "Evaluación que conecta · Futuro que transforma"
AUTOR = "Luis González Posada"
CONTACTO = "luis.gonpos@educa.jcyl.es"
LICENCIA = "Esta obra puede reutilizarse citando al autor y sin fines lucrativos (CC BY-NC)."
COLABORACION = "Con la colaboración del IES Virgen de la Calle, en Palencia."

RUTA_LOGO = ruta_raiz_proyecto() / "recursos" / "logo.png"
RUTA_LOGO_IES = ruta_raiz_proyecto() / "recursos" / "logo_ies.png"


class VentanaBienvenida(VentanaConFondo):
    """Primera pantalla que ve el docente al abrir la aplicación."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(NOMBRE_APLICACION)

        contenedor = QWidget()
        contenedor.setObjectName("fondoTransparente")
        self.setCentralWidget(contenedor)
        layout_exterior = QVBoxLayout(contenedor)
        layout_exterior.setAlignment(Qt.AlignmentFlag.AlignCenter)

        panel = QFrame()
        panel.setObjectName("panelSobreFondo")
        panel.setMaximumWidth(620)
        panel.setStyleSheet(
            f"QFrame#panelSobreFondo {{"
            f"  background-color: rgba(255, 255, 255, 240);"
            f"  border-radius: 18px;"
            f"  border-top: 6px solid {PALETA['rojo_medio']};"
            f"}}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(48, 36, 48, 40)
        layout.setSpacing(6)
        layout_exterior.addWidget(panel)

        etiqueta_logo = QLabel()
        etiqueta_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if RUTA_LOGO.exists():
            pixmap = QPixmap(str(RUTA_LOGO))
            pixmap_escalado = pixmap.scaledToHeight(190, Qt.TransformationMode.SmoothTransformation)
            etiqueta_logo.setPixmap(pixmap_escalado)
        else:
            etiqueta_logo.setText(NOMBRE_APLICACION)
        layout.addWidget(etiqueta_logo)

        layout.addSpacing(10)

        subtitulo = QLabel(ESLOGAN_APLICACION)
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet(f"color: {PALETA['rojo_medio']}; font-size: 15px; font-style: italic;")
        layout.addWidget(subtitulo)

        subtitulo2 = QLabel("Evaluación de módulos de Formación Profesional por Resultados de Aprendizaje")
        subtitulo2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo2.setWordWrap(True)
        subtitulo2.setStyleSheet(f"color: {PALETA['gris_texto_atenuado']}; font-size: 12px;")
        layout.addWidget(subtitulo2)

        layout.addSpacing(24)

        tarjeta_autoria = QFrame()
        tarjeta_autoria.setStyleSheet(
            f"QFrame {{ background-color: {PALETA['naranja_muy_claro']}; "
            f"border-radius: 12px; }}"
        )
        layout_autoria = QVBoxLayout(tarjeta_autoria)
        layout_autoria.setContentsMargins(20, 16, 20, 16)
        layout_autoria.setSpacing(4)

        etiqueta_autor = QLabel(f"👤  {AUTOR}")
        etiqueta_autor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        etiqueta_autor.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {PALETA['rojo_muy_oscuro']};")
        layout_autoria.addWidget(etiqueta_autor)

        etiqueta_contacto = QLabel(f"✉️  {CONTACTO}")
        etiqueta_contacto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        etiqueta_contacto.setStyleSheet(f"font-size: 14px; color: {PALETA['rojo_medio']};")
        layout_autoria.addWidget(etiqueta_contacto)

        layout.addWidget(tarjeta_autoria)

        layout.addSpacing(14)

        tarjeta_licencia = QFrame()
        tarjeta_licencia.setStyleSheet(
            f"QFrame {{ background-color: {PALETA['acento_frio_claro']}; "
            f"border-radius: 12px; border-left: 4px solid {PALETA['acento_frio']}; }}"
        )
        layout_licencia = QHBoxLayout(tarjeta_licencia)
        layout_licencia.setContentsMargins(16, 12, 16, 12)

        icono_licencia = QLabel("©️🆓")
        icono_licencia.setStyleSheet("font-size: 18px;")
        layout_licencia.addWidget(icono_licencia)

        etiqueta_licencia = QLabel(LICENCIA)
        etiqueta_licencia.setWordWrap(True)
        etiqueta_licencia.setStyleSheet(f"color: {PALETA['acento_frio']}; font-size: 13px;")
        layout_licencia.addWidget(etiqueta_licencia)

        layout.addWidget(tarjeta_licencia)

        layout.addSpacing(14)

        tarjeta_colaboracion = QFrame()
        tarjeta_colaboracion.setStyleSheet(
            f"QFrame {{ background-color: {PALETA['naranja_muy_claro']}; "
            f"border-radius: 12px; }}"
        )
        layout_colaboracion = QVBoxLayout(tarjeta_colaboracion)
        layout_colaboracion.setContentsMargins(16, 12, 16, 12)
        layout_colaboracion.setSpacing(6)

        if RUTA_LOGO_IES.exists():
            etiqueta_logo_ies = QLabel()
            etiqueta_logo_ies.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap_ies = QPixmap(str(RUTA_LOGO_IES))
            pixmap_ies_escalado = pixmap_ies.scaledToHeight(48, Qt.TransformationMode.SmoothTransformation)
            etiqueta_logo_ies.setPixmap(pixmap_ies_escalado)
            layout_colaboracion.addWidget(etiqueta_logo_ies)

        etiqueta_colaboracion = QLabel(COLABORACION)
        etiqueta_colaboracion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        etiqueta_colaboracion.setWordWrap(True)
        etiqueta_colaboracion.setStyleSheet(f"color: {PALETA['gris_texto_atenuado']}; font-size: 12px;")
        layout_colaboracion.addWidget(etiqueta_colaboracion)

        layout.addWidget(tarjeta_colaboracion)

        layout.addSpacing(28)

        boton_continuar = QPushButton("Comenzar  →")
        boton_continuar.setMinimumHeight(46)
        boton_continuar.setStyleSheet("font-size: 15px; font-weight: 600;")
        boton_continuar.clicked.connect(self._continuar)
        layout.addWidget(boton_continuar)

        self._accion_continuar = None

    def conectar_continuar(self, funcion_callback):
        """Define qué hacer al pulsar "Comenzar" (normalmente: abrir la
        siguiente ventana y cerrar esta). Se inyecta desde main.py para
        evitar que este módulo dependa de main.py.
        """
        self._accion_continuar = funcion_callback

    def _continuar(self):
        if self._accion_continuar is not None:
            self._accion_continuar()
