"""
Detección de incidencias de configuración en una evaluación parcial o
en FINAL, para mostrar un resumen ("panel de salud") dentro de cada
pestaña: en vez de que el docente tenga que descubrir un problema poco
a poco (un peso que no suma 100%, un alumno sin ninguna nota...), se
reúnen todas las incidencias detectables en una sola lista al entrar
en la pestaña.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.database import BaseDatosModulo, Evaluacion, Modulo

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
    """Incidencias de una evaluación PARCIAL concreta: pesos de RA,
    pesos de criterios dentro de cada RA, pesos de instrumentos de esa
    evaluación, y alumnado sin ninguna nota todavía.
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
        criterios = base_datos.listar_criterios_de_ra(ra.id)
        if not criterios:
            incidencias.append(
                IncidenciaSalud(SEVERIDAD_AVISO, f"RA{ra.numero} todavía no tiene ningún criterio definido.")
            )
        else:
            suma_criterios = base_datos.suma_pesos_criterios_de_ra(ra.id)
            if not _umbral_ok(suma_criterios):
                incidencias.append(
                    IncidenciaSalud(
                        SEVERIDAD_AVISO,
                        f"Los criterios de RA{ra.numero} suman {suma_criterios:g}% (deberían ser 100%).",
                    )
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
    """Incidencias de FINAL: pesos de RA, evaluaciones parciales sin
    instrumentos, y alumnado con algún RA todavía no superado o sin nota.
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

    alumnos = base_datos.listar_alumnos(modulo.id)
    notas_ra_final = base_datos.calcular_notas_ra_final(modulo.id)
    ras = base_datos.listar_ra(modulo.id)
    alumnos_con_ra_pendiente = []
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
