"""
Generación del informe individual de un alumno en PDF, a partir de las
estructuras recopiladas en core/informe_alumno.py. Incluye la nota por
RA (prioritaria para el profesorado de FP) y el detalle por criterio.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.informe_alumno import InformeAlumno, InformeAlumnoCompleto, InformeAlumnoFinal

COLOR_CABECERA = colors.HexColor("#E22B10")
COLOR_RESULTADO = colors.HexColor("#7A1B08")
COLOR_FILA_ALTERNA = colors.HexColor("#FDF3E7")

_estilos_base = getSampleStyleSheet()

ESTILO_TITULO = ParagraphStyle(
    "TituloInforme", parent=_estilos_base["Title"], fontSize=16, textColor=COLOR_RESULTADO
)
ESTILO_SUBTITULO = ParagraphStyle(
    "SubtituloInforme", parent=_estilos_base["Heading2"], fontSize=12, textColor=COLOR_CABECERA
)
ESTILO_NORMAL = _estilos_base["Normal"]
ESTILO_NOTA_FINAL = ParagraphStyle(
    "NotaFinal", parent=_estilos_base["Normal"], fontSize=13, textColor=COLOR_RESULTADO
)


def _formatear_numero(valor: float | None) -> str:
    if valor is None:
        return "—"
    return f"{valor:.2f}".replace(".", ",")


def _estilo_tabla_estandar() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_CABECERA),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#F6CFA0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_FILA_ALTERNA]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )


def _cabecera_comun(story: list, nombre_modulo: str, etiqueta_evaluacion: str, apellidos: str, nombre: str):
    story.append(Paragraph("Informe de calificaciones", ESTILO_TITULO))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Alumno/a:</b> {apellidos}, {nombre}", ESTILO_NORMAL))
    story.append(Paragraph(f"<b>Módulo:</b> {nombre_modulo}", ESTILO_NORMAL))
    story.append(Paragraph(f"<b>Evaluación:</b> {etiqueta_evaluacion}", ESTILO_NORMAL))
    story.append(Spacer(1, 14))


def _cuerpo_seccion_evaluacion(story: list, informe: InformeAlumno):
    """Las tablas de RA, criterios e instrumentos de una evaluación
    parcial, sin la cabecera ni la nota final (que ya se añaden por
    separado, igual en el informe individual que en el combinado)."""
    story.append(Paragraph("Calificación por Resultado de Aprendizaje", ESTILO_SUBTITULO))
    story.append(Spacer(1, 6))
    filas_ra_tabla = [["RA", "Peso en el módulo", "Nota", "Calificación"]]
    for fila in informe.filas_ra:
        filas_ra_tabla.append(
            [
                f"RA{fila.numero_ra}",
                f"{fila.peso_en_modulo:g}%",
                _formatear_numero(fila.valor),
                fila.calificacion or "—",
            ]
        )
    tabla_ra = Table(filas_ra_tabla, colWidths=[4 * cm, 4 * cm, 3 * cm, 4 * cm])
    tabla_ra.setStyle(_estilo_tabla_estandar())
    story.append(tabla_ra)
    story.append(Spacer(1, 18))

    story.append(Paragraph("Detalle por criterio de evaluación", ESTILO_SUBTITULO))
    story.append(Spacer(1, 6))
    filas_tabla = [["Criterio", "Peso en su RA", "Nota", "Calificación"]]
    for fila in informe.filas_criterios:
        filas_tabla.append(
            [
                fila.codigo_criterio,
                f"{fila.peso_en_ra:g}%",
                _formatear_numero(fila.valor),
                fila.calificacion or "—",
            ]
        )
    tabla = Table(filas_tabla, colWidths=[4 * cm, 4 * cm, 3 * cm, 4 * cm])
    tabla.setStyle(_estilo_tabla_estandar())
    story.append(tabla)
    story.append(Spacer(1, 18))

    story.append(Paragraph("Desglose por instrumento de evaluación", ESTILO_SUBTITULO))
    story.append(Spacer(1, 6))
    if not informe.bloques_instrumentos:
        story.append(Paragraph("No hay instrumentos de evaluación con criterios asignados.", ESTILO_NORMAL))
    for bloque in informe.bloques_instrumentos:
        texto_bloque = f"<b>{bloque.nombre_instrumento}</b> — peso {bloque.peso_global:g}% de la evaluación"
        story.append(Paragraph(texto_bloque, ESTILO_NORMAL))
        story.append(Spacer(1, 4))
        filas_bloque = [["Criterio", "Peso en este instrumento", "Nota", "Calificación"]]
        for fila in bloque.criterios:
            filas_bloque.append(
                [
                    fila.codigo_criterio,
                    f"{fila.peso_en_instrumento:g}%",
                    _formatear_numero(fila.valor),
                    fila.calificacion or "—",
                ]
            )
        tabla_bloque = Table(filas_bloque, colWidths=[4 * cm, 4.5 * cm, 2.5 * cm, 4 * cm])
        tabla_bloque.setStyle(_estilo_tabla_estandar())
        story.append(tabla_bloque)
        story.append(Spacer(1, 12))


def generar_informe_evaluacion_pdf(informe: InformeAlumno, ruta_destino: str | Path) -> Path:
    ruta_destino = Path(ruta_destino)
    doc = SimpleDocTemplate(
        str(ruta_destino), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    story = []

    _cabecera_comun(
        story, informe.nombre_modulo, informe.nombre_evaluacion, informe.apellidos_alumno, informe.nombre_alumno
    )

    texto_nota_final = (
        f"<b>Nota final de la evaluación: {_formatear_numero(informe.nota_final_numerica)} "
        f"({informe.calificacion_final or '—'})</b>"
    )
    story.append(Paragraph(texto_nota_final, ESTILO_NOTA_FINAL))
    story.append(Spacer(1, 16))

    _cuerpo_seccion_evaluacion(story, informe)

    doc.build(story)
    return ruta_destino


def _cuerpo_seccion_final(story: list, informe: InformeAlumnoFinal):
    """Las tablas de RA y criterios de FINAL, sin la cabecera ni la
    nota final (que ya se añaden por separado, igual en el informe
    individual que en el combinado)."""
    pesos_texto = "  ·  ".join(
        f"{nombre}: {peso:g}" for nombre, peso in informe.pesos_evaluaciones.items()
    )
    story.append(Paragraph(f"<i>Pesos aplicados entre evaluaciones — {pesos_texto}</i>", ESTILO_NORMAL))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Calificación final por Resultado de Aprendizaje", ESTILO_SUBTITULO))
    story.append(Spacer(1, 6))
    filas_ra_tabla = [["RA", "Peso en el módulo", "Nota FINAL", "Calificación"]]
    for fila in informe.filas_ra:
        filas_ra_tabla.append(
            [
                f"RA{fila.numero_ra}",
                f"{fila.peso_en_modulo:g}%",
                _formatear_numero(fila.valor),
                fila.calificacion or "—",
            ]
        )
    tabla_ra = Table(filas_ra_tabla, colWidths=[4 * cm, 4 * cm, 3 * cm, 4 * cm])
    tabla_ra.setStyle(_estilo_tabla_estandar())
    story.append(tabla_ra)
    story.append(Spacer(1, 18))

    story.append(Paragraph("Calificación de cada criterio, por evaluación", ESTILO_SUBTITULO))
    story.append(Spacer(1, 6))
    encabezados_criterios = ["Criterio"] + informe.nombres_evaluaciones + ["Nota FINAL", "Calif."]
    filas_tabla = [encabezados_criterios]
    for fila in informe.filas_criterios:
        valores_formateados = [_formatear_numero(v) for v in fila.valores_por_evaluacion]
        filas_tabla.append(
            [fila.codigo_criterio] + valores_formateados + [_formatear_numero(fila.valor), fila.calificacion or "—"]
        )
    n_columnas = len(encabezados_criterios)
    ancho_columna = 16.0 * cm / n_columnas
    tabla = Table(filas_tabla, colWidths=[ancho_columna] * n_columnas)
    tabla.setStyle(_estilo_tabla_estandar())
    story.append(tabla)
    story.append(Spacer(1, 14))
    story.append(
        Paragraph(
            "Las celdas en blanco (—) indican que ese criterio no tuvo ninguna nota calculada "
            "en esa evaluación. La nota FINAL combina las evaluaciones que sí tienen nota, "
            "según los pesos indicados arriba.",
            ESTILO_NORMAL,
        )
    )


def generar_informe_final_pdf(informe: InformeAlumnoFinal, ruta_destino: str | Path) -> Path:
    ruta_destino = Path(ruta_destino)
    doc = SimpleDocTemplate(
        str(ruta_destino), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    story = []

    _cabecera_comun(
        story, informe.nombre_modulo, "Evaluación final de curso",
        informe.apellidos_alumno, informe.nombre_alumno,
    )

    texto_nota_final = (
        f"<b>Nota final de curso: {_formatear_numero(informe.nota_final_numerica)} "
        f"({informe.calificacion_final or '—'})</b>"
    )
    story.append(Paragraph(texto_nota_final, ESTILO_NOTA_FINAL))
    story.append(Spacer(1, 10))

    _cuerpo_seccion_final(story, informe)

    doc.build(story)
    return ruta_destino


def generar_informe_completo_pdf(informe: "InformeAlumnoCompleto", ruta_destino: str | Path) -> Path:
    """Genera un único PDF con una sección por cada evaluación parcial
    evaluable, más una sección FINAL al final — todo en el mismo
    documento, separado por saltos de página.
    """
    ruta_destino = Path(ruta_destino)
    doc = SimpleDocTemplate(
        str(ruta_destino), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    story = []

    _cabecera_comun(
        story, informe.nombre_modulo, "Informe completo del curso",
        informe.apellidos_alumno, informe.nombre_alumno,
    )
    story.append(Spacer(1, 10))

    for indice, seccion in enumerate(informe.secciones_evaluaciones):
        if indice > 0:
            story.append(PageBreak())
        story.append(Paragraph(f"Evaluación: {seccion.nombre_evaluacion}", ESTILO_TITULO))
        story.append(Spacer(1, 6))
        texto_nota_final = (
            f"<b>Nota final de la evaluación: {_formatear_numero(seccion.nota_final_numerica)} "
            f"({seccion.calificacion_final or '—'})</b>"
        )
        story.append(Paragraph(texto_nota_final, ESTILO_NOTA_FINAL))
        story.append(Spacer(1, 16))
        _cuerpo_seccion_evaluacion(story, seccion)

    if informe.seccion_final is not None:
        story.append(PageBreak())
        story.append(Paragraph("Evaluación FINAL", ESTILO_TITULO))
        story.append(Spacer(1, 6))
        texto_nota_final = (
            f"<b>Nota final de curso: {_formatear_numero(informe.seccion_final.nota_final_numerica)} "
            f"({informe.seccion_final.calificacion_final or '—'})</b>"
        )
        story.append(Paragraph(texto_nota_final, ESTILO_NOTA_FINAL))
        story.append(Spacer(1, 10))
        _cuerpo_seccion_final(story, informe.seccion_final)

    doc.build(story)
    return ruta_destino
