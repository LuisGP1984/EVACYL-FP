"""
Reglas de calificación cualitativa y color, compartidas entre la interfaz
en pantalla y la exportación a Excel, para que ambas coincidan siempre.
"""

from __future__ import annotations

NOTA_MINIMA = 0.0
NOTA_MAXIMA = 10.0


class NotaFueraDeRangoError(ValueError):
    """Se lanza cuando una nota 0-10 introducida por el docente está fuera
    del rango permitido. El mensaje ya viene listo para mostrar al usuario.
    """

    def __init__(self, valor: float):
        self.valor = valor
        super().__init__(
            f"La nota {valor:g} no es válida: debe estar entre {NOTA_MINIMA:g} y {NOTA_MAXIMA:g}."
        )


def validar_nota_0_10(valor: float | None) -> float | None:
    """Comprueba que una nota esté en el rango [0, 10]. Devuelve el mismo
    valor si es válido (o None tal cual, que significa "sin nota"/"no
    presentado"). Lanza NotaFueraDeRangoError si está fuera de rango —
    NUNCA recorta el valor: se exige corregirlo.
    """
    if valor is None:
        return None
    if valor < NOTA_MINIMA or valor > NOTA_MAXIMA:
        raise NotaFueraDeRangoError(valor)
    return valor


# Umbrales de calificación cualitativa (escala 0-10):
#   < 5        -> IN (Insuficiente)
#   [5, 6)     -> SU (Suficiente)
#   [6, 7)     -> BI (Bien)
#   [7, 9)     -> NT (Notable)
#   >= 9       -> SB (Sobresaliente)


def calificacion_cualitativa(valor: float | None) -> str:
    """Devuelve la calificación cualitativa (IN/SU/BI/NT/SB) para una nota
    0-10, o "" si no hay nota.
    """
    if valor is None:
        return ""
    if valor < 5:
        return "IN"
    if valor < 6:
        return "SU"
    if valor < 7:
        return "BI"
    if valor < 9:
        return "NT"
    return "SB"


# Colores del degradado rojo -> amarillo -> verde, en formato (R, G, B).
# Tonos pastel suaves para que el color informe sin saturar la vista ni
# dificultar la lectura del número/letra sobre el fondo.
# 0.0 = nota 0 (rojo pastel), 0.5 = nota 5 (amarillo pastel), 1.0 = nota 10 (verde pastel).
_COLOR_ROJO = (244, 199, 195)
_COLOR_AMARILLO = (250, 235, 185)
_COLOR_VERDE = (198, 230, 201)


def color_degradado_nota(valor: float | None) -> tuple[int, int, int] | None:
    """Devuelve (R, G, B) para una nota 0-10, interpolando rojo (0) ->
    amarillo (5) -> verde (10). Devuelve None si no hay nota (sin color).
    """
    if valor is None:
        return None
    valor = max(0.0, min(10.0, valor))
    fraccion = valor / 10.0

    if fraccion <= 0.5:
        t = fraccion / 0.5
        inicio, fin = _COLOR_ROJO, _COLOR_AMARILLO
    else:
        t = (fraccion - 0.5) / 0.5
        inicio, fin = _COLOR_AMARILLO, _COLOR_VERDE

    return tuple(round(inicio[i] + (fin[i] - inicio[i]) * t) for i in range(3))


def color_hex_nota(valor: float | None) -> str | None:
    """Igual que color_degradado_nota, pero como cadena hexadecimal
    "RRGGBB" (formato que usa tanto Qt como openpyxl), o None si no hay nota.
    """
    rgb = color_degradado_nota(valor)
    if rgb is None:
        return None
    return "".join(f"{c:02X}" for c in rgb)
