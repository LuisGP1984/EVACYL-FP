"""
Panel de la evaluación FINAL de un módulo. A diferencia de las
evaluaciones parciales:

  - No tiene instrumentos propios: en su lugar, una sub-pestaña
    "Evaluaciones" donde se ajusta el peso de cada evaluación parcial
    (ver panel_evaluaciones_final.py).
  - Las calificaciones se calculan siempre a partir de las notas de
    criterio de todas las evaluaciones parciales: no hace falta ningún
    botón, se recalculan solas cada vez que se entra en la pestaña.

NOTA: Estadísticas, Trazabilidad, exportación a Excel y generación de
informes de alumno están pendientes de construir como siguiente paso —
de momento esta versión solo cubre Calificaciones y Evaluaciones.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.calificacion import calificacion_cualitativa
from core.database import BaseDatosModulo, Modulo
from core.exportacion import exportar_final
from ui.dialogo_informes import DialogoGenerarInformes, generar_informe_final_individual
from ui.panel_evaluacion import (
    COLOR_FONDO_IDENTIDAD,
    _aplicar_cabeceras_por_bloque,
    _color_para_nota,
    _formatear_celda_nota,
    _formatear_numero,
)
from ui.panel_evaluaciones_final import PanelEvaluacionesFinal
from ui.widgets_comunes import BotonAyuda

TEXTO_AYUDA_FINAL_CALIFICACIONES = (
    "Esta tabla es la nota final de curso del módulo para cada alumno/a: se calcula sola, "
    "combinando las notas de criterio de todas las evaluaciones parciales según el peso "
    "que le hayas dado a cada una en la sub-pestaña «⚖️ Evaluaciones».\n\n"
    "No introduces nada aquí directamente. Si a un alumno le falta nota de un criterio en "
    "alguna evaluación, las que sí tienen nota se reparten el 100% del peso para ese "
    "criterio (no se penaliza por tener menos evaluaciones)."
)


class TablaCalificacionesFinal(QWidget):
    """Igual idea que TablaCalificaciones de una evaluación parcial, pero
    calculando a partir de calcular_notas_ra_final / calcular_notas_modulo_final
    / calcular_notas_criterios_final, y sin atenuar a ningún alumno (en
    FINAL siempre se incluye a todo el alumnado, independientemente de
    cuándo se incorporara). Dos tablas: una de RA (prioritaria para el
    profesorado de FP) y otra de detalle por criterio.
    """

    def __init__(self, base_datos: BaseDatosModulo, modulo: Modulo):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        fila_titulo = QHBoxLayout()
        titulo = QLabel("🏁 Calificaciones — Evaluación Final del módulo")
        titulo.setObjectName("subtitulo")
        fila_titulo.addWidget(titulo)
        fila_titulo.addStretch()
        fila_titulo.addWidget(BotonAyuda("Ayuda — Calificaciones FINAL", TEXTO_AYUDA_FINAL_CALIFICACIONES))
        layout.addLayout(fila_titulo)

        self.aviso_pesos_ra = QLabel("")
        self.aviso_pesos_ra.setWordWrap(True)
        self.aviso_pesos_ra.setStyleSheet(
            "background-color: #FBE3D6; color: #7A1B08; border-left: 4px solid #E22B10; "
            "border-radius: 6px; padding: 10px;"
        )
        self.aviso_pesos_ra.setVisible(False)
        layout.addWidget(self.aviso_pesos_ra)

        titulo_ra = QLabel("Nota final por Resultado de Aprendizaje")
        titulo_ra.setStyleSheet("font-weight: 600; color: #7A1B08;")
        layout.addWidget(titulo_ra)

        self.tabla_ra = QTableWidget()
        self.tabla_ra.setAlternatingRowColors(True)
        self.tabla_ra.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla_ra)

        titulo_criterios = QLabel("Detalle por criterio de evaluación")
        titulo_criterios.setStyleSheet("font-weight: 600; color: #7A1B08; margin-top: 6px;")
        layout.addWidget(titulo_criterios)

        self.tabla_criterios = QTableWidget()
        self.tabla_criterios.setAlternatingRowColors(True)
        self.tabla_criterios.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla_criterios)

        nota = QLabel(
            "Esta tabla se calcula automáticamente a partir de todas las evaluaciones "
            "parciales, según el peso indicado en la sub-pestaña «Evaluaciones». No hace "
            "falta introducir nada aquí directamente."
        )
        nota.setWordWrap(True)
        nota.setStyleSheet("color: #8A7A6E;")
        layout.addWidget(nota)

        fila_botones = QHBoxLayout()
        boton_exportar = QPushButton("📥 Exportar a Excel…")
        boton_exportar.clicked.connect(self.exportar_a_excel)
        fila_botones.addWidget(boton_exportar)

        boton_informe = QPushButton("📄 Generar informe de alumno…")
        boton_informe.setObjectName("botonSecundario")
        boton_informe.clicked.connect(self.abrir_dialogo_informes)
        fila_botones.addWidget(boton_informe)

        fila_botones.addStretch()
        layout.addLayout(fila_botones)

        self.refrescar()

    def exportar_a_excel(self):
        nombre_sugerido = f"{self.modulo.nombre} - FINAL.xlsx"
        ruta_texto, _ = QFileDialog.getSaveFileName(
            self, "Exportar calificaciones finales a Excel", nombre_sugerido, filter="Excel (*.xlsx)"
        )
        if not ruta_texto:
            return
        ruta = Path(ruta_texto)
        if ruta.suffix.lower() != ".xlsx":
            ruta = ruta.with_suffix(".xlsx")
        try:
            exportar_final(self.base_datos, self.modulo, ruta)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "No se pudo exportar", str(exc))
            return
        QMessageBox.information(self, "Exportación completada", f"Archivo guardado en:\n{ruta}")

    def abrir_dialogo_informes(self):
        alumnos = self.base_datos.listar_alumnos(self.modulo.id)
        lista_alumnos = [(a.id, f"{a.apellidos}, {a.nombre}".strip(", ")) for a in alumnos]
        if not lista_alumnos:
            QMessageBox.information(self, "Sin alumnado", "Este módulo todavía no tiene alumnado.")
            return

        def generar_uno(alumno_id, formato, carpeta_destino):
            return generar_informe_final_individual(
                self.base_datos, self.modulo, alumno_id, formato, carpeta_destino
            )

        dialogo = DialogoGenerarInformes("Generar informe — FINAL", lista_alumnos, generar_uno, self)
        dialogo.exec()

    @staticmethod
    def _ajustar_columnas_identidad(tabla: QTableWidget):
        cabecera = tabla.horizontalHeader()
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        ancho_apellidos = max(tabla.columnWidth(0), 110)
        ancho_nombre = max(tabla.columnWidth(1), 90)
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        tabla.setColumnWidth(0, ancho_apellidos)
        tabla.setColumnWidth(1, ancho_nombre)

    def refrescar(self):
        suma_pesos_ra = self.base_datos.suma_pesos_ra(self.modulo.id)
        if abs(suma_pesos_ra - 100.0) >= 0.01:
            self.aviso_pesos_ra.setText(
                f"⚠️ Los pesos de los RA suman {suma_pesos_ra:g}% (deberían sumar 100%), así "
                "que la NOTA FINAL DE CURSO no se puede calcular todavía. Ve a la pestaña "
                "«🎯 RA y Criterios» y ajusta el peso de cada RA para que sumen 100% entre todos."
            )
            self.aviso_pesos_ra.setVisible(True)
        else:
            self.aviso_pesos_ra.setVisible(False)

        alumnos = self.base_datos.listar_alumnos(self.modulo.id)
        notas_modulo = self.base_datos.calcular_notas_modulo_final(self.modulo.id)
        self._refrescar_tabla_ra(alumnos, notas_modulo)
        self._refrescar_tabla_criterios(alumnos, notas_modulo)

    def _refrescar_tabla_ra(self, alumnos, notas_modulo):
        ras = self.base_datos.listar_ra(self.modulo.id)
        notas_ra = self.base_datos.calcular_notas_ra_final(self.modulo.id)

        encabezados = (
            ["Apellidos", "Nombre"]
            + [f"RA{ra.numero}" for ra in ras]
            + ["NOTA FINAL DE CURSO", "CALIFICACIÓN", "RA SUPERADOS"]
        )
        self.tabla_ra.setColumnCount(len(encabezados))
        self.tabla_ra.setRowCount(len(alumnos))
        col_final_numero = 2 + len(ras)
        col_final_letra = col_final_numero + 1
        col_ra_superados = col_final_letra + 1
        _aplicar_cabeceras_por_bloque(self.tabla_ra, encabezados, col_final_numero)
        cabecera = self.tabla_ra.horizontalHeader()
        for col in range(2, col_final_numero):
            cabecera.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.tabla_ra.setColumnWidth(col, 80)
        cabecera.setSectionResizeMode(col_final_numero, QHeaderView.ResizeMode.Fixed)
        cabecera.setSectionResizeMode(col_final_letra, QHeaderView.ResizeMode.Fixed)
        cabecera.setSectionResizeMode(col_ra_superados, QHeaderView.ResizeMode.Fixed)
        self.tabla_ra.setColumnWidth(col_final_numero, 100)
        self.tabla_ra.setColumnWidth(col_final_letra, 110)
        self.tabla_ra.setColumnWidth(col_ra_superados, 160)
        self._ajustar_columnas_identidad(self.tabla_ra)

        for fila, alumno in enumerate(alumnos):
            item_apellidos = QTableWidgetItem(alumno.apellidos)
            item_nombre = QTableWidgetItem(alumno.nombre)
            item_apellidos.setBackground(COLOR_FONDO_IDENTIDAD)
            item_nombre.setBackground(COLOR_FONDO_IDENTIDAD)
            self.tabla_ra.setItem(fila, 0, item_apellidos)
            self.tabla_ra.setItem(fila, 1, item_nombre)

            ras_no_superados = []
            for indice, ra in enumerate(ras):
                valor = notas_ra.get((ra.id, alumno.id))
                texto, color = _formatear_celda_nota(valor)
                item = QTableWidgetItem(texto)
                if color is not None:
                    item.setBackground(color)
                self.tabla_ra.setItem(fila, 2 + indice, item)
                if valor is None or valor < 5.0:
                    ras_no_superados.append(ra.numero)

            valor_final = notas_modulo.get(alumno.id)
            color_final = _color_para_nota(valor_final)
            item_numero_final = QTableWidgetItem(_formatear_numero(valor_final))
            item_letra_final = QTableWidgetItem(calificacion_cualitativa(valor_final))
            for item in (item_numero_final, item_letra_final):
                if color_final is not None:
                    item.setBackground(color_final)
                fuente = item.font()
                fuente.setBold(True)
                item.setFont(fuente)
            self.tabla_ra.setItem(fila, col_final_numero, item_numero_final)
            self.tabla_ra.setItem(fila, col_final_letra, item_letra_final)

            if ras_no_superados:
                texto_superados = "FALTAN: " + ", ".join(f"RA{n}" for n in ras_no_superados)
                color_superados = QColor("#FBE3D6")
            else:
                texto_superados = "TODOS"
                color_superados = QColor("#D7F2E3")
            item_superados = QTableWidgetItem(texto_superados)
            item_superados.setBackground(color_superados)
            fuente_superados = item_superados.font()
            fuente_superados.setBold(True)
            item_superados.setFont(fuente_superados)
            self.tabla_ra.setItem(fila, col_ra_superados, item_superados)

    def _refrescar_tabla_criterios(self, alumnos, notas_modulo):
        criterios_con_ra = self.base_datos.listar_criterios_de_modulo(self.modulo.id)

        codigos = [self.base_datos.codigo_criterio(ra, criterio) for ra, criterio in criterios_con_ra]
        encabezados = ["Apellidos", "Nombre"] + codigos + ["NOTA FINAL DE CURSO", "CALIFICACIÓN"]
        self.tabla_criterios.setColumnCount(len(encabezados))
        self.tabla_criterios.setRowCount(len(alumnos))

        col_final_numero = 2 + len(criterios_con_ra)
        col_final_letra = col_final_numero + 1
        _aplicar_cabeceras_por_bloque(self.tabla_criterios, encabezados, col_final_numero)
        cabecera = self.tabla_criterios.horizontalHeader()
        for col in range(2, col_final_numero):
            cabecera.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.tabla_criterios.setColumnWidth(col, 70)
        cabecera.setSectionResizeMode(col_final_numero, QHeaderView.ResizeMode.Fixed)
        cabecera.setSectionResizeMode(col_final_letra, QHeaderView.ResizeMode.Fixed)
        self.tabla_criterios.setColumnWidth(col_final_numero, 100)
        self.tabla_criterios.setColumnWidth(col_final_letra, 110)
        self._ajustar_columnas_identidad(self.tabla_criterios)

        notas_criterio = self.base_datos.calcular_notas_criterios_final(self.modulo.id)

        for fila, alumno in enumerate(alumnos):
            item_apellidos = QTableWidgetItem(alumno.apellidos)
            item_nombre = QTableWidgetItem(alumno.nombre)
            item_apellidos.setBackground(COLOR_FONDO_IDENTIDAD)
            item_nombre.setBackground(COLOR_FONDO_IDENTIDAD)
            self.tabla_criterios.setItem(fila, 0, item_apellidos)
            self.tabla_criterios.setItem(fila, 1, item_nombre)

            for indice, (_ra, criterio) in enumerate(criterios_con_ra):
                valor = notas_criterio.get((criterio.id, alumno.id))
                texto, color = _formatear_celda_nota(valor)
                item = QTableWidgetItem(texto)
                if color is not None:
                    item.setBackground(color)
                self.tabla_criterios.setItem(fila, 2 + indice, item)

            valor_final = notas_modulo.get(alumno.id)
            color_final = _color_para_nota(valor_final)
            item_numero_final = QTableWidgetItem(_formatear_numero(valor_final))
            item_letra_final = QTableWidgetItem(calificacion_cualitativa(valor_final))
            for item in (item_numero_final, item_letra_final):
                if color_final is not None:
                    item.setBackground(color_final)
                fuente = item.font()
                fuente.setBold(True)
                item.setFont(fuente)
            self.tabla_criterios.setItem(fila, col_final_numero, item_numero_final)
            self.tabla_criterios.setItem(fila, col_final_letra, item_letra_final)


class PanelFinal(QWidget):
    def __init__(self, base_datos: BaseDatosModulo, modulo: Modulo):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sub_pestanas = QTabWidget()
        layout.addWidget(self.sub_pestanas)

        self.tabla_calificaciones = TablaCalificacionesFinal(base_datos, modulo)
        self.sub_pestanas.addTab(self.tabla_calificaciones, "📊 Calificaciones")

        self.panel_evaluaciones = PanelEvaluacionesFinal(base_datos, modulo)
        self.sub_pestanas.addTab(self.panel_evaluaciones, "⚖️ Evaluaciones")

        self.sub_pestanas.currentChanged.connect(self._al_cambiar_sub_pestana)

    def _al_cambiar_sub_pestana(self, _indice: int):
        self.tabla_calificaciones.refrescar()

    def refrescar(self):
        self.tabla_calificaciones.refrescar()
        self.panel_evaluaciones.refrescar()
