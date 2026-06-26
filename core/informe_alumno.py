"""
Recopilación de datos para el informe individual de un alumno: pensado
para que el alumno (o su familia) entienda exactamente de dónde sale
cada nota, de cara a posibles reclamaciones. No genera ningún archivo —
eso lo hacen informe_pdf.py e informe_docx.py a partir de estas
estructuras, para no duplicar la lógica de cálculo en dos sitios.

A diferencia de EVACYL, aquí cada informe incluye también la nota por
Resultado de Aprendizaje (RA), ya que es la vista que prioriza el
profesorado de FP — el detalle por criterio se mantiene como
información adicional, agrupado bajo su RA.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.calificacion import calificacion_cualitativa
from core.database import BaseDatosModulo, Evaluacion, Modulo


@dataclass
class FilaCriterioInstrumento:
    codigo_criterio: str
    peso_en_instrumento: float
    valor: float | None
    calificacion: str


@dataclass
class BloqueInstrumento:
    nombre_instrumento: str
    tipo_instrumento: str
    peso_global: float
    criterios: list[FilaCriterioInstrumento]


@dataclass
class FilaRA:
    numero_ra: int
    descripcion: str
    peso_en_modulo: float
    valor: float | None
    calificacion: str


@dataclass
class FilaCriterioPorRA:
    numero_ra: int
    codigo_criterio: str
    peso_en_ra: float
    valor: float | None
    calificacion: str


@dataclass
class FilaRAFinal:
    numero_ra: int
    descripcion: str
    peso_en_modulo: float
    valor: float | None
    calificacion: str


@dataclass
class FilaCriterioFinal:
    numero_ra: int
    codigo_criterio: str
    valor: float | None
    calificacion: str
    valores_por_evaluacion: list[float | None]


@dataclass
class InformeAlumno:
    nombre_modulo: str
    nombre_evaluacion: str
    apellidos_alumno: str
    nombre_alumno: str
    filas_ra: list[FilaRA] = field(default_factory=list)
    filas_criterios: list[FilaCriterioPorRA] = field(default_factory=list)
    nota_final_numerica: float | None = None
    calificacion_final: str = ""
    bloques_instrumentos: list[BloqueInstrumento] = field(default_factory=list)


@dataclass
class InformeAlumnoFinal:
    nombre_modulo: str
    apellidos_alumno: str
    nombre_alumno: str
    filas_ra: list[FilaRAFinal] = field(default_factory=list)
    filas_criterios: list[FilaCriterioFinal] = field(default_factory=list)
    nombres_evaluaciones: list[str] = field(default_factory=list)
    nota_final_numerica: float | None = None
    calificacion_final: str = ""
    pesos_evaluaciones: dict[str, float] = field(default_factory=dict)


def recopilar_informe_evaluacion(
    base_datos: BaseDatosModulo, modulo: Modulo, evaluacion: Evaluacion, alumno_id: int
) -> InformeAlumno | None:
    vista_alumnos = base_datos.listar_alumnos_para_evaluacion(modulo.id, evaluacion.orden)
    alumno_encontrado = None
    evaluable = False
    for alumno, es_evaluable in vista_alumnos:
        if alumno.id == alumno_id:
            alumno_encontrado = alumno
            evaluable = es_evaluable
            break
    if alumno_encontrado is None or not evaluable:
        return None

    ras = base_datos.listar_ra(modulo.id)
    criterios_con_ra = base_datos.listar_criterios_de_modulo(modulo.id)
    notas_criterio = base_datos.calcular_notas_criterios_evaluacion(evaluacion.id, modulo.id)
    notas_ra = base_datos.calcular_notas_ra_evaluacion(evaluacion.id, modulo.id)
    notas_modulo = base_datos.calcular_notas_modulo_evaluacion(evaluacion.id, modulo.id)

    filas_ra = []
    for ra in ras:
        valor_ra = notas_ra.get((ra.id, alumno_id))
        filas_ra.append(
            FilaRA(
                numero_ra=ra.numero,
                descripcion=ra.descripcion,
                peso_en_modulo=ra.peso,
                valor=valor_ra,
                calificacion=calificacion_cualitativa(valor_ra),
            )
        )

    filas_criterios = []
    for ra, criterio in criterios_con_ra:
        valor = notas_criterio.get((criterio.id, alumno_id))
        codigo = base_datos.codigo_criterio(ra, criterio)
        filas_criterios.append(
            FilaCriterioPorRA(
                numero_ra=ra.numero,
                codigo_criterio=codigo,
                peso_en_ra=criterio.peso,
                valor=valor,
                calificacion=calificacion_cualitativa(valor),
            )
        )

    nota_final = notas_modulo.get(alumno_id)

    instrumentos = base_datos.listar_instrumentos(evaluacion.id)
    bloques = []
    for instrumento in instrumentos:
        criterios_marcados_ids = base_datos.criterios_marcados_de_instrumento(instrumento.id)
        if not criterios_marcados_ids:
            continue
        relaciones = {
            ic.criterio_id: ic for ic in base_datos.listar_criterios_de_instrumento(instrumento.id)
        }
        notas_criterio_instrumento = base_datos.obtener_notas_criterio_instrumento(instrumento.id)

        filas_bloque = []
        for ra, criterio in criterios_con_ra:
            if criterio.id not in criterios_marcados_ids:
                continue
            codigo = base_datos.codigo_criterio(ra, criterio)
            relacion = relaciones.get(criterio.id)
            valor, _es_manual = notas_criterio_instrumento.get((criterio.id, alumno_id), (None, False))
            filas_bloque.append(
                FilaCriterioInstrumento(
                    codigo_criterio=codigo,
                    peso_en_instrumento=relacion.peso if relacion is not None else 0.0,
                    valor=valor,
                    calificacion=calificacion_cualitativa(valor),
                )
            )
        bloques.append(
            BloqueInstrumento(
                nombre_instrumento=instrumento.nombre,
                tipo_instrumento=instrumento.tipo,
                peso_global=instrumento.peso,
                criterios=filas_bloque,
            )
        )

    return InformeAlumno(
        nombre_modulo=modulo.nombre,
        nombre_evaluacion=evaluacion.nombre,
        apellidos_alumno=alumno_encontrado.apellidos,
        nombre_alumno=alumno_encontrado.nombre,
        filas_ra=filas_ra,
        filas_criterios=filas_criterios,
        nota_final_numerica=nota_final,
        calificacion_final=calificacion_cualitativa(nota_final),
        bloques_instrumentos=bloques,
    )


def recopilar_informe_final(
    base_datos: BaseDatosModulo, modulo: Modulo, alumno_id: int
) -> InformeAlumnoFinal | None:
    alumnos = base_datos.listar_alumnos(modulo.id)
    alumno_encontrado = next((a for a in alumnos if a.id == alumno_id), None)
    if alumno_encontrado is None:
        return None

    ras = base_datos.listar_ra(modulo.id)
    criterios_con_ra = base_datos.listar_criterios_de_modulo(modulo.id)
    notas_criterio_final = base_datos.calcular_notas_criterios_final(modulo.id)
    notas_ra_final = base_datos.calcular_notas_ra_final(modulo.id)
    notas_modulo_final = base_datos.calcular_notas_modulo_final(modulo.id)

    evaluaciones = base_datos.listar_evaluaciones_parciales(modulo.id)
    notas_por_evaluacion = {
        ev.id: base_datos.calcular_notas_criterios_evaluacion(ev.id, modulo.id) for ev in evaluaciones
    }

    filas_ra = []
    for ra in ras:
        valor_ra = notas_ra_final.get((ra.id, alumno_id))
        filas_ra.append(
            FilaRAFinal(
                numero_ra=ra.numero,
                descripcion=ra.descripcion,
                peso_en_modulo=ra.peso,
                valor=valor_ra,
                calificacion=calificacion_cualitativa(valor_ra),
            )
        )

    filas_criterios = []
    for ra, criterio in criterios_con_ra:
        valor_final = notas_criterio_final.get((criterio.id, alumno_id))
        codigo = base_datos.codigo_criterio(ra, criterio)
        valores_por_evaluacion = [
            notas_por_evaluacion[ev.id].get((criterio.id, alumno_id)) for ev in evaluaciones
        ]
        filas_criterios.append(
            FilaCriterioFinal(
                numero_ra=ra.numero,
                codigo_criterio=codigo,
                valor=valor_final,
                calificacion=calificacion_cualitativa(valor_final),
                valores_por_evaluacion=valores_por_evaluacion,
            )
        )

    nota_final_modulo = notas_modulo_final.get(alumno_id)
    pesos_evaluaciones_por_id = base_datos.obtener_pesos_evaluaciones_final(modulo.id)
    pesos_evaluaciones = {ev.nombre: pesos_evaluaciones_por_id.get(ev.id, 1.0) for ev in evaluaciones}

    return InformeAlumnoFinal(
        nombre_modulo=modulo.nombre,
        apellidos_alumno=alumno_encontrado.apellidos,
        nombre_alumno=alumno_encontrado.nombre,
        filas_ra=filas_ra,
        filas_criterios=filas_criterios,
        nombres_evaluaciones=[ev.nombre for ev in evaluaciones],
        nota_final_numerica=nota_final_modulo,
        calificacion_final=calificacion_cualitativa(nota_final_modulo),
        pesos_evaluaciones=pesos_evaluaciones,
    )
