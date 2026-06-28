"""
Estadísticas numéricas por Resultado de Aprendizaje (RA), para una
evaluación parcial o para FINAL: media, máxima y mínima de las notas
del grupo en cada RA. A diferencia de EVACYL (centrado en el desglose
cualitativo IN/SU/BI/NT/SB), en FP se prioriza la nota numérica por RA,
ya que es la unidad de seguimiento principal del profesorado.

No almacena nada nuevo en la base de datos: se calcula a partir de las
notas de RA ya existentes (calcular_notas_ra_evaluacion /
calcular_notas_ra_final).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EstadisticaRA:
    numero_ra: int
    descripcion: str
    media: float | None
    maxima: float | None
    minima: float | None
    total_con_nota: int
    total_sin_nota: int


def calcular_estadisticas_por_ra(
    ras: list,
    notas_ra: dict[tuple[int, int], float | None],
    ids_alumnos: list[int],
) -> list[EstadisticaRA]:
    """Para cada RA, calcula media/máxima/mínima de las notas de los
    alumnos indicados en ese RA (ignorando los que no tienen nota
    todavía, que se cuentan aparte en total_sin_nota).
    """
    resultado = []
    for ra in ras:
        valores = []
        sin_nota = 0
        for alumno_id in ids_alumnos:
            valor = notas_ra.get((ra.id, alumno_id))
            if valor is None:
                sin_nota += 1
            else:
                valores.append(valor)

        media = round(sum(valores) / len(valores), 2) if valores else None
        maxima = max(valores) if valores else None
        minima = min(valores) if valores else None

        resultado.append(
            EstadisticaRA(
                numero_ra=ra.numero,
                descripcion=ra.descripcion,
                media=media,
                maxima=maxima,
                minima=minima,
                total_con_nota=len(valores),
                total_sin_nota=sin_nota,
            )
        )
    return resultado
