"""
Detección de incidencias de configuración en una evaluación parcial o
en FINAL, para mostrar un resumen ("panel de salud") dentro de cada
pestaña.

Importante: dentro de un RA, los criterios son una lista compartida
por todas las evaluaciones del módulo, pero NO todos tienen que
evaluarse en la misma evaluación parcial — es normal que un criterio
de un RA se evalúe en la 1ª evaluación y otro criterio del mismo RA se
evalúe en la 2ª. Por eso aquí NUNCA se avisa de "los criterios de este
RA suman X%" dentro de una evaluación parcial concreta: esa suma global
del RA no es relevante por evaluación (a diferencia del peso de los
RA entre sí, que sí es siempre relevante porque decide cómo se combina
la nota del módulo).

El único aviso relacionado con "criterios sin usar" vive en FINAL, y
mira si un criterio se ha quedado sin ninguna nota en NINGUNA
evaluación para NINGÚN alumno — lo cual normalmente indica que el
docente se olvidó de marcarlo en algún instrumento durante el curso.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.database import BaseDatosModulo, Evaluacion, Modulo, TIPO_MEDIA_PONDERADA

SEVERIDAD_AVISO = "aviso"
SEVERIDAD_ERROR = "error"


@dataclass
class IncidenciaSalud:
    severidad: str
    mensaje: str


def _umbral_ok(suma: float) -> bool:
    return abs(suma - 100.0) < 0.01


def revisar_salud_evaluacion(
    base_datos: BaseDatosModulo, modulo: Modulo, evaluacion: Evaluacion
) -> list[IncidenciaSalud]:
    """Incidencias de una evaluación PARCIAL concreta: pesos de los RA
    entre sí (siempre relevante: decide la nota del módulo), RA sin
    ningún criterio definido, pesos de los instrumentos de esta
    evaluación, instrumentos sin ningún criterio marcado, instrumentos
    de media ponderada cuyas pruebas no suman 100% entre ellas, y
    alumnado sin ninguna nota todavía.
    """
    incidencias: list[IncidenciaSalud] = []

    suma_ra = base_datos.suma_pesos_ra(modulo.id)
    if not _umbral_ok(suma_ra):
        incidencias.append(
            IncidenciaSalud(
                SEVERIDAD_ERROR,
                f"Los pesos de los RA suman {suma_ra:g}% (deberían ser 100%): la nota final del "
                "módulo no se puede calcular todavía. Ajústalo en «RA y Criterios».",
            )
        )

    ras = base_datos.listar_ra(modulo.id)
    for ra in ras:
        if not base_datos.listar_criterios_de_ra(ra.id):
            incidencias.append(
                IncidenciaSalud(SEVERIDAD_AVISO, f"RA{ra.numero} todavía no tiene ningún criterio definido.")
            )

    instrumentos = base_datos.listar_instrumentos(evaluacion.id)
    if not instrumentos:
        incidencias.append(
            IncidenciaSalud(SEVERIDAD_AVISO, "Todavía no hay ningún instrumento de evaluación creado en esta evaluación.")
        )
    else:
        suma_instrumentos = base_datos.suma_pesos_instrumentos(evaluacion.id)
        if not _umbral_ok(suma_instrumentos):
            incidencias.append(
                IncidenciaSalud(
                    SEVERIDAD_AVISO,
                    f"Los pesos de los instrumentos suman {suma_instrumentos:g}% (deberían ser 100%).",
                )
            )
        for instrumento in instrumentos:
            if not base_datos.criterios_marcados_de_instrumento(instrumento.id):
                incidencias.append(
                    IncidenciaSalud(
                        SEVERIDAD_AVISO,
                        f"El instrumento «{instrumento.nombre}» no evalúa ningún criterio todavía.",
                    )
                )

            pruebas = base_datos.listar_pruebas(instrumento.id)
            if instrumento.tipo == TIPO_MEDIA_PONDERADA and len(pruebas) > 1:
                suma_pruebas = base_datos.suma_pesos_pruebas(instrumento.id)
                if not _umbral_ok(suma_pruebas):
                    incidencias.append(
                        IncidenciaSalud(
                            SEVERIDAD_AVISO,
                            f"Las pruebas del instrumento «{instrumento.nombre}» suman {suma_pruebas:g}% "
                            "(deberían ser 100%).",
                        )
                    )

    vista_alumnos = base_datos.listar_alumnos_para_evaluacion(modulo.id, evaluacion.orden)
    notas_modulo = base_datos.calcular_notas_modulo_evaluacion(evaluacion.id, modulo.id)
    alumnos_sin_nota = [
        alumno for alumno, evaluable in vista_alumnos if evaluable and notas_modulo.get(alumno.id) is None
    ]
    if alumnos_sin_nota:
        nombres = ", ".join(f"{a.apellidos}, {a.nombre}".strip(", ") for a in alumnos_sin_nota[:5])
        extra = f" y {len(alumnos_sin_nota) - 5} más" if len(alumnos_sin_nota) > 5 else ""
        incidencias.append(
            IncidenciaSalud(
                SEVERIDAD_AVISO,
                f"{len(alumnos_sin_nota)} alumno/a(s) sin ninguna nota todavía: {nombres}{extra}.",
            )
        )

    return incidencias


def revisar_salud_final(base_datos: BaseDatosModulo, modulo: Modulo) -> list[IncidenciaSalud]:
    """Incidencias de FINAL: pesos de RA entre sí, evaluaciones
    parciales sin instrumentos, criterios que se han quedado sin
    ninguna nota en ninguna evaluación para ningún alumno (olvidados
    al configurar los instrumentos), y alumnado con algún RA todavía
    no superado o sin nota.
    """
    incidencias: list[IncidenciaSalud] = []

    suma_ra = base_datos.suma_pesos_ra(modulo.id)
    if not _umbral_ok(suma_ra):
        incidencias.append(
            IncidenciaSalud(
                SEVERIDAD_ERROR,
                f"Los pesos de los RA suman {suma_ra:g}% (deberían ser 100%): la NOTA FINAL DE "
                "CURSO no se puede calcular todavía. Ajústalo en «RA y Criterios».",
            )
        )

    evaluaciones_parciales = base_datos.listar_evaluaciones_parciales(modulo.id)
    if not evaluaciones_parciales:
        incidencias.append(IncidenciaSalud(SEVERIDAD_AVISO, "Este módulo no tiene evaluaciones parciales."))
    else:
        for evaluacion in evaluaciones_parciales:
            if not base_datos.listar_instrumentos(evaluacion.id):
                incidencias.append(
                    IncidenciaSalud(
                        SEVERIDAD_AVISO,
                        f"«{evaluacion.nombre}» todavía no tiene ningún instrumento de evaluación "
                        "creado, así que no aporta nada a la nota final.",
                    )
                )

    criterios_con_ra = base_datos.listar_criterios_de_modulo(modulo.id)
    alumnos = base_datos.listar_alumnos(modulo.id)
    if criterios_con_ra and alumnos:
        notas_criterios_final = base_datos.calcular_notas_criterios_final(modulo.id)
        criterios_sin_calificar = [
            (ra, criterio)
            for ra, criterio in criterios_con_ra
            if all(notas_criterios_final.get((criterio.id, alumno.id)) is None for alumno in alumnos)
        ]
        if criterios_sin_calificar:
            codigos = ", ".join(
                base_datos.codigo_criterio(ra, criterio) for ra, criterio in criterios_sin_calificar[:8]
            )
            extra = f" y {len(criterios_sin_calificar) - 8} más" if len(criterios_sin_calificar) > 8 else ""
            incidencias.append(
                IncidenciaSalud(
                    SEVERIDAD_AVISO,
                    f"{len(criterios_sin_calificar)} criterio(s) sin ninguna nota en todo el curso "
                    f"(ningún alumno, en ninguna evaluación): {codigos}{extra}. Puede que se hayan "
                    "olvidado al configurar los instrumentos.",
                )
            )

    alumnos_con_ra_pendiente = []
    notas_ra_final = base_datos.calcular_notas_ra_final(modulo.id)
    ras = base_datos.listar_ra(modulo.id)
    for alumno in alumnos:
        tiene_pendiente = any(
            notas_ra_final.get((ra.id, alumno.id)) is None or notas_ra_final.get((ra.id, alumno.id)) < 5.0
            for ra in ras
        )
        if tiene_pendiente:
            alumnos_con_ra_pendiente.append(alumno)
    if alumnos_con_ra_pendiente:
        nombres = ", ".join(f"{a.apellidos}, {a.nombre}".strip(", ") for a in alumnos_con_ra_pendiente[:5])
        extra = f" y {len(alumnos_con_ra_pendiente) - 5} más" if len(alumnos_con_ra_pendiente) > 5 else ""
        incidencias.append(
            IncidenciaSalud(
                SEVERIDAD_AVISO,
                f"{len(alumnos_con_ra_pendiente)} alumno/a(s) con algún RA todavía no superado o "
                f"sin nota: {nombres}{extra}.",
            )
        )

    return incidencias
