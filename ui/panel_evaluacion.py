"""
Panel de una evaluación parcial concreta (FINAL usa su propio panel, ver
panel_final.py, todavía pendiente de construir).

El alumnado se hereda del módulo (pestaña "Alumnos") y los criterios de
"RA y Criterios"; aquí no se editan. Sub-pestañas:

  - Calificaciones: tabla con la nota de cada criterio (calculada a
    partir de los instrumentos de evaluación) y la nota final del
    módulo, por alumno. Solo lectura.
  - Instrumentos de Evaluación: donde se crean los IE y se introducen
    las notas que alimentan el cálculo anterior.

NOTA: Estadísticas, Trazabilidad y generación de informes de alumno
están pendientes de construir como siguiente pantalla — de momento esta
versión solo cubre Calificaciones e Instrumentos.
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

from core.calificacion import calificacion_cualitativa, color_hex_nota
from core.database import BaseDatosModulo, Evaluacion, Modulo
from core.exportacion import exportar_evaluacion
from ui.dialogo_informes import DialogoGenerarInformes, generar_informe_evaluacion_individual
from ui.estilos import COLOR_COLUMNA_IDENTIDAD
from ui.panel_instrumentos import PanelInstrumentos
from ui.widgets_comunes import BotonAyuda
from ui.widgets_comunes import aplicar_cabeceras_por_bloque as _aplicar_cabeceras_por_bloque

COLOR_TEXTO_NO_EVALUADO = QColor("#A6927F")
COLOR_FONDO_IDENTIDAD = QColor(COLOR_COLUMNA_IDENTIDAD)

TEXTO_AYUDA_CALIFICACIONES = (
    "Esta tabla muestra el resultado calculado, sin que tengas que introducir nada aquí "
    "directamente: la nota de cada criterio se calcula combinando los instrumentos de "
    "evaluación que lo evalúan (pestaña «📝 Instrumentos de Evaluación»), y la nota final "
    "del módulo combina todos los criterios según el peso de su RA y el peso del propio "
    "criterio dentro de ese RA.\n\n"
    "Si no ves ninguna nota, lo más probable es que todavía no hayas creado ningún "
    "instrumento, o que no le hayas asignado ningún criterio."
)


def _formatear_numero(valor: float | None) -> str:
    if valor is None:
        return ""
    return f"{valor:.2f}".replace(".", ",")


def _color_para_nota(valor: float | None) -> QColor | None:
    color_hex = color_hex_nota(valor)
    return QColor(f"#{color_hex}") if color_hex else None


def _formatear_celda_nota(valor: float | None) -> tuple[str, QColor | None]:
    return _formatear_numero(valor), _color_para_nota(valor)


class TablaCalificaciones(QWidget):
    """Dos tablas, una debajo de otra:
      - Tabla de RA: alumnos en filas, una columna por Resultado de
        Aprendizaje con su nota en esta evaluación, y la nota final del
        módulo. Es la vista principal para el profesorado de FP.
      - Tabla de Criterios: el mismo alumnado, pero con una columna por
        criterio individual (de todos los RA), para quien quiera el
        detalle más fino.
    Ambas en solo lectura; se calculan a partir de los instrumentos de
    evaluación.
    """

    def __init__(self, base_datos: BaseDatosModulo, modulo: Modulo, evaluacion: Evaluacion):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo
        self.evaluacion = evaluacion

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        fila_titulo = QHBoxLayout()
        titulo = QLabel("📊 Calificaciones")
        titulo.setObjectName("subtitulo")
        fila_titulo.addWidget(titulo)
        fila_titulo.addStretch()
        fila_titulo.addWidget(BotonAyuda("Ayuda — Calificaciones", TEXTO_AYUDA_CALIFICACIONES))
        layout.addLayout(fila_titulo)

        self.aviso_sin_instrumentos = QLabel("")
        self.aviso_sin_instrumentos.setWordWrap(True)
        self.aviso_sin_instrumentos.setStyleSheet(
            "background-color: #FBE3D6; color: #7A1B08; border-left: 4px solid #E22B10; "
            "border-radius: 6px; padding: 10px;"
        )
        self.aviso_sin_instrumentos.setVisible(False)
        layout.addWidget(self.aviso_sin_instrumentos)

        self.aviso_pesos_ra = QLabel("")
        self.aviso_pesos_ra.setWordWrap(True)
        self.aviso_pesos_ra.setStyleSheet(
            "background-color: #FBE3D6; color: #7A1B08; border-left: 4px solid #E22B10; "
            "border-radius: 6px; padding: 10px;"
        )
        self.aviso_pesos_ra.setVisible(False)
        layout.addWidget(self.aviso_pesos_ra)

        titulo_ra = QLabel("Nota por Resultado de Aprendizaje")
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
            "Las notas se calculan a partir de los instrumentos de evaluación (pestaña "
            "«📝 Instrumentos de Evaluación»). La tabla de arriba muestra la nota de cada "
            "RA y la nota final del módulo; la de abajo, el detalle de cada criterio "
            "individual. Las celdas en blanco indican que el alumno/a todavía no tiene "
            "ninguna nota ahí."
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
        nombre_sugerido = f"{self.modulo.nombre} - {self.evaluacion.nombre}.xlsx"
        ruta_texto, _ = QFileDialog.getSaveFileName(
            self, "Exportar calificaciones a Excel", nombre_sugerido, filter="Excel (*.xlsx)"
        )
        if not ruta_texto:
            return
        ruta = Path(ruta_texto)
        if ruta.suffix.lower() != ".xlsx":
            ruta = ruta.with_suffix(".xlsx")
        try:
            exportar_evaluacion(self.base_datos, self.modulo, self.evaluacion, ruta)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "No se pudo exportar", str(exc))
            return
        QMessageBox.information(self, "Exportación completada", f"Archivo guardado en:\n{ruta}")

    def abrir_dialogo_informes(self):
        vista = self.base_datos.listar_alumnos_para_evaluacion(self.modulo.id, self.evaluacion.orden)
        lista_alumnos = [
            (alumno.id, f"{alumno.apellidos}, {alumno.nombre}".strip(", "))
            for alumno, evaluable in vista
            if evaluable
        ]
        if not lista_alumnos:
            QMessageBox.information(
                self, "Sin alumnado", "No hay alumnado evaluable todavía en esta evaluación."
            )
            return

        def generar_uno(alumno_id, formato, carpeta_destino):
            return generar_informe_evaluacion_individual(
                self.base_datos, self.modulo, self.evaluacion, alumno_id, formato, carpeta_destino
            )

        dialogo = DialogoGenerarInformes(
            f"Generar informe — {self.evaluacion.nombre}", lista_alumnos, generar_uno, self
        )
        dialogo.exec()

    @staticmethod
    def _ajustar_columnas_identidad(tabla: QTableWidget):
        """Apellidos/Nombre se ajustan al contenido (con un mínimo
        razonable) en vez de estirarse sin límite, y quedan luego
        arrastrables a mano si el docente quiere ensancharlas más.
        """
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
        instrumentos = self.base_datos.listar_instrumentos(self.evaluacion.id)
        if not instrumentos:
            self.aviso_sin_instrumentos.setText(
                "⚠️ Todavía no has creado ningún Instrumento de Evaluación (IE) en esta "
                "evaluación, así que no hay notas que mostrar. Ve a la pestaña «📝 "
                "Instrumentos de Evaluación» para crear el primero."
            )
            self.aviso_sin_instrumentos.setVisible(True)
        else:
            self.aviso_sin_instrumentos.setVisible(False)

        suma_pesos_ra = self.base_datos.suma_pesos_ra(self.modulo.id)
        if abs(suma_pesos_ra - 100.0) >= 0.01:
            self.aviso_pesos_ra.setText(
                f"⚠️ Los pesos de los RA suman {suma_pesos_ra:g}% (deberían sumar 100%), así "
                "que la NOTA FINAL del módulo no se puede calcular todavía. Ve a la pestaña "
                "«🎯 RA y Criterios» y ajusta el peso de cada RA para que sumen 100% entre todos. "
                "(Las notas de cada RA por separado sí se calculan correctamente; solo falta "
                "la combinación final.)"
            )
            self.aviso_pesos_ra.setVisible(True)
        else:
            self.aviso_pesos_ra.setVisible(False)

        vista_alumnos = self.base_datos.listar_alumnos_para_evaluacion(
            self.modulo.id, self.evaluacion.orden
        )
        notas_modulo = self.base_datos.calcular_notas_modulo_evaluacion(
            self.evaluacion.id, self.modulo.id
        )
        self._refrescar_tabla_ra(vista_alumnos, notas_modulo)
        self._refrescar_tabla_criterios(vista_alumnos, notas_modulo)

    def _refrescar_tabla_ra(self, vista_alumnos, notas_modulo):
        ras = self.base_datos.listar_ra(self.modulo.id)
        notas_ra = self.base_datos.calcular_notas_ra_evaluacion(self.evaluacion.id, self.modulo.id)

        encabezados = (
            ["Apellidos", "Nombre"]
            + [f"RA{ra.numero}" for ra in ras]
            + ["NOTA FINAL", "CALIFICACIÓN", "RA SUPERADOS"]
        )
        self.tabla_ra.setColumnCount(len(encabezados))
        self.tabla_ra.setRowCount(len(vista_alumnos))
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

        for fila, (alumno, evaluable_aqui) in enumerate(vista_alumnos):
            item_apellidos = QTableWidgetItem(alumno.apellidos)
            item_nombre = QTableWidgetItem(alumno.nombre)
            item_apellidos.setBackground(COLOR_FONDO_IDENTIDAD)
            item_nombre.setBackground(COLOR_FONDO_IDENTIDAD)
            self.tabla_ra.setItem(fila, 0, item_apellidos)
            self.tabla_ra.setItem(fila, 1, item_nombre)

            if not evaluable_aqui:
                for col in range(2, len(encabezados)):
                    item = QTableWidgetItem("— no evaluado/a aún —" if col == 2 else "")
                    item.setForeground(COLOR_TEXTO_NO_EVALUADO)
                    self.tabla_ra.setItem(fila, col, item)
                item_apellidos.setForeground(COLOR_TEXTO_NO_EVALUADO)
                item_nombre.setForeground(COLOR_TEXTO_NO_EVALUADO)
                continue

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

    def _refrescar_tabla_criterios(self, vista_alumnos, notas_modulo):
        criterios_con_ra = self.base_datos.listar_criterios_de_modulo(self.modulo.id)
        codigos = [self.base_datos.codigo_criterio(ra, criterio) for ra, criterio in criterios_con_ra]
        encabezados = ["Apellidos", "Nombre"] + codigos + ["NOTA FINAL", "CALIFICACIÓN"]
        self.tabla_criterios.setColumnCount(len(encabezados))
        self.tabla_criterios.setRowCount(len(vista_alumnos))
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

        notas_criterio = self.base_datos.calcular_notas_criterios_evaluacion(
            self.evaluacion.id, self.modulo.id
        )

        for fila, (alumno, evaluable_aqui) in enumerate(vista_alumnos):
            item_apellidos = QTableWidgetItem(alumno.apellidos)
            item_nombre = QTableWidgetItem(alumno.nombre)
            item_apellidos.setBackground(COLOR_FONDO_IDENTIDAD)
            item_nombre.setBackground(COLOR_FONDO_IDENTIDAD)
            self.tabla_criterios.setItem(fila, 0, item_apellidos)
            self.tabla_criterios.setItem(fila, 1, item_nombre)

            if not evaluable_aqui:
                for col in range(2, len(encabezados)):
                    item = QTableWidgetItem("— no evaluado/a aún —" if col == 2 else "")
                    item.setForeground(COLOR_TEXTO_NO_EVALUADO)
                    self.tabla_criterios.setItem(fila, col, item)
                item_apellidos.setForeground(COLOR_TEXTO_NO_EVALUADO)
                item_nombre.setForeground(COLOR_TEXTO_NO_EVALUADO)
                continue

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


class PanelEvaluacion(QWidget):
    """Panel de una evaluación parcial: sub-pestañas Calificaciones e
    Instrumentos de Evaluación.
    """

    def __init__(self, base_datos: BaseDatosModulo, modulo: Modulo, evaluacion: Evaluacion):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo
        self.evaluacion = evaluacion

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sub_pestanas = QTabWidget()
        layout.addWidget(self.sub_pestanas)

        self.tabla_calificaciones = TablaCalificaciones(base_datos, modulo, evaluacion)
        self.sub_pestanas.addTab(self.tabla_calificaciones, "📊 Calificaciones")

        self.panel_instrumentos = PanelInstrumentos(base_datos, modulo, evaluacion)
        self.sub_pestanas.addTab(self.panel_instrumentos, "📝 Instrumentos de Evaluación")

        self.sub_pestanas.currentChanged.connect(self._al_cambiar_sub_pestana)

    def _al_cambiar_sub_pestana(self, _indice: int):
        self.tabla_calificaciones.refrescar()

    def refrescar(self):
        self.tabla_calificaciones.refrescar()
        self.panel_instrumentos.refrescar_todo()
