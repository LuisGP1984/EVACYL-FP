"""
Ventana de un módulo. Pestañas previstas:
  - Alumnos               (lista única del módulo)
  - RA y Criterios        (Resultados de Aprendizaje y sus criterios)
  - Una pestaña por cada evaluación parcial (1ª, 2ª... según lo que se
    indicó al crear el módulo): instrumentos de evaluación propios y
    calificaciones calculadas a partir de ellos.
  - FINAL: sin instrumentos propios; agrega las evaluaciones parciales
    con un peso editable (por defecto igual entre todas).

NOTA: de momento, las pestañas de RA/Criterios y de evaluación son
placeholders (QWidget con un texto descriptivo) — se irán sustituyendo
por los paneles reales uno a uno.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.database import BaseDatosModulo, Modulo
from ui.estilos import hoja_estilos_pestanas_modulo
from ui.panel_alumnos import PanelAlumnos
from ui.panel_evaluacion import PanelEvaluacion
from ui.panel_final import PanelFinal
from ui.panel_ra_criterios import PanelRACriterios


def _placeholder(texto: str) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    etiqueta = QLabel(texto)
    etiqueta.setWordWrap(True)
    etiqueta.setStyleSheet("color: #8A7A6E; font-size: 14px; padding: 24px;")
    layout.addWidget(etiqueta)
    layout.addStretch()
    return widget


class VentanaModulo(QMainWindow):
    def __init__(self, base_datos: BaseDatosModulo, modulo: Modulo):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo
        self._accion_ir_a_inicio = None

        self.setWindowTitle(f"Módulo — {modulo.nombre}")
        self.resize(1050, 680)

        contenedor = QWidget()
        layout_raiz = QVBoxLayout(contenedor)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)
        self.setCentralWidget(contenedor)

        barra_superior = QWidget()
        barra_superior.setObjectName("barraSuperior")
        layout_barra = QHBoxLayout(barra_superior)
        layout_barra.setContentsMargins(12, 8, 12, 8)

        boton_inicio = QPushButton("🏠 Inicio")
        boton_inicio.setObjectName("botonSecundario")
        boton_inicio.clicked.connect(self._ir_a_inicio)
        layout_barra.addWidget(boton_inicio)
        layout_barra.addStretch()
        layout_raiz.addWidget(barra_superior)

        self.pestanas = QTabWidget()
        self.pestanas.setStyleSheet(
            hoja_estilos_pestanas_modulo(modulo.numero_evaluaciones_parciales)
        )
        layout_raiz.addWidget(self.pestanas)

        self.panel_alumnos = PanelAlumnos(base_datos, modulo)
        self.pestanas.addTab(self.panel_alumnos, "👥 Alumnos")

        self.panel_ra_criterios = PanelRACriterios(base_datos, modulo)
        self.pestanas.addTab(self.panel_ra_criterios, "🎯 RA y Criterios")

        ICONOS_NUMERICOS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
        evaluaciones = self.base_datos.listar_evaluaciones(modulo.id)
        self.paneles_refrescables: list = []
        for evaluacion in evaluaciones:
            if evaluacion.nombre == "FINAL":
                panel = PanelFinal(base_datos, modulo)
                self.pestanas.addTab(panel, "🏁 FINAL")
            else:
                icono = ICONOS_NUMERICOS[evaluacion.orden - 1] if evaluacion.orden <= 6 else ""
                panel = PanelEvaluacion(base_datos, modulo, evaluacion)
                self.pestanas.addTab(panel, f"{icono} {evaluacion.nombre}".strip())
            self.paneles_refrescables.append(panel)

        self.pestanas.currentChanged.connect(self._al_cambiar_pestana)

    def conectar_ir_a_inicio(self, funcion_callback):
        self._accion_ir_a_inicio = funcion_callback

    def _ir_a_inicio(self):
        if self._accion_ir_a_inicio is not None:
            self._accion_ir_a_inicio()

    def _al_cambiar_pestana(self, _indice: int):
        self.panel_alumnos.refrescar()
        self.panel_ra_criterios.refrescar()
        for panel in self.paneles_refrescables:
            if hasattr(panel, "refrescar"):
                panel.refrescar()
