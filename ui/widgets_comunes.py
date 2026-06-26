"""
Widgets reutilizables compartidos por varios paneles de la interfaz.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.estilos import (
    COLOR_CABECERA_CRITERIO_ROJO,
    COLOR_CABECERA_DATOS,
    COLOR_CABECERA_DATOS_NARANJA,
    COLOR_CABECERA_IDENTIDAD,
    COLOR_CABECERA_IDENTIDAD_GRIS,
    COLOR_CABECERA_RESULTADO,
)
from core.rutas_app import ruta_raiz_proyecto

RUTA_IMAGEN_FONDO = ruta_raiz_proyecto() / "recursos" / "fondo.png"


class TablaConBorrado(QTableWidget):
    """QTableWidget normal, salvo que las teclas Supr/Backspace vacían el
    texto de las celdas seleccionadas. Por defecto, Qt solo vacía una celda
    con esas teclas si está en modo edición (doble clic o F2); aquí se
    soporta también pulsando Supr directamente con la celda seleccionada.
    """

    def keyPressEvent(self, evento):
        if evento.matches(QKeySequence.StandardKey.Delete) or evento.key() in (
            Qt.Key.Key_Delete,
            Qt.Key.Key_Backspace,
        ):
            for item in self.selectedItems():
                if item.flags() & Qt.ItemFlag.ItemIsEditable:
                    item.setText("")
            return
        super().keyPressEvent(evento)


class VentanaConFondo(QMainWindow):
    """QMainWindow que pinta recursos/fondo.png como fondo, escalada para
    cubrir toda la ventana y centrada (estilo "cover", como en CSS). Si el
    archivo no existe, se comporta como una QMainWindow normal sin fondo.

    Los widgets normales de la ventana (botones, tablas, etc.) se pintan
    encima sin más, porque viven en el central widget habitual; solo hay
    que evitar darle a ese central widget un color de fondo opaco para que
    se vea la imagen detrás. Por eso las ventanas que usan este fondo
    deben usar el objectName "fondoTransparente" en su widget central.
    """

    _pixmap_fondo: QPixmap | None = None
    _intento_carga_realizado = False

    def __init__(self):
        super().__init__()
        self._cargar_pixmap_fondo()

    @classmethod
    def _cargar_pixmap_fondo(cls):
        if cls._intento_carga_realizado:
            return
        cls._intento_carga_realizado = True
        if RUTA_IMAGEN_FONDO.exists():
            pixmap = QPixmap(str(RUTA_IMAGEN_FONDO))
            if not pixmap.isNull():
                cls._pixmap_fondo = pixmap

    def paintEvent(self, evento):
        if self._pixmap_fondo is not None:
            painter = QPainter(self)
            pixmap_escalado = self._pixmap_fondo.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - pixmap_escalado.width()) // 2
            y = (self.height() - pixmap_escalado.height()) // 2
            painter.drawPixmap(x, y, pixmap_escalado)
            painter.end()
        super().paintEvent(evento)


def aplicar_cabeceras_por_bloque(
    tabla: QTableWidget,
    encabezados: list[str],
    col_inicio_resultado: int,
    col_inicio_datos: int = 2,
):
    """Construye la fila de cabecera de una QTableWidget con un color de
    fondo distinto según el bloque de columnas: identidad del alumno
    (columnas antes de col_inicio_datos, normalmente Apellidos y Nombre),
    datos intermedios (criterios, pruebas o instrumentos) y resultado
    final (a partir de col_inicio_resultado) — para que se distingan a
    simple vista incluso con muchas columnas de criterio.
    """
    for col, texto in enumerate(encabezados):
        item = QTableWidgetItem(texto)
        if col < col_inicio_datos:
            color = COLOR_CABECERA_IDENTIDAD
        elif col >= col_inicio_resultado:
            color = COLOR_CABECERA_RESULTADO
        else:
            color = COLOR_CABECERA_DATOS
        item.setBackground(QColor(color))
        item.setForeground(QColor("#FFFFFF"))
        fuente = item.font()
        fuente.setBold(True)
        item.setFont(fuente)
        tabla.setHorizontalHeaderItem(col, item)


def aplicar_cabeceras_tres_bloques(
    tabla: QTableWidget,
    encabezados: list[str],
    col_inicio_datos_entrada: int,
    col_inicio_criterios: int,
):
    """Variante de aplicar_cabeceras_por_bloque con TRES colores bien
    diferenciados, pensada para la tabla de notas dentro de un
    instrumento: identidad del alumno en gris, datos de entrada
    (pruebas o nota cruda de examen) en azul, y resultado por criterio
    en verde.
    """
    for col, texto in enumerate(encabezados):
        item = QTableWidgetItem(texto)
        if col < col_inicio_datos_entrada:
            color = COLOR_CABECERA_IDENTIDAD_GRIS
        elif col < col_inicio_criterios:
            color = COLOR_CABECERA_DATOS_NARANJA
        else:
            color = COLOR_CABECERA_CRITERIO_ROJO
        item.setBackground(QColor(color))
        item.setForeground(QColor("#FFFFFF"))
        fuente = item.font()
        fuente.setBold(True)
        item.setFont(fuente)
        tabla.setHorizontalHeaderItem(col, item)


class BotonAyuda(QPushButton):
    """Botón con forma de "❓" que, al pulsarlo, muestra un cuadro de
    diálogo explicando qué se puede hacer en la pantalla/pestaña actual.
    Pensado para colocarse en la esquina de cualquier panel.
    """

    def __init__(self, titulo: str, texto_ayuda: str, parent=None):
        super().__init__("❓ Ayuda", parent)
        self.setObjectName("botonAyuda")
        self._titulo = titulo
        self._texto_ayuda = texto_ayuda
        self.setToolTip("Qué puedes hacer en esta pantalla")
        self.clicked.connect(self._mostrar_ayuda)

    def _mostrar_ayuda(self):
        QMessageBox.information(self, self._titulo, self._texto_ayuda)


class SeccionPlegable(QWidget):
    """Contenedor con una cabecera-botón (▸/▾ + título) que muestra u
    oculta el contenido al pulsarla. Pensado para liberar espacio
    vertical en pantallas con poco sitio (por ejemplo, para no empujar
    hacia abajo una tabla larga de alumnado).

    El contenido desplegado tiene su propio scroll interno con una altura
    máxima limitada: si hay pocos elementos no se nota ningún scroll de
    sobra, pero si hay muchos (por ejemplo, 20-30 criterios) no se cortan
    sin poder llegar a ellos — el scroll queda contenido dentro de la
    propia sección, sin tener que envolver toda la pantalla.

    Uso:
        seccion = SeccionPlegable("¿Qué criterios evalúa?", inicialmente_abierta=True)
        seccion.layout_contenido.addWidget(mi_checkbox)
        ...
        layout_padre.addWidget(seccion)
    """

    def __init__(
        self,
        titulo: str,
        inicialmente_abierta: bool = True,
        altura_maxima_contenido: int = 220,
        parent=None,
    ):
        super().__init__(parent)
        self._abierta = inicialmente_abierta

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        self.boton_cabecera = QPushButton()
        self.boton_cabecera.setObjectName("botonSeccionPlegable")
        self.boton_cabecera.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_cabecera.clicked.connect(self._alternar)
        layout_raiz.addWidget(self.boton_cabecera)

        self.scroll_contenido = QScrollArea()
        self.scroll_contenido.setWidgetResizable(True)
        self.scroll_contenido.setMaximumHeight(altura_maxima_contenido)
        self.scroll_contenido.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_contenido.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_contenido.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.contenedor_contenido = QWidget()
        self.layout_contenido = QVBoxLayout(self.contenedor_contenido)
        self.layout_contenido.setContentsMargins(12, 8, 12, 12)
        self.scroll_contenido.setWidget(self.contenedor_contenido)
        layout_raiz.addWidget(self.scroll_contenido)

        self._titulo_base = titulo
        self._actualizar_texto_boton()
        self.scroll_contenido.setVisible(self._abierta)

    def _actualizar_texto_boton(self):
        flecha = "▾" if self._abierta else "▸"
        self.boton_cabecera.setText(f"{flecha}  {self._titulo_base}")

    def _alternar(self):
        self._abierta = not self._abierta
        self.scroll_contenido.setVisible(self._abierta)
        self._actualizar_texto_boton()

    def establecer_abierta(self, abierta: bool):
        self._abierta = abierta
        self.scroll_contenido.setVisible(abierta)
        self._actualizar_texto_boton()

    def esta_abierta(self) -> bool:
        return self._abierta
