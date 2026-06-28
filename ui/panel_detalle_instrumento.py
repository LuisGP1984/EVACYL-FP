"""
Panel de detalle de un Instrumento de Evaluación (IE), dentro de una
evaluación parcial de un módulo.

Según el tipo de instrumento, muestra una zona de configuración distinta:
  - MANUAL: nada que configurar más allá de los criterios.
  - MEDIA_ARITMETICA: lista de pruebas (nombre), sin pesos.
  - MEDIA_PONDERADA: lista de pruebas con peso (debe sumar 100%).
  - EXAMEN: un campo de "nota máxima".

Debajo, una tabla de notas, igual mecánica que en EVACYL. La diferencia
respecto a EVACYL: los criterios no cuelgan directamente del módulo,
sino de un RA, así que su código se calcula como "numero_RA.letra" y se
listan recorriendo todos los RA del módulo.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
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

from core.database import (
    BaseDatosModulo,
    Evaluacion,
    InstrumentoEvaluacion,
    Modulo,
    TIPO_EXAMEN,
    TIPO_MANUAL,
    TIPO_MEDIA_ARITMETICA,
    TIPO_MEDIA_PONDERADA,
)
from ui.estilos import COLOR_CELDA_IDENTIDAD_GRIS_CLARO
from ui.widgets_comunes import (
    SeccionPlegable,
    TablaConBorrado,
    aplicar_cabeceras_tres_bloques as _aplicar_cabeceras_tres_bloques,
)

COLOR_MANUAL = QColor("#FBEFD3")
COLOR_CALCULADO = QColor("#FFFFFF")
COLOR_FONDO_IDENTIDAD = QColor(COLOR_CELDA_IDENTIDAD_GRIS_CLARO)


class PanelDetalleInstrumento(QWidget):
    def __init__(
        self,
        base_datos: BaseDatosModulo,
        modulo: Modulo,
        instrumento: InstrumentoEvaluacion,
        evaluacion: Evaluacion,
        al_volver,
    ):
        super().__init__()
        self.base_datos = base_datos
        self.modulo = modulo
        self.instrumento = instrumento
        self.evaluacion = evaluacion
        self.al_volver = al_volver
        self._actualizando_desde_codigo = False

        layout_general = QVBoxLayout(self)
        layout_general.setContentsMargins(16, 16, 16, 16)
        layout_general.setSpacing(10)

        cabecera = QHBoxLayout()
        boton_volver = QPushButton("← Volver a Instrumentos")
        boton_volver.setObjectName("botonSecundario")
        boton_volver.clicked.connect(self.al_volver)
        cabecera.addWidget(boton_volver)
        cabecera.addStretch()
        layout_general.addLayout(cabecera)

        titulo = QLabel(f"{instrumento.nombre} — {self._etiqueta_tipo(instrumento.tipo)}")
        titulo.setObjectName("subtitulo")
        layout_general.addWidget(titulo)

        criterios_con_ra = self.base_datos.listar_criterios_de_modulo(self.modulo.id)
        marcados_iniciales = self.base_datos.criterios_marcados_de_instrumento(self.instrumento.id)
        self.seccion_criterios = SeccionPlegable(
            "¿Qué criterios evalúa este instrumento?",
            inicialmente_abierta=(len(marcados_iniciales) == 0),
            altura_maxima_contenido=420,
        )
        self.checks_criterios: dict[int, QCheckBox] = {}
        self.checks_ra: dict[int, QCheckBox] = {}
        self._ra_de_cada_criterio: dict[int, int] = {}  # criterio_id -> ra_id
        self._criterios_de_cada_ra: dict[int, list[int]] = {}  # ra_id -> [criterio_id, ...]
        relaciones_iniciales = {
            ic.criterio_id: ic for ic in self.base_datos.listar_criterios_de_instrumento(self.instrumento.id)
        }
        if not criterios_con_ra:
            self.seccion_criterios.layout_contenido.addWidget(
                QLabel("Este módulo todavía no tiene RA ni criterios definidos.")
            )

        # Agrupar (ra, criterio) por RA, conservando el orden ya dado por
        # listar_criterios_de_modulo (RA en orden, y sus criterios en orden).
        ras_con_sus_criterios: dict[int, tuple] = {}
        for ra, criterio in criterios_con_ra:
            if ra.id not in ras_con_sus_criterios:
                ras_con_sus_criterios[ra.id] = (ra, [])
            ras_con_sus_criterios[ra.id][1].append(criterio)

        for ra_id, (ra, criterios_del_ra) in ras_con_sus_criterios.items():
            self._construir_bloque_ra(ra, criterios_del_ra, marcados_iniciales, relaciones_iniciales)
        layout_general.addWidget(self.seccion_criterios)

        self.seccion_configuracion = SeccionPlegable(
            "Configuración", inicialmente_abierta=(len(marcados_iniciales) == 0)
        )
        self.layout_configuracion = self.seccion_configuracion.layout_contenido
        layout_general.addWidget(self.seccion_configuracion)

        self.tabla_pruebas: QTableWidget | None = None
        self.spin_nota_maxima: QDoubleSpinBox | None = None
        self._construir_zona_configuracion()

        titulo_notas = QLabel("Notas del alumnado")
        titulo_notas.setObjectName("subtitulo")
        layout_general.addWidget(titulo_notas)

        self.tabla_notas = TablaConBorrado()
        self.tabla_notas.setAlternatingRowColors(True)
        self.tabla_notas.itemChanged.connect(self._al_cambiar_celda_notas)
        layout_general.addWidget(self.tabla_notas, stretch=1)

        ayuda_notas = QLabel(
            "Deja la celda vacía si el alumno/a no se ha presentado: no contará en su nota. "
            "Las columnas de criterio en blanco se rellenan automáticamente; si editas una a mano "
            "queda fijada (resaltada) y no se sobrescribirá al recalcular."
        )
        ayuda_notas.setWordWrap(True)
        ayuda_notas.setStyleSheet("color: #8A7A6E;")
        layout_general.addWidget(ayuda_notas)

        if instrumento.tipo == TIPO_MANUAL:
            fila_relleno = QHBoxLayout()
            fila_relleno.addWidget(QLabel("Rellenar todos los criterios de un alumno con:"))
            self.combo_alumno_relleno = QComboBox()
            fila_relleno.addWidget(self.combo_alumno_relleno)
            self.spin_valor_relleno = QDoubleSpinBox()
            self.spin_valor_relleno.setRange(0.0, 10.0)
            self.spin_valor_relleno.setDecimals(2)
            self.spin_valor_relleno.setSingleStep(0.5)
            self.spin_valor_relleno.setValue(5.0)
            fila_relleno.addWidget(self.spin_valor_relleno)
            boton_rellenar = QPushButton("Aplicar a ese alumno/a")
            boton_rellenar.setObjectName("botonSecundario")
            boton_rellenar.clicked.connect(self._rellenar_criterios_manual_para_alumno)
            fila_relleno.addWidget(boton_rellenar)
            fila_relleno.addStretch()
            layout_general.addLayout(fila_relleno)
            self._poblar_combo_relleno()

        boton_restablecer = QPushButton("Restablecer todas las celdas fijadas de este instrumento")
        boton_restablecer.setObjectName("botonSecundario")
        boton_restablecer.clicked.connect(self._restablecer_celdas_fijadas)
        layout_general.addWidget(boton_restablecer)

        self._refrescar_tabla_notas()

    def _construir_bloque_ra(self, ra, criterios_del_ra, marcados_iniciales, relaciones_iniciales):
        """Construye, dentro de la sección de criterios, un bloque por RA:
        un checkbox de RA arriba (marca/desmarca todos sus criterios de
        golpe) y, plegada dentro, la lista de criterios individuales por
        si el docente quiere afinar cuáles marcar.
        """
        ids_criterios_ra = [c.id for c in criterios_del_ra]
        self._criterios_de_cada_ra[ra.id] = ids_criterios_ra
        for cid in ids_criterios_ra:
            self._ra_de_cada_criterio[cid] = ra.id
        todos_marcados = all(cid in marcados_iniciales for cid in ids_criterios_ra)
        ninguno_marcado = not any(cid in marcados_iniciales for cid in ids_criterios_ra)

        fila_ra = QHBoxLayout()
        check_ra = QCheckBox(f"RA{ra.numero}" + (f" — {ra.descripcion}" if ra.descripcion else ""))
        check_ra.setProperty("es_check_ra", True)
        check_ra.setTristate(True)
        if todos_marcados:
            check_ra.setCheckState(Qt.CheckState.Checked)
        elif ninguno_marcado:
            check_ra.setCheckState(Qt.CheckState.Unchecked)
        else:
            check_ra.setCheckState(Qt.CheckState.PartiallyChecked)
        # Qt, con tristate activo, cicla Unchecked -> PartiallyChecked ->
        # Checked -> Unchecked... en cada clic del ratón. Eso significa
        # que el primer clic sobre un RA recién creado (estado inicial
        # Unchecked) lo deja en PartiallyChecked, no en Checked, así que
        # no marcaría ningún criterio. El estado "parcial" solo debe
        # poder MOSTRARSE (calculado desde los criterios reales), nunca
        # ser el resultado directo de un clic; por eso aquí se fuerza a
        # saltarlo cuando el cambio viene de la interacción del usuario.
        check_ra.stateChanged.connect(
            lambda _estado, ra_id=ra.id, ids=ids_criterios_ra: self._alternar_ra(ra_id, ids)
        )
        self.checks_ra[ra.id] = check_ra
        fila_ra.addWidget(check_ra)
        fila_ra.addStretch()
        self.seccion_criterios.layout_contenido.addLayout(fila_ra)

        sub_seccion = SeccionPlegable(
            f"Ver criterios individuales de RA{ra.numero} ({len(criterios_del_ra)})",
            inicialmente_abierta=False,
            altura_maxima_contenido=280,
        )
        for criterio in criterios_del_ra:
            codigo = self.base_datos.codigo_criterio(ra, criterio)
            fila_criterio = QHBoxLayout()
            check = QCheckBox(f"{codigo}  (peso en RA{ra.numero}: {criterio.peso:g})")
            marcado = criterio.id in marcados_iniciales
            check.setChecked(marcado)
            check.stateChanged.connect(
                lambda _estado, criterio_id=criterio.id: self._alternar_criterio(criterio_id)
            )
            self.checks_criterios[criterio.id] = check
            fila_criterio.addWidget(check)
            fila_criterio.addStretch()

            sub_seccion.layout_contenido.addLayout(fila_criterio)

        self.seccion_criterios.layout_contenido.addWidget(sub_seccion)

    def _alternar_ra(self, ra_id: int, ids_criterios: list[int]):
        """Al marcar/desmarcar el checkbox de un RA, aplica ese mismo
        estado a todos sus criterios individuales de golpe.

        Qt, con tristate activo, cicla Unchecked -> PartiallyChecked ->
        Checked -> Unchecked en cada clic. Si el clic deja el checkbox en
        PartiallyChecked, lo forzamos a Checked (un RA recién pulsado
        nunca debe quedar a medias por culpa del ciclo de tres estados;
        el estado parcial solo se usa para MOSTRAR la situación real
        tras tocar criterios individuales, no como destino de un clic).
        """
        check_ra = self.checks_ra[ra_id]
        if check_ra.checkState() == Qt.CheckState.PartiallyChecked:
            check_ra.blockSignals(True)
            check_ra.setCheckState(Qt.CheckState.Checked)
            check_ra.blockSignals(False)
        marcar_todos = check_ra.checkState() == Qt.CheckState.Checked
        for criterio_id in ids_criterios:
            check_criterio = self.checks_criterios.get(criterio_id)
            if check_criterio is None:
                continue
            if check_criterio.isChecked() != marcar_todos:
                check_criterio.setChecked(marcar_todos)  # esto ya dispara _alternar_criterio

    @staticmethod
    def _etiqueta_tipo(tipo: str) -> str:
        return {
            TIPO_MANUAL: "Manual",
            TIPO_MEDIA_ARITMETICA: "Varias pruebas — media aritmética",
            TIPO_MEDIA_PONDERADA: "Varias pruebas — media ponderada",
            TIPO_EXAMEN: "Examen",
        }.get(tipo, tipo)

    def _criterios_marcados_ordenados(self):
        criterios_con_ra = self.base_datos.listar_criterios_de_modulo(self.modulo.id)
        marcados = self.base_datos.criterios_marcados_de_instrumento(self.instrumento.id)
        resultado = []
        for ra, criterio in criterios_con_ra:
            if criterio.id in marcados:
                codigo = self.base_datos.codigo_criterio(ra, criterio)
                resultado.append((codigo, criterio.id))
        return resultado

    def _alternar_criterio(self, criterio_id: int):
        check = self.checks_criterios[criterio_id]
        if check.isChecked():
            # El peso de partida no importa: marcar_criterio_en_instrumento
            # recalcula inmediatamente el peso real de todos los criterios
            # de su mismo RA marcados en este instrumento (redistribución
            # automática a partir del peso de cada criterio en su RA).
            self.base_datos.marcar_criterio_en_instrumento(self.instrumento.id, criterio_id)
        else:
            self.base_datos.desmarcar_criterio_en_instrumento(self.instrumento.id, criterio_id)
        if self.instrumento.tipo == TIPO_MANUAL:
            self._refrescar_tabla_notas()
        else:
            self._recalcular_y_refrescar()
        self._sincronizar_check_ra_de(criterio_id)

    def _sincronizar_check_ra_de(self, criterio_id: int):
        """Tras marcar/desmarcar un criterio individual, actualiza el
        estado visual (marcado/desmarcado/parcial) del checkbox de su RA
        padre, sin volver a disparar _alternar_ra (que recorrería de
        nuevo todos sus criterios sin necesidad).
        """
        ra_id = self._ra_de_cada_criterio.get(criterio_id)
        if ra_id is None:
            return
        check_ra = self.checks_ra.get(ra_id)
        if check_ra is None:
            return
        ids_criterios = self._criterios_de_cada_ra.get(ra_id, [])
        marcados = [self.checks_criterios[cid].isChecked() for cid in ids_criterios if cid in self.checks_criterios]
        check_ra.blockSignals(True)
        if all(marcados):
            check_ra.setCheckState(Qt.CheckState.Checked)
        elif not any(marcados):
            check_ra.setCheckState(Qt.CheckState.Unchecked)
        else:
            check_ra.setCheckState(Qt.CheckState.PartiallyChecked)
        check_ra.blockSignals(False)

    def _construir_zona_configuracion(self):
        tipo = self.instrumento.tipo

        if tipo == TIPO_MANUAL:
            self.layout_configuracion.addWidget(
                QLabel("Sin configuración adicional: introduce la nota directamente por criterio.")
            )
            return

        if tipo == TIPO_EXAMEN:
            fila = QHBoxLayout()
            fila.addWidget(QLabel("Nota máxima del examen:"))
            self.spin_nota_maxima = QDoubleSpinBox()
            self.spin_nota_maxima.setRange(0.1, 1000.0)
            self.spin_nota_maxima.setDecimals(2)
            self.spin_nota_maxima.setValue(self.instrumento.nota_maxima)
            self.spin_nota_maxima.valueChanged.connect(self._al_cambiar_nota_maxima)
            fila.addWidget(self.spin_nota_maxima)
            fila.addStretch()
            self.layout_configuracion.addLayout(fila)
            return

        es_ponderada = tipo == TIPO_MEDIA_PONDERADA
        self.tabla_pruebas = TablaConBorrado()
        columnas = ["Nombre de la prueba", "Peso (%)"] if es_ponderada else ["Nombre de la prueba"]
        self.tabla_pruebas.setColumnCount(len(columnas))
        self.tabla_pruebas.setHorizontalHeaderLabels(columnas)
        self.tabla_pruebas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_pruebas.itemChanged.connect(self._al_cambiar_celda_prueba)
        self.layout_configuracion.addWidget(self.tabla_pruebas)

        self.etiqueta_suma_pesos_pruebas = QLabel("")
        if es_ponderada:
            self.layout_configuracion.addWidget(self.etiqueta_suma_pesos_pruebas)

        fila_botones = QHBoxLayout()
        boton_anadir_prueba = QPushButton("Añadir prueba")
        boton_anadir_prueba.clicked.connect(self._anadir_prueba)
        fila_botones.addWidget(boton_anadir_prueba)
        boton_quitar_prueba = QPushButton("Quitar prueba seleccionada")
        boton_quitar_prueba.setObjectName("botonPeligro")
        boton_quitar_prueba.clicked.connect(self._quitar_prueba_seleccionada)
        fila_botones.addWidget(boton_quitar_prueba)
        fila_botones.addStretch()
        self.layout_configuracion.addLayout(fila_botones)

        self._refrescar_tabla_pruebas()

    def _al_cambiar_nota_maxima(self, valor: float):
        self.base_datos.actualizar_instrumento(
            self.instrumento.id, self.instrumento.nombre, self.instrumento.peso, valor
        )
        self.instrumento.nota_maxima = valor
        self._recalcular_y_refrescar()

    def _refrescar_tabla_pruebas(self):
        self._actualizando_desde_codigo = True
        pruebas = self.base_datos.listar_pruebas(self.instrumento.id)
        self.tabla_pruebas.setRowCount(len(pruebas))
        es_ponderada = self.instrumento.tipo == TIPO_MEDIA_PONDERADA
        for fila, prueba in enumerate(pruebas):
            item_nombre = QTableWidgetItem(prueba.nombre)
            item_nombre.setData(Qt.ItemDataRole.UserRole, prueba.id)
            self.tabla_pruebas.setItem(fila, 0, item_nombre)
            if es_ponderada:
                item_peso = QTableWidgetItem(str(prueba.peso))
                self.tabla_pruebas.setItem(fila, 1, item_peso)
        self._actualizando_desde_codigo = False

        if es_ponderada:
            suma = self.base_datos.suma_pesos_pruebas(self.instrumento.id)
            if abs(suma - 100.0) < 0.01:
                self.etiqueta_suma_pesos_pruebas.setText(f"Suma de pesos: {suma:.1f}% ✓")
                self.etiqueta_suma_pesos_pruebas.setStyleSheet("color: #0DAB6C; font-weight: bold;")
            else:
                self.etiqueta_suma_pesos_pruebas.setText(
                    f"⚠ Suma de pesos: {suma:.1f}% — debe sumar 100% entre todas las pruebas."
                )
                self.etiqueta_suma_pesos_pruebas.setStyleSheet("color: #B23B3B; font-weight: bold;")

    def _al_cambiar_celda_prueba(self, item: QTableWidgetItem):
        if self._actualizando_desde_codigo:
            return
        fila = item.row()
        item_nombre = self.tabla_pruebas.item(fila, 0)
        if item_nombre is None:
            return
        prueba_id = item_nombre.data(Qt.ItemDataRole.UserRole)
        if prueba_id is None:
            return
        nombre = item_nombre.text()
        peso = 0.0
        if self.instrumento.tipo == TIPO_MEDIA_PONDERADA:
            item_peso = self.tabla_pruebas.item(fila, 1)
            texto_peso = item_peso.text() if item_peso else "0"
            try:
                peso = float(texto_peso.replace(",", "."))
            except ValueError:
                peso = 0.0
        try:
            self.base_datos.actualizar_prueba(prueba_id, nombre, peso)
        except ValueError as exc:
            QMessageBox.warning(self, "Dato no válido", str(exc))
        self._refrescar_tabla_pruebas()
        self._recalcular_y_refrescar()

    def _anadir_prueba(self):
        self.base_datos.agregar_prueba(self.instrumento.id)
        self._refrescar_tabla_pruebas()
        self._refrescar_tabla_notas()

    def _quitar_prueba_seleccionada(self):
        fila = self.tabla_pruebas.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Sin selección", "Selecciona primero una prueba.")
            return
        item_nombre = self.tabla_pruebas.item(fila, 0)
        prueba_id = item_nombre.data(Qt.ItemDataRole.UserRole) if item_nombre else None
        if prueba_id is None:
            return
        self.base_datos.eliminar_prueba(prueba_id)
        self._refrescar_tabla_pruebas()
        self._recalcular_y_refrescar()

    def _refrescar_tabla_notas(self):
        tipo = self.instrumento.tipo
        criterios_marcados = self._criterios_marcados_ordenados()
        vista_alumnos = self.base_datos.listar_alumnos_para_evaluacion(
            self.modulo.id, self.evaluacion.orden
        )

        self._actualizando_desde_codigo = True

        if tipo in (TIPO_MEDIA_ARITMETICA, TIPO_MEDIA_PONDERADA):
            pruebas = self.base_datos.listar_pruebas(self.instrumento.id)
            columnas_previas = [p.nombre for p in pruebas]
            self._pruebas_actuales = pruebas
        elif tipo == TIPO_EXAMEN:
            columnas_previas = [f"Nota cruda (sobre {self.instrumento.nota_maxima:g})"]
            self._pruebas_actuales = []
        else:
            columnas_previas = []
            self._pruebas_actuales = []

        columnas_criterio = [codigo for codigo, _cid in criterios_marcados]
        encabezados = ["Apellidos", "Nombre"] + columnas_previas + columnas_criterio
        self.tabla_notas.setColumnCount(len(encabezados))
        col_inicio_criterios_cabecera = 2 + len(columnas_previas)
        _aplicar_cabeceras_tres_bloques(
            self.tabla_notas, encabezados,
            col_inicio_datos_entrada=2,
            col_inicio_criterios=col_inicio_criterios_cabecera,
        )
        self.tabla_notas.setRowCount(len(vista_alumnos))

        notas_pruebas = self.base_datos.obtener_notas_pruebas(self.instrumento.id) if self._pruebas_actuales else {}
        notas_instrumento = self.base_datos.obtener_notas_instrumento(self.instrumento.id)
        notas_criterio = self.base_datos.obtener_notas_criterio_instrumento(self.instrumento.id)

        col_inicio_previas = 2
        col_inicio_criterios = 2 + len(columnas_previas)

        for fila, (alumno, evaluable_aqui) in enumerate(vista_alumnos):
            item_apellidos = QTableWidgetItem(alumno.apellidos)
            item_apellidos.setData(Qt.ItemDataRole.UserRole, alumno.id)
            item_apellidos.setFlags(item_apellidos.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_apellidos.setBackground(COLOR_FONDO_IDENTIDAD)
            item_nombre = QTableWidgetItem(alumno.nombre)
            item_nombre.setFlags(item_nombre.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_nombre.setBackground(COLOR_FONDO_IDENTIDAD)
            self.tabla_notas.setItem(fila, 0, item_apellidos)
            self.tabla_notas.setItem(fila, 1, item_nombre)

            if not evaluable_aqui:
                for col in range(2, len(encabezados)):
                    item_vacio = QTableWidgetItem("")
                    item_vacio.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.tabla_notas.setItem(fila, col, item_vacio)
                continue

            if tipo in (TIPO_MEDIA_ARITMETICA, TIPO_MEDIA_PONDERADA):
                for indice_prueba, prueba in enumerate(self._pruebas_actuales):
                    valor = notas_pruebas.get((prueba.id, alumno.id))
                    item = QTableWidgetItem("" if valor is None else self._formatear(valor))
                    item.setData(Qt.ItemDataRole.UserRole, ("prueba", prueba.id))
                    self.tabla_notas.setItem(fila, col_inicio_previas + indice_prueba, item)
            elif tipo == TIPO_EXAMEN:
                valor = notas_instrumento.get(alumno.id)
                item = QTableWidgetItem("" if valor is None else self._formatear(valor))
                item.setData(Qt.ItemDataRole.UserRole, ("instrumento", self.instrumento.id))
                self.tabla_notas.setItem(fila, col_inicio_previas, item)

            for indice_criterio, (_codigo, criterio_id) in enumerate(criterios_marcados):
                valor, es_manual = notas_criterio.get((criterio_id, alumno.id), (None, False))
                if tipo == TIPO_MANUAL:
                    item = QTableWidgetItem("" if valor is None else self._formatear(valor))
                    item.setData(Qt.ItemDataRole.UserRole, ("criterio_manual", criterio_id))
                else:
                    item = QTableWidgetItem("" if valor is None else self._formatear(valor))
                    item.setData(Qt.ItemDataRole.UserRole, ("criterio_calculado", criterio_id))
                if es_manual:
                    item.setBackground(COLOR_MANUAL)
                self.tabla_notas.setItem(fila, col_inicio_criterios + indice_criterio, item)

        cabecera = self.tabla_notas.horizontalHeader()
        # Se ajusta primero al contenido (ResizeToContents) para calcular
        # un ancho adecuado, y luego se deja en modo Interactive: así el
        # docente puede seguir arrastrando el borde para ensancharla o
        # estrecharla a mano si lo prefiere, en vez de quedar bloqueada.
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        ancho_apellidos = max(self.tabla_notas.columnWidth(0), 110)
        ancho_nombre = max(self.tabla_notas.columnWidth(1), 90)
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.tabla_notas.setColumnWidth(0, ancho_apellidos)
        self.tabla_notas.setColumnWidth(1, ancho_nombre)
        for col in range(2, self.tabla_notas.columnCount()):
            cabecera.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.tabla_notas.setColumnWidth(col, 78)
        self._actualizando_desde_codigo = False

    @staticmethod
    def _formatear(valor: float) -> str:
        texto = f"{valor:.2f}".rstrip("0").rstrip(".")
        return texto if texto else "0"

    def _al_cambiar_celda_notas(self, item: QTableWidgetItem):
        if self._actualizando_desde_codigo:
            return
        datos = item.data(Qt.ItemDataRole.UserRole)
        if datos is None:
            return
        clase, identificador = datos
        fila = item.row()
        item_apellidos = self.tabla_notas.item(fila, 0)
        alumno_id = item_apellidos.data(Qt.ItemDataRole.UserRole) if item_apellidos else None
        if alumno_id is None:
            return

        texto = item.text().strip()
        valor = None
        if texto != "":
            try:
                valor = float(texto.replace(",", "."))
            except ValueError:
                QMessageBox.warning(self, "Nota no válida", "Escribe un número, o deja la celda vacía si no se presentó.")
                self._refrescar_tabla_notas()
                return

            limite_superior = self.instrumento.nota_maxima if clase == "instrumento" else 10.0
            if valor < 0.0 or valor > limite_superior:
                QMessageBox.warning(
                    self,
                    "Nota fuera de rango",
                    f"La nota debe estar entre 0 y {limite_superior:g}. No se ha guardado el valor.",
                )
                self._refrescar_tabla_notas()
                return

        if clase == "prueba":
            self.base_datos.guardar_nota_prueba(identificador, alumno_id, valor)
            self._recalcular_y_refrescar()
        elif clase == "instrumento":
            self.base_datos.guardar_nota_instrumento(identificador, alumno_id, valor)
            self._recalcular_y_refrescar()
        elif clase == "criterio_manual":
            self.base_datos.guardar_nota_criterio_instrumento(
                self.instrumento.id, identificador, alumno_id, valor, es_manual=(valor is not None)
            )
            self._refrescar_tabla_notas()
        elif clase == "criterio_calculado":
            if valor is None:
                self.base_datos.guardar_nota_criterio_instrumento(
                    self.instrumento.id, identificador, alumno_id, None, es_manual=False
                )
                self._recalcular_y_refrescar()
            else:
                self.base_datos.guardar_nota_criterio_instrumento(
                    self.instrumento.id, identificador, alumno_id, valor, es_manual=True
                )
                self._refrescar_tabla_notas()

    def _recalcular_y_refrescar(self):
        self.base_datos.recalcular_notas_criterio_para_instrumento(self.instrumento)
        self._refrescar_tabla_notas()

    def _poblar_combo_relleno(self):
        self.combo_alumno_relleno.clear()
        vista_alumnos = self.base_datos.listar_alumnos_para_evaluacion(
            self.modulo.id, self.evaluacion.orden
        )
        for alumno, evaluable_aqui in vista_alumnos:
            if not evaluable_aqui:
                continue
            etiqueta = f"{alumno.apellidos}, {alumno.nombre}".strip(", ")
            self.combo_alumno_relleno.addItem(etiqueta, alumno.id)

    def _rellenar_criterios_manual_para_alumno(self):
        alumno_id = self.combo_alumno_relleno.currentData()
        if alumno_id is None:
            QMessageBox.information(self, "Sin alumnado", "No hay alumnado disponible en esta evaluación.")
            return
        valor = self.spin_valor_relleno.value()
        criterios_marcados = self.base_datos.criterios_marcados_de_instrumento(self.instrumento.id)
        if not criterios_marcados:
            QMessageBox.information(
                self, "Sin criterios", "Marca primero qué criterios evalúa este instrumento."
            )
            return
        for criterio_id in criterios_marcados:
            self.base_datos.guardar_nota_criterio_instrumento(
                self.instrumento.id, criterio_id, alumno_id, valor, es_manual=False
            )
        self._refrescar_tabla_notas()

    def _restablecer_celdas_fijadas(self):
        respuesta = QMessageBox.question(
            self,
            "Restablecer celdas fijadas",
            "Esto eliminará todas las ediciones manuales de criterio en este instrumento "
            "y volverá a calcular sus valores automáticamente. ¿Continuar?",
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        notas_actuales = self.base_datos.obtener_notas_criterio_instrumento(self.instrumento.id)
        for (criterio_id, alumno_id), (_valor, es_manual) in notas_actuales.items():
            if es_manual:
                self.base_datos.guardar_nota_criterio_instrumento(
                    self.instrumento.id, criterio_id, alumno_id, None, es_manual=False
                )
        if self.instrumento.tipo == TIPO_MANUAL:
            self._refrescar_tabla_notas()
        else:
            self._recalcular_y_refrescar()
