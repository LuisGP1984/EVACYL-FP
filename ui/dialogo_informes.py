"""
Diálogo para generar el informe de calificaciones de un alumno (o de
toda la clase de golpe), en PDF o en Word, para una evaluación parcial
o para FINAL.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from core.database import BaseDatosModulo, Evaluacion, Modulo
from core.informe_alumno import recopilar_informe_completo, recopilar_informe_evaluacion, recopilar_informe_final
from core.informe_docx import (
    generar_informe_completo_docx,
    generar_informe_evaluacion_docx,
    generar_informe_final_docx,
)
from core.informe_pdf import generar_informe_completo_pdf, generar_informe_evaluacion_pdf, generar_informe_final_pdf

OPCION_TODOS = "__TODOS__"


def _nombre_archivo_seguro(texto: str) -> str:
    caracteres_invalidos = '<>:"/\\|?*'
    limpio = "".join(c if c not in caracteres_invalidos else "_" for c in texto)
    return limpio.strip()


class DialogoGenerarInformes(QDialog):
    """Diálogo genérico: pide alumno (o todos), formato, y carpeta de
    destino, y delega la generación real en las funciones que se le
    pasen al construirlo (distintas para evaluación parcial y FINAL).
    """

    def __init__(
        self,
        titulo: str,
        lista_alumnos: list[tuple[int, str]],
        funcion_generar_uno,
        parent=None,
    ):
        """funcion_generar_uno(alumno_id, formato, carpeta_destino) -> Path | None
        formato es "pdf" o "docx". Debe devolver la ruta generada, o None
        si ese alumno no tiene informe que generar (por ejemplo, no es
        evaluable en esta evaluación).
        """
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(420)
        self._lista_alumnos = lista_alumnos
        self._funcion_generar_uno = funcion_generar_uno

        layout = QVBoxLayout(self)

        explicacion = QLabel(
            "Genera un informe de calificaciones para un alumno, pensado para que él o su "
            "familia entiendan de dónde sale cada nota (útil también de cara a reclamaciones)."
        )
        explicacion.setWordWrap(True)
        layout.addWidget(explicacion)

        formulario = QFormLayout()

        self.combo_alumno = QComboBox()
        self.combo_alumno.addItem("👥 Toda la clase (un archivo por alumno)", OPCION_TODOS)
        for alumno_id, etiqueta in lista_alumnos:
            self.combo_alumno.addItem(etiqueta, alumno_id)
        formulario.addRow("Alumno/a:", self.combo_alumno)

        contenedor_formato = QWidget()
        layout_formato = QVBoxLayout(contenedor_formato)
        layout_formato.setContentsMargins(0, 0, 0, 0)
        self.radio_pdf = QRadioButton("PDF (recomendado para entregar)")
        self.radio_pdf.setChecked(True)
        self.radio_docx = QRadioButton("Word (.docx, editable)")
        layout_formato.addWidget(self.radio_pdf)
        layout_formato.addWidget(self.radio_docx)
        formulario.addRow("Formato:", contenedor_formato)

        layout.addLayout(formulario)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Generar")
        botones.accepted.connect(self._al_aceptar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _al_aceptar(self):
        seleccion = self.combo_alumno.currentData()
        formato = "pdf" if self.radio_pdf.isChecked() else "docx"

        carpeta_destino = QFileDialog.getExistingDirectory(
            self, "Elige la carpeta donde guardar el informe"
        )
        if not carpeta_destino:
            return
        carpeta_destino = Path(carpeta_destino)

        try:
            if seleccion == OPCION_TODOS:
                generados = 0
                omitidos = 0
                for alumno_id, _etiqueta in self._lista_alumnos:
                    ruta = self._funcion_generar_uno(alumno_id, formato, carpeta_destino)
                    if ruta is not None:
                        generados += 1
                    else:
                        omitidos += 1
                mensaje = f"Se han generado {generados} informes en:\n{carpeta_destino}"
                if omitidos:
                    mensaje += f"\n\n({omitidos} alumnos/as omitidos: no evaluables en esta evaluación.)"
                QMessageBox.information(self, "Informes generados", mensaje)
            else:
                ruta = self._funcion_generar_uno(seleccion, formato, carpeta_destino)
                if ruta is None:
                    QMessageBox.warning(
                        self, "No se pudo generar",
                        "Ese alumno/a no es evaluable en esta evaluación todavía.",
                    )
                    return
                QMessageBox.information(self, "Informe generado", f"Archivo guardado en:\n{ruta}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error al generar el informe", str(exc))
            return

        self.accept()


def generar_informe_evaluacion_individual(
    base_datos: BaseDatosModulo, modulo: Modulo, evaluacion: Evaluacion,
    alumno_id: int, formato: str, carpeta_destino: Path,
) -> Path | None:
    informe = recopilar_informe_evaluacion(base_datos, modulo, evaluacion, alumno_id)
    if informe is None:
        return None
    nombre_base = _nombre_archivo_seguro(
        f"Informe {evaluacion.nombre} - {informe.apellidos_alumno} {informe.nombre_alumno}"
    )
    if formato == "pdf":
        return generar_informe_evaluacion_pdf(informe, carpeta_destino / f"{nombre_base}.pdf")
    return generar_informe_evaluacion_docx(informe, carpeta_destino / f"{nombre_base}.docx")


def generar_informe_final_individual(
    base_datos: BaseDatosModulo, modulo: Modulo, alumno_id: int, formato: str, carpeta_destino: Path,
) -> Path | None:
    informe = recopilar_informe_final(base_datos, modulo, alumno_id)
    if informe is None:
        return None
    nombre_base = _nombre_archivo_seguro(
        f"Informe FINAL - {informe.apellidos_alumno} {informe.nombre_alumno}"
    )
    if formato == "pdf":
        return generar_informe_final_pdf(informe, carpeta_destino / f"{nombre_base}.pdf")
    return generar_informe_final_docx(informe, carpeta_destino / f"{nombre_base}.docx")


def generar_informe_completo_individual(
    base_datos: BaseDatosModulo, modulo: Modulo, alumno_id: int, formato: str, carpeta_destino: Path,
) -> Path | None:
    """Genera un único documento con todas las evaluaciones parciales
    evaluables + FINAL, como secciones del mismo archivo."""
    informe = recopilar_informe_completo(base_datos, modulo, alumno_id)
    if informe is None:
        return None
    nombre_base = _nombre_archivo_seguro(
        f"Informe completo - {informe.apellidos_alumno} {informe.nombre_alumno}"
    )
    if formato == "pdf":
        return generar_informe_completo_pdf(informe, carpeta_destino / f"{nombre_base}.pdf")
    return generar_informe_completo_docx(informe, carpeta_destino / f"{nombre_base}.docx")
