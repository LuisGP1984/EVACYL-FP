"""
Panel "RA y Criterios" de un módulo: define los Resultados de Aprendizaje
(con su peso dentro del módulo) y, dentro de cada uno, sus criterios de
evaluación (con su peso dentro de ese RA, código "numero.letra"
generado automáticamente: 1.a, 1.b, 1.c...).

Cada RA se muestra como una sección plegable; dentro, una tabla con sus
criterios y un botón para regenerar la cantidad de criterios (que
reparte el peso igual entre todos, ajustable después a mano).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.database import BaseDatosModulo, Modulo
from ui.widgets_comunes import BotonAyuda, SeccionPlegable

TEXTO_AYUDA = (
    "Aquí defines los <b>Resultados de Aprendizaje (RA)</b> del módulo y, dentro de cada "
    "uno, sus <b>criterios de evaluación</b>.\n\n"
    "• Cada RA tiene un peso dentro de la nota del módulo (deben sumar 100% entre todos "
    "los RA, aunque la app no te lo impone — solo te avisa si no suman).\n"
    "• Dentro de cada RA, indica cuántos criterios tiene y pulsa «Generar criterios»: se "
    "crean automáticamente con código 1.a, 1.b, 1.c... (el número es el del RA, la letra "
    "es correlativa) y peso igual entre ellos dentro de ese RA. Puedes ajustar el peso de "
    "cada criterio después, a mano, en su propia fila.\n\n"
    "Si vuelves a generar criterios para un RA que ya los tenía, se sustituyen todos por "
    "los nuevos (perderías los pesos que hubieras ajustado a mano en ese RA)."
)


class PanelRACriterios(QWidget):
    def __init__(self, base_datos: BaseDatosModulo, modulo: Modulo):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(16, 16, 16, 16)
        layout_raiz.setSpacing(10)

        fila_titulo = QHBoxLayout()
        titulo = QLabel("🎯 Resultados de Aprendizaje y Criterios")
        titulo.setObjectName("subtitulo")
        fila_titulo.addWidget(titulo)
        fila_titulo.addStretch()
        fila_titulo.addWidget(BotonAyuda("Ayuda — RA y Criterios", TEXTO_AYUDA))
        layout_raiz.addLayout(fila_titulo)

        self.etiqueta_suma_pesos_ra = QLabel("")
        self.etiqueta_suma_pesos_ra.setTextFormat(Qt.TextFormat.RichText)
        layout_raiz.addWidget(self.etiqueta_suma_pesos_ra)

        boton_anadir_ra = QPushButton("➕ Añadir Resultado de Aprendizaje")
        boton_anadir_ra.clicked.connect(self.anadir_ra)
        layout_raiz.addWidget(boton_anadir_ra)

        # Contenedor donde se irán añadiendo una sección plegable por RA.
        self.layout_secciones = QVBoxLayout()
        self.layout_secciones.setSpacing(10)
        layout_raiz.addLayout(self.layout_secciones)
        layout_raiz.addStretch()

        self.refrescar()

    # -- refresco completo ------------------------------------------------

    def refrescar(self):
        # Se reconstruye todo desde cero: más simple que sincronizar
        # widgets existentes, y el número de RA no suele cambiar muy a
        # menudo como para que el coste de rehacerlo importe.
        while self.layout_secciones.count():
            item = self.layout_secciones.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        ras = self.base_datos.listar_ra(self.modulo.id)
        suma_pesos_ra = self.base_datos.suma_pesos_ra(self.modulo.id)
        color_suma = "#0DAB6C" if abs(suma_pesos_ra - 100.0) < 0.01 else "#E22B10"
        self.etiqueta_suma_pesos_ra.setText(
            f"Suma de pesos de los RA: <span style='color:{color_suma}; font-weight:600;'>"
            f"{suma_pesos_ra:g}%</span> (debe ser 100%)"
        )

        if not ras:
            etiqueta_vacio = QLabel(
                "Todavía no has añadido ningún Resultado de Aprendizaje. Pulsa «➕ Añadir "
                "Resultado de Aprendizaje» para empezar."
            )
            etiqueta_vacio.setWordWrap(True)
            etiqueta_vacio.setStyleSheet("color: #8A7A6E; padding: 12px;")
            self.layout_secciones.addWidget(etiqueta_vacio)
            return

        for ra in ras:
            seccion = self._construir_seccion_ra(ra)
            self.layout_secciones.addWidget(seccion)

    # -- construcción de la sección de un RA -------------------------------

    def _construir_seccion_ra(self, ra) -> SeccionPlegable:
        criterios = self.base_datos.listar_criterios_de_ra(ra.id)
        titulo_seccion = (
            f"RA{ra.numero} — peso {ra.peso:g}% del módulo"
            + (f"  ·  {ra.descripcion}" if ra.descripcion else "")
            + f"  ({len(criterios)} criterios)"
        )
        # Altura triplicada respecto al valor por defecto de SeccionPlegable
        # (220px): un RA puede tener bastantes criterios, y el docente
        # necesita verlos casi todos de un vistazo sin estar bajando el
        # scroll interno constantemente.
        seccion = SeccionPlegable(
            titulo_seccion, inicialmente_abierta=(len(criterios) == 0), altura_maxima_contenido=660
        )

        # -- fila de edición del propio RA: descripción y peso --
        fila_ra = QHBoxLayout()
        fila_ra.addWidget(QLabel("Descripción:"))
        campo_descripcion = QLineEdit(ra.descripcion)
        fila_ra.addWidget(campo_descripcion)

        fila_ra.addWidget(QLabel("Peso en el módulo:"))
        spin_peso_ra = QDoubleSpinBox()
        spin_peso_ra.setRange(0.0, 100.0)
        spin_peso_ra.setDecimals(1)
        spin_peso_ra.setSuffix(" %")
        spin_peso_ra.setValue(ra.peso)
        fila_ra.addWidget(spin_peso_ra)

        def _guardar_ra():
            self.base_datos.actualizar_ra(ra.id, campo_descripcion.text(), spin_peso_ra.value())
            self.refrescar()

        campo_descripcion.editingFinished.connect(_guardar_ra)
        spin_peso_ra.editingFinished.connect(_guardar_ra)

        boton_eliminar_ra = QPushButton("🗑️ Eliminar este RA")
        boton_eliminar_ra.setObjectName("botonPeligro")
        boton_eliminar_ra.clicked.connect(lambda: self._eliminar_ra(ra))
        fila_ra.addWidget(boton_eliminar_ra)

        seccion.layout_contenido.addLayout(fila_ra)

        # -- fila de generación automática de criterios --
        fila_generar = QHBoxLayout()
        fila_generar.addWidget(QLabel("Número de criterios:"))
        spin_cantidad = QSpinBox()
        spin_cantidad.setRange(1, 26)  # 26 letras del alfabeto disponibles
        spin_cantidad.setValue(max(1, len(criterios)))
        fila_generar.addWidget(spin_cantidad)

        boton_generar = QPushButton("⚙️ Generar criterios (1.a, 1.b...)")
        boton_generar.setObjectName("botonSecundario")
        boton_generar.clicked.connect(
            lambda: self._generar_criterios(ra, spin_cantidad.value())
        )
        fila_generar.addWidget(boton_generar)
        fila_generar.addStretch()
        seccion.layout_contenido.addLayout(fila_generar)

        # -- tabla de criterios ya generados --
        if criterios:
            tabla = QTableWidget()
            tabla.setColumnCount(2)
            tabla.setHorizontalHeaderLabels(["Código", "Peso dentro del RA"])
            tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            tabla.setColumnWidth(0, 90)
            tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            tabla.setRowCount(len(criterios))
            tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

            suma_pesos_criterios = self.base_datos.suma_pesos_criterios_de_ra(ra.id)

            for fila, criterio in enumerate(criterios):
                codigo = self.base_datos.codigo_criterio(ra, criterio)
                item_codigo = QTableWidgetItem(codigo)
                tabla.setItem(fila, 0, item_codigo)

                spin_peso_criterio = QDoubleSpinBox()
                spin_peso_criterio.setRange(0.0, 100.0)
                spin_peso_criterio.setDecimals(2)
                spin_peso_criterio.setSuffix(" %")
                spin_peso_criterio.setValue(criterio.peso)
                spin_peso_criterio.valueChanged.connect(
                    lambda valor, criterio_id=criterio.id: self.base_datos.actualizar_peso_criterio(
                        criterio_id, valor
                    )
                )
                tabla.setCellWidget(fila, 1, spin_peso_criterio)

            tabla.setMaximumHeight(32 * (len(criterios) + 1) + 10)
            seccion.layout_contenido.addWidget(tabla)

            color_suma_criterios = "#0DAB6C" if abs(suma_pesos_criterios - 100.0) < 0.01 else "#E22B10"
            etiqueta_suma = QLabel(
                f"Suma de pesos de estos criterios: "
                f"<span style='color:{color_suma_criterios}; font-weight:600;'>{suma_pesos_criterios:g}%</span> "
                f"(debe ser 100%)"
            )
            etiqueta_suma.setTextFormat(Qt.TextFormat.RichText)
            seccion.layout_contenido.addWidget(etiqueta_suma)

        return seccion

    # -- acciones -----------------------------------------------------------

    def anadir_ra(self):
        ras_existentes = self.base_datos.listar_ra(self.modulo.id)
        siguiente_numero = (max((ra.numero for ra in ras_existentes), default=0)) + 1
        descripcion, ok = QInputDialog.getText(
            self,
            f"Nuevo RA{siguiente_numero}",
            f"Descripción del RA{siguiente_numero} (puedes dejarlo en blanco y rellenarlo después):",
        )
        if not ok:
            return
        self.base_datos.agregar_ra(self.modulo.id, numero=siguiente_numero, descripcion=descripcion, peso=0.0)
        self.refrescar()

    def _generar_criterios(self, ra, cantidad: int):
        criterios_existentes = self.base_datos.listar_criterios_de_ra(ra.id)
        if criterios_existentes:
            respuesta = QMessageBox.question(
                self,
                "Sustituir criterios existentes",
                f"RA{ra.numero} ya tiene {len(criterios_existentes)} criterios. Generar de nuevo "
                "los sustituirá todos por otros nuevos con peso igual entre ellos (perderás "
                "cualquier ajuste de peso que hayas hecho a mano).\n\n¿Continuar?",
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                return
        self.base_datos.generar_criterios_para_ra(ra.id, cantidad)
        self.refrescar()

    def _eliminar_ra(self, ra):
        criterios = self.base_datos.listar_criterios_de_ra(ra.id)
        mensaje = (
            f"Esto borrará RA{ra.numero} y sus {len(criterios)} criterios, junto con "
            "cualquier nota asociada a ellos. Esta acción no se puede deshacer.\n\n¿Continuar?"
        )
        respuesta = QMessageBox.question(self, "Confirmar eliminación", mensaje)
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        self.base_datos.eliminar_ra(ra.id)
        self.refrescar()
