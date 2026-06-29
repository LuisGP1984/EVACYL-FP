"""
Núcleo de datos de EVACYL FP: gestión de la evaluación de módulos de
Formación Profesional, organizados en Resultados de Aprendizaje (RA) y
sus criterios de evaluación, con instrumentos de evaluación por cada
evaluación parcial (cuyo número es configurable por módulo) y una
evaluación FINAL que las combina.

Jerarquía de datos:

    Modulo (carpeta del curso -> modulo.db)
      ├─ ResultadoAprendizaje (RA): peso dentro del módulo
      │    └─ Criterio (código "1.a", "1.b"...): peso dentro de su RA
      ├─ Alumno (a nivel de módulo, compartido por todas sus evaluaciones)
      ├─ Evaluacion: N evaluaciones parciales (configurable al crear el
      │    módulo) + 1 FINAL siempre automática
      └─ Por cada evaluación parcial: InstrumentoEvaluacion (Manual,
           Examen, Media aritmética, Media ponderada) — idéntico
           mecanismo que en EVACYL, incluido el modelo de peso propio
           por cada criterio que evalúa (con redistribución dinámica).

Cálculo en cascada (la diferencia principal respecto a EVACYL):
    nota_criterio  -> combinación de los instrumentos que lo evalúan
    nota_RA        -> media ponderada de sus criterios (peso del
                       criterio DENTRO de su RA), con reparto dinámico
    nota_modulo    -> media ponderada de sus RA (peso del RA dentro del
                       módulo), con el mismo reparto dinámico
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Modulo:
    id: int
    nombre: str
    numero_evaluaciones_parciales: int


@dataclass
class Evaluacion:
    id: int
    modulo_id: int
    nombre: str
    orden: int


@dataclass
class Alumno:
    id: int
    modulo_id: int
    apellidos: str
    nombre: str
    orden: int
    orden_alta: int = 1


@dataclass
class ResultadoAprendizaje:
    id: int
    modulo_id: int
    numero: int
    descripcion: str
    peso: float
    orden: int


@dataclass
class Criterio:
    id: int
    ra_id: int
    letra: str
    peso: float
    orden: int


TIPO_MANUAL = "MANUAL"
TIPO_MEDIA_ARITMETICA = "MEDIA_ARITMETICA"
TIPO_MEDIA_PONDERADA = "MEDIA_PONDERADA"
TIPO_EXAMEN = "EXAMEN"
TIPOS_INSTRUMENTO = [TIPO_MANUAL, TIPO_MEDIA_ARITMETICA, TIPO_MEDIA_PONDERADA, TIPO_EXAMEN]


@dataclass
class InstrumentoEvaluacion:
    id: int
    evaluacion_id: int
    nombre: str
    tipo: str
    peso: float
    nota_maxima: float
    orden: int


@dataclass
class PruebaInstrumento:
    id: int
    instrumento_id: int
    nombre: str
    peso: float
    orden: int


@dataclass
class InstrumentoCriterio:
    id: int
    instrumento_id: int
    criterio_id: int
    peso: float
    peso_manual: bool = False


class BaseDatosModulo:
    def __init__(self, ruta_archivo: str | Path):
        self.ruta_archivo = Path(ruta_archivo)
        self.conexion = sqlite3.connect(self.ruta_archivo)
        self.conexion.execute("PRAGMA foreign_keys = ON;")
        self._crear_esquema_si_falta()

    def cerrar(self):
        self.conexion.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cerrar()

    def _crear_esquema_si_falta(self):
        cur = self.conexion.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS modulo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                numero_evaluaciones_parciales INTEGER NOT NULL DEFAULT 2
            );

            CREATE TABLE IF NOT EXISTS evaluacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modulo_id INTEGER NOT NULL REFERENCES modulo(id) ON DELETE CASCADE,
                nombre TEXT NOT NULL,
                orden INTEGER NOT NULL,
                UNIQUE(modulo_id, nombre)
            );

            CREATE TABLE IF NOT EXISTS alumno (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modulo_id INTEGER NOT NULL REFERENCES modulo(id) ON DELETE CASCADE,
                apellidos TEXT NOT NULL,
                nombre TEXT NOT NULL,
                orden INTEGER NOT NULL,
                orden_alta INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS resultado_aprendizaje (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modulo_id INTEGER NOT NULL REFERENCES modulo(id) ON DELETE CASCADE,
                numero INTEGER NOT NULL,
                descripcion TEXT NOT NULL DEFAULT '',
                peso REAL NOT NULL DEFAULT 0,
                orden INTEGER NOT NULL,
                UNIQUE(modulo_id, numero)
            );

            CREATE TABLE IF NOT EXISTS criterio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ra_id INTEGER NOT NULL REFERENCES resultado_aprendizaje(id) ON DELETE CASCADE,
                letra TEXT NOT NULL,
                peso REAL NOT NULL DEFAULT 1,
                orden INTEGER NOT NULL,
                UNIQUE(ra_id, letra)
            );

            CREATE TABLE IF NOT EXISTS instrumento_evaluacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluacion_id INTEGER NOT NULL REFERENCES evaluacion(id) ON DELETE CASCADE,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                peso REAL NOT NULL DEFAULT 0,
                nota_maxima REAL NOT NULL DEFAULT 10,
                orden INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS prueba_instrumento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrumento_id INTEGER NOT NULL REFERENCES instrumento_evaluacion(id) ON DELETE CASCADE,
                nombre TEXT NOT NULL,
                peso REAL NOT NULL DEFAULT 0,
                orden INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS instrumento_criterio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrumento_id INTEGER NOT NULL REFERENCES instrumento_evaluacion(id) ON DELETE CASCADE,
                criterio_id INTEGER NOT NULL REFERENCES criterio(id) ON DELETE CASCADE,
                peso REAL NOT NULL DEFAULT 100,
                peso_manual INTEGER NOT NULL DEFAULT 0,
                UNIQUE(instrumento_id, criterio_id)
            );

            CREATE TABLE IF NOT EXISTS nota_prueba (
                prueba_id INTEGER NOT NULL REFERENCES prueba_instrumento(id) ON DELETE CASCADE,
                alumno_id INTEGER NOT NULL REFERENCES alumno(id) ON DELETE CASCADE,
                valor REAL,
                PRIMARY KEY (prueba_id, alumno_id)
            );

            CREATE TABLE IF NOT EXISTS nota_instrumento_alumno (
                instrumento_id INTEGER NOT NULL REFERENCES instrumento_evaluacion(id) ON DELETE CASCADE,
                alumno_id INTEGER NOT NULL REFERENCES alumno(id) ON DELETE CASCADE,
                valor REAL,
                PRIMARY KEY (instrumento_id, alumno_id)
            );

            CREATE TABLE IF NOT EXISTS nota_criterio_instrumento_alumno (
                instrumento_id INTEGER NOT NULL REFERENCES instrumento_evaluacion(id) ON DELETE CASCADE,
                criterio_id INTEGER NOT NULL REFERENCES criterio(id) ON DELETE CASCADE,
                alumno_id INTEGER NOT NULL REFERENCES alumno(id) ON DELETE CASCADE,
                valor REAL,
                es_manual INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (instrumento_id, criterio_id, alumno_id)
            );

            CREATE TABLE IF NOT EXISTS peso_evaluacion_final (
                modulo_id INTEGER NOT NULL REFERENCES modulo(id) ON DELETE CASCADE,
                evaluacion_id INTEGER NOT NULL REFERENCES evaluacion(id) ON DELETE CASCADE,
                peso REAL NOT NULL DEFAULT 1,
                PRIMARY KEY (modulo_id, evaluacion_id)
            );
            """
        )
        self.conexion.commit()

    # -- módulo ------------------------------------------------------------

    def crear_modulo(self, nombre: str, numero_evaluaciones_parciales: int) -> Modulo:
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre del módulo no puede estar vacío.")
        if numero_evaluaciones_parciales < 1:
            raise ValueError("El módulo debe tener al menos una evaluación parcial.")
        cur = self.conexion.execute(
            "INSERT INTO modulo (nombre, numero_evaluaciones_parciales) VALUES (?, ?);",
            (nombre, numero_evaluaciones_parciales),
        )
        modulo_id = cur.lastrowid

        for indice in range(1, numero_evaluaciones_parciales + 1):
            nombre_evaluacion = f"{indice}ª Evaluación"
            self.conexion.execute(
                "INSERT INTO evaluacion (modulo_id, nombre, orden) VALUES (?, ?, ?);",
                (modulo_id, nombre_evaluacion, indice),
            )
        self.conexion.execute(
            "INSERT INTO evaluacion (modulo_id, nombre, orden) VALUES (?, 'FINAL', ?);",
            (modulo_id, numero_evaluaciones_parciales + 1),
        )
        self.conexion.commit()
        return Modulo(id=modulo_id, nombre=nombre, numero_evaluaciones_parciales=numero_evaluaciones_parciales)

    def listar_modulos(self) -> list[Modulo]:
        cur = self.conexion.execute(
            "SELECT id, nombre, numero_evaluaciones_parciales FROM modulo ORDER BY nombre;"
        )
        return [Modulo(id=r[0], nombre=r[1], numero_evaluaciones_parciales=r[2]) for r in cur.fetchall()]

    def eliminar_modulo(self, modulo_id: int):
        self.conexion.execute("DELETE FROM modulo WHERE id = ?;", (modulo_id,))
        self.conexion.commit()

    def renombrar_modulo(self, modulo_id: int, nuevo_nombre: str):
        nuevo_nombre = nuevo_nombre.strip()
        if not nuevo_nombre:
            raise ValueError("El nombre del módulo no puede estar vacío.")
        self.conexion.execute("UPDATE modulo SET nombre = ? WHERE id = ?;", (nuevo_nombre, modulo_id))
        self.conexion.commit()

    # -- evaluaciones --------------------------------------------------------

    def listar_evaluaciones(self, modulo_id: int) -> list[Evaluacion]:
        cur = self.conexion.execute(
            "SELECT id, modulo_id, nombre, orden FROM evaluacion WHERE modulo_id = ? ORDER BY orden;",
            (modulo_id,),
        )
        return [Evaluacion(id=r[0], modulo_id=r[1], nombre=r[2], orden=r[3]) for r in cur.fetchall()]

    def listar_evaluaciones_parciales(self, modulo_id: int) -> list[Evaluacion]:
        return [ev for ev in self.listar_evaluaciones(modulo_id) if ev.nombre != "FINAL"]

    def obtener_evaluacion_final(self, modulo_id: int) -> Evaluacion | None:
        for ev in self.listar_evaluaciones(modulo_id):
            if ev.nombre == "FINAL":
                return ev
        return None

    # -- alumnos --------------------------------------------------------------

    def listar_alumnos(self, modulo_id: int) -> list[Alumno]:
        cur = self.conexion.execute(
            """SELECT id, modulo_id, apellidos, nombre, orden, orden_alta
               FROM alumno WHERE modulo_id = ? ORDER BY orden;""",
            (modulo_id,),
        )
        return [
            Alumno(id=r[0], modulo_id=r[1], apellidos=r[2], nombre=r[3], orden=r[4], orden_alta=r[5])
            for r in cur.fetchall()
        ]

    def agregar_alumno(self, modulo_id: int, apellidos: str, nombre: str, orden_alta: int = 1) -> Alumno:
        # No se exige apellidos/nombre no vacíos aquí: el botón "Añadir
        # alumno/a" de la interfaz crea una fila en blanco a propósito,
        # para que el docente la rellene escribiendo directamente en la
        # tabla. La validación de filas vacías al pegar/importar en lote
        # ya se hace por separado en agregar_alumnos_en_lote().
        apellidos = apellidos.strip()
        nombre = nombre.strip()
        cur = self.conexion.execute(
            "SELECT COALESCE(MAX(orden), 0) + 1 FROM alumno WHERE modulo_id = ?;", (modulo_id,)
        )
        siguiente_orden = cur.fetchone()[0]
        cur = self.conexion.execute(
            """INSERT INTO alumno (modulo_id, apellidos, nombre, orden, orden_alta)
               VALUES (?, ?, ?, ?, ?);""",
            (modulo_id, apellidos, nombre, siguiente_orden, orden_alta),
        )
        self.conexion.commit()
        return Alumno(
            id=cur.lastrowid, modulo_id=modulo_id, apellidos=apellidos, nombre=nombre,
            orden=siguiente_orden, orden_alta=orden_alta,
        )

    def agregar_alumnos_en_lote(self, modulo_id: int, filas: list[tuple[str, str]]) -> int:
        cur = self.conexion.execute(
            "SELECT COALESCE(MAX(orden), 0) FROM alumno WHERE modulo_id = ?;", (modulo_id,)
        )
        orden_actual = cur.fetchone()[0]
        insertados = 0
        for apellidos, nombre in filas:
            apellidos = (apellidos or "").strip()
            nombre = (nombre or "").strip()
            if not apellidos and not nombre:
                continue
            orden_actual += 1
            self.conexion.execute(
                "INSERT INTO alumno (modulo_id, apellidos, nombre, orden, orden_alta) VALUES (?, ?, ?, ?, 1);",
                (modulo_id, apellidos, nombre, orden_actual),
            )
            insertados += 1
        self.conexion.commit()
        return insertados

    def actualizar_alumno(self, alumno_id: int, apellidos: str, nombre: str):
        self.conexion.execute(
            "UPDATE alumno SET apellidos = ?, nombre = ? WHERE id = ?;",
            (apellidos.strip(), nombre.strip(), alumno_id),
        )
        self.conexion.commit()

    def actualizar_orden_alta_alumno(self, alumno_id: int, orden_alta: int):
        if orden_alta < 1:
            raise ValueError("La evaluación de alta debe ser 1 o mayor.")
        self.conexion.execute("UPDATE alumno SET orden_alta = ? WHERE id = ?;", (orden_alta, alumno_id))
        self.conexion.commit()

    def eliminar_alumno(self, alumno_id: int):
        self.conexion.execute("DELETE FROM alumno WHERE id = ?;", (alumno_id,))
        self.conexion.commit()

    def listar_alumnos_para_evaluacion(
        self, modulo_id: int, evaluacion_orden: int
    ) -> list[tuple[Alumno, bool]]:
        """Devuelve (alumno, evaluable_aqui) para cada alumno del módulo.
        evaluable_aqui es False si el alumno se incorporó en una
        evaluación posterior a evaluacion_orden (igual mecanismo que en
        EVACYL). Para FINAL, se debe pasar un orden mayor que cualquier
        evaluación parcial (así todos resultan evaluables).
        """
        alumnos = self.listar_alumnos(modulo_id)
        return [(alumno, alumno.orden_alta <= evaluacion_orden) for alumno in alumnos]

    # -- Resultados de Aprendizaje (RA) ---------------------------------------

    def listar_ra(self, modulo_id: int) -> list[ResultadoAprendizaje]:
        cur = self.conexion.execute(
            """SELECT id, modulo_id, numero, descripcion, peso, orden
               FROM resultado_aprendizaje WHERE modulo_id = ? ORDER BY orden;""",
            (modulo_id,),
        )
        return [
            ResultadoAprendizaje(id=r[0], modulo_id=r[1], numero=r[2], descripcion=r[3], peso=r[4], orden=r[5])
            for r in cur.fetchall()
        ]

    def agregar_ra(self, modulo_id: int, numero: int, descripcion: str = "", peso: float = 0.0) -> ResultadoAprendizaje:
        cur = self.conexion.execute(
            "SELECT COALESCE(MAX(orden), 0) + 1 FROM resultado_aprendizaje WHERE modulo_id = ?;",
            (modulo_id,),
        )
        siguiente_orden = cur.fetchone()[0]
        cur = self.conexion.execute(
            """INSERT INTO resultado_aprendizaje (modulo_id, numero, descripcion, peso, orden)
               VALUES (?, ?, ?, ?, ?);""",
            (modulo_id, numero, descripcion.strip(), peso, siguiente_orden),
        )
        self.conexion.commit()
        return ResultadoAprendizaje(
            id=cur.lastrowid, modulo_id=modulo_id, numero=numero,
            descripcion=descripcion.strip(), peso=peso, orden=siguiente_orden,
        )

    def actualizar_ra(self, ra_id: int, descripcion: str, peso: float):
        self.conexion.execute(
            "UPDATE resultado_aprendizaje SET descripcion = ?, peso = ? WHERE id = ?;",
            (descripcion.strip(), peso, ra_id),
        )
        self.conexion.commit()

    def eliminar_ra(self, ra_id: int):
        self.conexion.execute("DELETE FROM resultado_aprendizaje WHERE id = ?;", (ra_id,))
        self.conexion.commit()

    def suma_pesos_ra(self, modulo_id: int) -> float:
        cur = self.conexion.execute(
            "SELECT COALESCE(SUM(peso), 0) FROM resultado_aprendizaje WHERE modulo_id = ?;",
            (modulo_id,),
        )
        return cur.fetchone()[0]

    # -- criterios (dentro de un RA) -------------------------------------------

    def listar_criterios_de_ra(self, ra_id: int) -> list[Criterio]:
        cur = self.conexion.execute(
            "SELECT id, ra_id, letra, peso, orden FROM criterio WHERE ra_id = ? ORDER BY orden;",
            (ra_id,),
        )
        return [Criterio(id=r[0], ra_id=r[1], letra=r[2], peso=r[3], orden=r[4]) for r in cur.fetchall()]

    def listar_criterios_de_modulo(self, modulo_id: int) -> list[tuple[ResultadoAprendizaje, Criterio]]:
        """Todos los criterios de todos los RA de un módulo, junto con su
        RA, en el orden natural (RA 1 con sus criterios, luego RA 2...).
        """
        resultado = []
        for ra in self.listar_ra(modulo_id):
            for criterio in self.listar_criterios_de_ra(ra.id):
                resultado.append((ra, criterio))
        return resultado

    def codigo_criterio(self, ra: ResultadoAprendizaje, criterio: Criterio) -> str:
        return f"{ra.numero}.{criterio.letra}"

    def generar_criterios_para_ra(self, ra_id: int, cantidad: int):
        """Genera automáticamente "cantidad" criterios para un RA, con
        letras correlativas (a, b, c...) y peso relativo igual entre
        ellos (1 cada uno: todos valen lo mismo dentro del RA, sin
        necesidad de que la suma "cuadre" a 100 exacto — el peso es un
        valor relativo, igual que en EVACYL, no un porcentaje fijo).
        Si el RA ya tenía criterios, se eliminan primero (esta función
        está pensada para usarse al configurar el RA por primera vez,
        no para añadir criterios sueltos después — para eso está
        agregar_criterio_manual).
        """
        if cantidad < 1:
            raise ValueError("Un RA debe tener al menos un criterio.")
        self.conexion.execute("DELETE FROM criterio WHERE ra_id = ?;", (ra_id,))
        for indice in range(cantidad):
            letra = chr(ord("a") + indice)
            self.conexion.execute(
                "INSERT INTO criterio (ra_id, letra, peso, orden) VALUES (?, ?, ?, ?);",
                (ra_id, letra, 1.0, indice + 1),
            )
        self.conexion.commit()

    def agregar_criterio_manual(self, ra_id: int, letra: str, peso: float = 1.0) -> Criterio:
        letra = letra.strip().lower()
        if not letra or not letra.isalpha():
            raise ValueError("La letra del criterio debe ser una letra (a, b, c...).")
        cur = self.conexion.execute(
            "SELECT COALESCE(MAX(orden), 0) + 1 FROM criterio WHERE ra_id = ?;", (ra_id,)
        )
        siguiente_orden = cur.fetchone()[0]
        cur = self.conexion.execute(
            "INSERT INTO criterio (ra_id, letra, peso, orden) VALUES (?, ?, ?, ?);",
            (ra_id, letra, peso, siguiente_orden),
        )
        self.conexion.commit()
        return Criterio(id=cur.lastrowid, ra_id=ra_id, letra=letra, peso=peso, orden=siguiente_orden)

    def actualizar_peso_criterio(self, criterio_id: int, peso: float):
        cur = self.conexion.execute("SELECT peso FROM criterio WHERE id = ?;", (criterio_id,))
        fila = cur.fetchone()
        peso_anterior = fila[0] if fila else None

        self.conexion.execute("UPDATE criterio SET peso = ? WHERE id = ?;", (peso, criterio_id))
        self.conexion.commit()

        # Si el peso ha cambiado, hay que recalcular el peso de este
        # criterio en TODOS los instrumentos donde ya estuviera marcado:
        # ese peso se calcula a partir del peso del criterio en su RA,
        # así que si este cambia, el recalculado de cada instrumento
        # queda desactualizado hasta que se vuelva a marcar/desmarcar
        # algo en ese instrumento — forzar el recálculo aquí evita ese
        # desajuste silencioso (visible, por ejemplo, en Trazabilidad).
        if peso_anterior is not None and peso_anterior != peso:
            cur = self.conexion.execute(
                "SELECT DISTINCT instrumento_id FROM instrumento_criterio WHERE criterio_id = ?;",
                (criterio_id,),
            )
            for (instrumento_id,) in cur.fetchall():
                self.recalcular_pesos_criterios_de_instrumento(instrumento_id)

    def eliminar_criterio(self, criterio_id: int):
        # Antes de borrar, identificamos qué instrumentos tenían este
        # criterio marcado: tras el borrado (que se propaga en cascada a
        # instrumento_criterio), los demás criterios del mismo RA que
        # sigan marcados en esos instrumentos deben recalcular su peso,
        # ya que el total entre el que quede ha cambiado.
        cur = self.conexion.execute(
            "SELECT instrumento_id FROM instrumento_criterio WHERE criterio_id = ?;", (criterio_id,)
        )
        instrumentos_afectados = [r[0] for r in cur.fetchall()]
        self.conexion.execute("DELETE FROM criterio WHERE id = ?;", (criterio_id,))
        self.conexion.commit()
        for instrumento_id in instrumentos_afectados:
            self.recalcular_pesos_criterios_de_instrumento(instrumento_id)

    def suma_pesos_criterios_de_ra(self, ra_id: int) -> float:
        cur = self.conexion.execute("SELECT COALESCE(SUM(peso), 0) FROM criterio WHERE ra_id = ?;", (ra_id,))
        return cur.fetchone()[0]

    # -- instrumentos de evaluación -------------------------------------------

    def listar_instrumentos(self, evaluacion_id: int) -> list[InstrumentoEvaluacion]:
        cur = self.conexion.execute(
            """SELECT id, evaluacion_id, nombre, tipo, peso, nota_maxima, orden
               FROM instrumento_evaluacion WHERE evaluacion_id = ? ORDER BY orden;""",
            (evaluacion_id,),
        )
        return [
            InstrumentoEvaluacion(
                id=r[0], evaluacion_id=r[1], nombre=r[2], tipo=r[3], peso=r[4],
                nota_maxima=r[5], orden=r[6],
            )
            for r in cur.fetchall()
        ]

    def obtener_instrumento(self, instrumento_id: int) -> InstrumentoEvaluacion | None:
        cur = self.conexion.execute(
            """SELECT id, evaluacion_id, nombre, tipo, peso, nota_maxima, orden
               FROM instrumento_evaluacion WHERE id = ?;""",
            (instrumento_id,),
        )
        r = cur.fetchone()
        if r is None:
            return None
        return InstrumentoEvaluacion(
            id=r[0], evaluacion_id=r[1], nombre=r[2], tipo=r[3], peso=r[4],
            nota_maxima=r[5], orden=r[6],
        )

    def suma_pesos_instrumentos(self, evaluacion_id: int) -> float:
        cur = self.conexion.execute(
            "SELECT COALESCE(SUM(peso), 0) FROM instrumento_evaluacion WHERE evaluacion_id = ?;",
            (evaluacion_id,),
        )
        return cur.fetchone()[0]

    def crear_instrumento(
        self, evaluacion_id: int, nombre: str, tipo: str, nota_maxima: float = 10.0
    ) -> InstrumentoEvaluacion:
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre del instrumento no puede estar vacío.")
        if tipo not in TIPOS_INSTRUMENTO:
            raise ValueError(f"Tipo de instrumento no reconocido: {tipo}")

        cur = self.conexion.execute(
            "SELECT COALESCE(MAX(orden), 0) + 1 FROM instrumento_evaluacion WHERE evaluacion_id = ?;",
            (evaluacion_id,),
        )
        siguiente_orden = cur.fetchone()[0]

        instrumentos_existentes = self.listar_instrumentos(evaluacion_id)
        peso_inicial = 100.0 if not instrumentos_existentes else 0.0

        cur = self.conexion.execute(
            """INSERT INTO instrumento_evaluacion
               (evaluacion_id, nombre, tipo, peso, nota_maxima, orden)
               VALUES (?, ?, ?, ?, ?, ?);""",
            (evaluacion_id, nombre, tipo, peso_inicial, nota_maxima, siguiente_orden),
        )
        self.conexion.commit()
        return InstrumentoEvaluacion(
            id=cur.lastrowid, evaluacion_id=evaluacion_id, nombre=nombre, tipo=tipo,
            peso=peso_inicial, nota_maxima=nota_maxima, orden=siguiente_orden,
        )

    def actualizar_instrumento(self, instrumento_id: int, nombre: str, peso: float, nota_maxima: float):
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre del instrumento no puede estar vacío.")
        if nota_maxima <= 0:
            raise ValueError("La nota máxima debe ser mayor que 0.")
        self.conexion.execute(
            "UPDATE instrumento_evaluacion SET nombre = ?, peso = ?, nota_maxima = ? WHERE id = ?;",
            (nombre, peso, nota_maxima, instrumento_id),
        )
        self.conexion.commit()
        # Nota: el peso GLOBAL del instrumento ya no afecta al peso de
        # cada criterio dentro de él (eso ahora depende solo del peso
        # del criterio en su RA, ver recalcular_pesos_criterios_de_instrumento).
        # El peso global se usa únicamente para repartir entre varios
        # instrumentos que evalúen el mismo criterio.

    def eliminar_instrumento(self, instrumento_id: int):
        self.conexion.execute("DELETE FROM instrumento_evaluacion WHERE id = ?;", (instrumento_id,))
        self.conexion.commit()

    # -- pruebas de un instrumento (para MEDIA_ARITMETICA / MEDIA_PONDERADA) --

    def listar_pruebas(self, instrumento_id: int) -> list[PruebaInstrumento]:
        cur = self.conexion.execute(
            """SELECT id, instrumento_id, nombre, peso, orden
               FROM prueba_instrumento WHERE instrumento_id = ? ORDER BY orden;""",
            (instrumento_id,),
        )
        return [
            PruebaInstrumento(id=r[0], instrumento_id=r[1], nombre=r[2], peso=r[3], orden=r[4])
            for r in cur.fetchall()
        ]

    def suma_pesos_pruebas(self, instrumento_id: int) -> float:
        cur = self.conexion.execute(
            "SELECT COALESCE(SUM(peso), 0) FROM prueba_instrumento WHERE instrumento_id = ?;",
            (instrumento_id,),
        )
        return cur.fetchone()[0]

    def agregar_prueba(self, instrumento_id: int, nombre: str | None = None) -> PruebaInstrumento:
        cur = self.conexion.execute(
            "SELECT COALESCE(MAX(orden), 0) + 1 FROM prueba_instrumento WHERE instrumento_id = ?;",
            (instrumento_id,),
        )
        siguiente_orden = cur.fetchone()[0]
        nombre = (nombre or f"Prueba {siguiente_orden}").strip()

        pruebas_existentes = self.listar_pruebas(instrumento_id)
        peso_inicial = 100.0 if not pruebas_existentes else 0.0

        cur = self.conexion.execute(
            "INSERT INTO prueba_instrumento (instrumento_id, nombre, peso, orden) VALUES (?, ?, ?, ?);",
            (instrumento_id, nombre, peso_inicial, siguiente_orden),
        )
        self.conexion.commit()
        return PruebaInstrumento(
            id=cur.lastrowid, instrumento_id=instrumento_id, nombre=nombre,
            peso=peso_inicial, orden=siguiente_orden,
        )

    def actualizar_prueba(self, prueba_id: int, nombre: str, peso: float):
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre de la prueba no puede estar vacío.")
        self.conexion.execute(
            "UPDATE prueba_instrumento SET nombre = ?, peso = ? WHERE id = ?;", (nombre, peso, prueba_id)
        )
        self.conexion.commit()

    def eliminar_prueba(self, prueba_id: int):
        self.conexion.execute("DELETE FROM prueba_instrumento WHERE id = ?;", (prueba_id,))
        self.conexion.commit()

    # -- relación instrumento <-> criterio (con peso propio, "modelo b") -----

    def listar_criterios_de_instrumento(self, instrumento_id: int) -> list[InstrumentoCriterio]:
        cur = self.conexion.execute(
            """SELECT id, instrumento_id, criterio_id, peso, peso_manual
               FROM instrumento_criterio WHERE instrumento_id = ?;""",
            (instrumento_id,),
        )
        return [
            InstrumentoCriterio(
                id=r[0], instrumento_id=r[1], criterio_id=r[2], peso=r[3], peso_manual=bool(r[4])
            )
            for r in cur.fetchall()
        ]

    def criterios_marcados_de_instrumento(self, instrumento_id: int) -> set[int]:
        return {ic.criterio_id for ic in self.listar_criterios_de_instrumento(instrumento_id)}

    def marcar_criterio_en_instrumento(self, instrumento_id: int, criterio_id: int, peso: float = 100.0):
        """Marca que este instrumento evalúa este criterio. El peso que
        se pasa aquí es solo un valor de partida (se recalcula
        inmediatamente después con recalcular_pesos_criterios_de_instrumento,
        así que en la práctica da igual lo que se indique).
        """
        self.conexion.execute(
            """INSERT INTO instrumento_criterio (instrumento_id, criterio_id, peso, peso_manual)
               VALUES (?, ?, ?, 0)
               ON CONFLICT(instrumento_id, criterio_id)
               DO UPDATE SET peso = excluded.peso, peso_manual = 0;""",
            (instrumento_id, criterio_id, peso),
        )
        self.conexion.commit()
        self.recalcular_pesos_criterios_de_instrumento(instrumento_id)

    def desmarcar_criterio_en_instrumento(self, instrumento_id: int, criterio_id: int):
        self.conexion.execute(
            "DELETE FROM instrumento_criterio WHERE instrumento_id = ? AND criterio_id = ?;",
            (instrumento_id, criterio_id),
        )
        self.conexion.execute(
            "DELETE FROM nota_criterio_instrumento_alumno WHERE instrumento_id = ? AND criterio_id = ?;",
            (instrumento_id, criterio_id),
        )
        self.conexion.commit()
        self.recalcular_pesos_criterios_de_instrumento(instrumento_id)

    def recalcular_pesos_criterios_de_instrumento(self, instrumento_id: int):
        """Recalcula el peso de cada criterio marcado en este
        instrumento, SOLO entre los criterios de su MISMO RA que también
        estén marcados en este mismo instrumento (si el instrumento
        marca criterios de varios RA, cada RA se redistribuye por
        separado, sin mezclarse entre sí).

        Ejemplo: un RA con criterios de peso 30/30/40 (sobre 100 dentro
        del RA). Si el instrumento solo marca los dos primeros, sus
        pesos originales (30 y 30) se reescalan sobre su nueva suma (60)
        para que ese instrumento les dé 50% y 50% entre sí.

        El docente nunca edita esto a mano: se recalcula solo cada vez
        que se marca o desmarca un criterio en el instrumento.
        """
        relaciones = self.listar_criterios_de_instrumento(instrumento_id)
        if not relaciones:
            return
        ids_marcados = {r.criterio_id for r in relaciones}

        # Agrupar los criterios marcados por su RA, usando su peso
        # ORIGINAL (el definido en "RA y Criterios"), no el que tuvieran
        # hasta ahora en instrumento_criterio.
        cur = self.conexion.execute(
            f"""SELECT c.id, c.ra_id, c.peso FROM criterio c
                WHERE c.id IN ({','.join('?' for _ in ids_marcados)});""",
            tuple(ids_marcados),
        )
        peso_y_ra_por_criterio = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

        suma_por_ra: dict[int, float] = {}
        for criterio_id in ids_marcados:
            ra_id, peso_original = peso_y_ra_por_criterio.get(criterio_id, (None, 0.0))
            if ra_id is None:
                continue
            suma_por_ra[ra_id] = suma_por_ra.get(ra_id, 0.0) + peso_original

        for criterio_id in ids_marcados:
            ra_id, peso_original = peso_y_ra_por_criterio.get(criterio_id, (None, 0.0))
            if ra_id is None:
                continue
            suma_ra = suma_por_ra.get(ra_id, 0.0)
            peso_recalculado = (peso_original * 100.0 / suma_ra) if suma_ra > 0 else 0.0
            self.conexion.execute(
                "UPDATE instrumento_criterio SET peso = ? WHERE instrumento_id = ? AND criterio_id = ?;",
                (round(peso_recalculado, 4), instrumento_id, criterio_id),
            )
        self.conexion.commit()

    # -- notas de pruebas (ARITMETICA / PONDERADA) ---------------------------

    def obtener_notas_pruebas(self, instrumento_id: int) -> dict[tuple[int, int], float | None]:
        cur = self.conexion.execute(
            """SELECT np.prueba_id, np.alumno_id, np.valor
               FROM nota_prueba np
               JOIN prueba_instrumento pi ON pi.id = np.prueba_id
               WHERE pi.instrumento_id = ?;""",
            (instrumento_id,),
        )
        return {(r[0], r[1]): r[2] for r in cur.fetchall()}

    def guardar_nota_prueba(self, prueba_id: int, alumno_id: int, valor: float | None):
        self.conexion.execute(
            """INSERT INTO nota_prueba (prueba_id, alumno_id, valor) VALUES (?, ?, ?)
               ON CONFLICT(prueba_id, alumno_id) DO UPDATE SET valor = excluded.valor;""",
            (prueba_id, alumno_id, valor),
        )
        self.conexion.commit()

    # -- nota general del instrumento por alumno -----------------------------

    def obtener_notas_instrumento(self, instrumento_id: int) -> dict[int, float | None]:
        cur = self.conexion.execute(
            "SELECT alumno_id, valor FROM nota_instrumento_alumno WHERE instrumento_id = ?;",
            (instrumento_id,),
        )
        return {r[0]: r[1] for r in cur.fetchall()}

    def guardar_nota_instrumento(self, instrumento_id: int, alumno_id: int, valor: float | None):
        self.conexion.execute(
            """INSERT INTO nota_instrumento_alumno (instrumento_id, alumno_id, valor)
               VALUES (?, ?, ?)
               ON CONFLICT(instrumento_id, alumno_id) DO UPDATE SET valor = excluded.valor;""",
            (instrumento_id, alumno_id, valor),
        )
        self.conexion.commit()

    # -- nota que el instrumento aporta a cada criterio, por alumno ----------

    def obtener_notas_criterio_instrumento(
        self, instrumento_id: int
    ) -> dict[tuple[int, int], tuple[float | None, bool]]:
        cur = self.conexion.execute(
            """SELECT criterio_id, alumno_id, valor, es_manual
               FROM nota_criterio_instrumento_alumno WHERE instrumento_id = ?;""",
            (instrumento_id,),
        )
        return {(r[0], r[1]): (r[2], bool(r[3])) for r in cur.fetchall()}

    def guardar_nota_criterio_instrumento(
        self, instrumento_id: int, criterio_id: int, alumno_id: int, valor: float | None, es_manual: bool,
    ):
        self.conexion.execute(
            """INSERT INTO nota_criterio_instrumento_alumno
               (instrumento_id, criterio_id, alumno_id, valor, es_manual)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(instrumento_id, criterio_id, alumno_id)
               DO UPDATE SET valor = excluded.valor, es_manual = excluded.es_manual;""",
            (instrumento_id, criterio_id, alumno_id, valor, 1 if es_manual else 0),
        )
        self.conexion.commit()

    # -- cálculo de la nota general del instrumento --------------------------

    def calcular_nota_instrumento_para_alumno(
        self, instrumento: InstrumentoEvaluacion, alumno_id: int
    ) -> float | None:
        if instrumento.tipo == TIPO_EXAMEN:
            notas = self.obtener_notas_instrumento(instrumento.id)
            valor_crudo = notas.get(alumno_id)
            if valor_crudo is None:
                return None
            return round(valor_crudo * 10.0 / instrumento.nota_maxima, 2)

        if instrumento.tipo == TIPO_MEDIA_ARITMETICA:
            pruebas = self.listar_pruebas(instrumento.id)
            notas = self.obtener_notas_pruebas(instrumento.id)
            valores = [
                notas.get((p.id, alumno_id)) for p in pruebas if notas.get((p.id, alumno_id)) is not None
            ]
            if not valores:
                return None
            return round(sum(valores) / len(valores), 2)

        if instrumento.tipo == TIPO_MEDIA_PONDERADA:
            pruebas = self.listar_pruebas(instrumento.id)
            notas = self.obtener_notas_pruebas(instrumento.id)
            suma_pesos = 0.0
            suma_ponderada = 0.0
            for p in pruebas:
                valor = notas.get((p.id, alumno_id))
                if valor is None:
                    continue
                suma_pesos += p.peso
                suma_ponderada += valor * p.peso
            if suma_pesos == 0:
                return None
            return round(suma_ponderada / suma_pesos, 2)

        return None  # MANUAL no se calcula aquí

    def nota_representativa_instrumento_para_alumno(
        self, instrumento: InstrumentoEvaluacion, alumno_id: int
    ) -> float | None:
        if instrumento.tipo != TIPO_MANUAL:
            return self.calcular_nota_instrumento_para_alumno(instrumento, alumno_id)

        notas_criterio = self.obtener_notas_criterio_instrumento(instrumento.id)
        valores = [
            valor
            for (criterio_id, a_id), (valor, _es_manual) in notas_criterio.items()
            if a_id == alumno_id and valor is not None
        ]
        if not valores:
            return None
        return round(sum(valores) / len(valores), 2)

    def recalcular_notas_criterio_para_instrumento(self, instrumento: InstrumentoEvaluacion):
        """Tras cambiar una nota general (examen/aritmética/ponderada),
        vuelve a copiar el valor calculado a todos los criterios
        marcados de este instrumento, PERO solo para las celdas que el
        docente no haya editado a mano (es_manual=False).
        """
        if instrumento.tipo == TIPO_MANUAL:
            return

        criterios_ids = self.criterios_marcados_de_instrumento(instrumento.id)
        if not criterios_ids:
            return

        alumno_ids = set(self.obtener_notas_instrumento(instrumento.id).keys())
        if instrumento.tipo in (TIPO_MEDIA_ARITMETICA, TIPO_MEDIA_PONDERADA):
            alumno_ids |= {a_id for (_p_id, a_id) in self.obtener_notas_pruebas(instrumento.id).keys()}
        existentes = self.obtener_notas_criterio_instrumento(instrumento.id)
        alumno_ids |= {a_id for (_c_id, a_id) in existentes.keys()}

        for alumno_id in alumno_ids:
            valor_calculado = self.calcular_nota_instrumento_para_alumno(instrumento, alumno_id)
            for criterio_id in criterios_ids:
                _valor_previo, es_manual = existentes.get((criterio_id, alumno_id), (None, False))
                if es_manual:
                    continue
                self.guardar_nota_criterio_instrumento(
                    instrumento.id, criterio_id, alumno_id, valor_calculado, es_manual=False
                )

    # -- cálculo agregado: nota de cada criterio en una evaluación -----------
    #
    # Idéntica mecánica que en EVACYL: cuando varios instrumentos evalúan
    # el mismo criterio, la nota de ese criterio para un alumno es la
    # media ponderada de las notas de los instrumentos que SÍ tienen nota
    # para él en ese criterio, usando el peso instrumento↔criterio,
    # redistribuido dinámicamente entre los instrumentos presentes.

    def calcular_notas_criterios_evaluacion(
        self, evaluacion_id: int, modulo_id: int
    ) -> dict[tuple[int, int], float | None]:
        """Devuelve {(criterio_id, alumno_id): nota_0_10 o None} para
        todos los criterios del módulo (de todos sus RA) y todos los
        alumnos, considerando los instrumentos de esta evaluación.
        """
        criterios_con_ra = self.listar_criterios_de_modulo(modulo_id)
        instrumentos = self.listar_instrumentos(evaluacion_id)
        alumnos = self.listar_alumnos(modulo_id)

        notas_por_instrumento = {
            inst.id: self.obtener_notas_criterio_instrumento(inst.id) for inst in instrumentos
        }
        pesos_por_instrumento = {
            inst.id: {ic.criterio_id: ic.peso for ic in self.listar_criterios_de_instrumento(inst.id)}
            for inst in instrumentos
        }

        resultado: dict[tuple[int, int], float | None] = {}
        for _ra, criterio in criterios_con_ra:
            for alumno in alumnos:
                suma_pesos = 0.0
                suma_ponderada = 0.0
                for inst in instrumentos:
                    peso_ie_criterio = pesos_por_instrumento[inst.id].get(criterio.id)
                    if peso_ie_criterio is None:
                        continue
                    valor, _es_manual = notas_por_instrumento[inst.id].get(
                        (criterio.id, alumno.id), (None, False)
                    )
                    if valor is None:
                        continue
                    suma_pesos += peso_ie_criterio
                    suma_ponderada += valor * peso_ie_criterio
                if suma_pesos == 0:
                    resultado[(criterio.id, alumno.id)] = None
                else:
                    resultado[(criterio.id, alumno.id)] = round(suma_ponderada / suma_pesos, 2)
        return resultado

    # -- cálculo agregado: nota de cada RA en una evaluación (NUEVO) ---------
    #
    # Primer nivel de la cascada propia de FP: la nota de un RA es la
    # media ponderada de sus criterios (peso del criterio DENTRO de su
    # RA), redistribuida dinámicamente entre los criterios que el alumno
    # SÍ tiene calificados en esa evaluación.

    def calcular_notas_ra_evaluacion(
        self, evaluacion_id: int, modulo_id: int
    ) -> dict[tuple[int, int], float | None]:
        """Devuelve {(ra_id, alumno_id): nota_0_10 o None}."""
        notas_criterio = self.calcular_notas_criterios_evaluacion(evaluacion_id, modulo_id)
        alumnos = self.listar_alumnos(modulo_id)
        ras = self.listar_ra(modulo_id)

        resultado: dict[tuple[int, int], float | None] = {}
        for ra in ras:
            criterios_del_ra = self.listar_criterios_de_ra(ra.id)
            for alumno in alumnos:
                suma_pesos = 0.0
                suma_ponderada = 0.0
                for criterio in criterios_del_ra:
                    valor = notas_criterio.get((criterio.id, alumno.id))
                    if valor is None:
                        continue
                    suma_pesos += criterio.peso
                    suma_ponderada += valor * criterio.peso
                resultado[(ra.id, alumno.id)] = (
                    None if suma_pesos == 0 else round(suma_ponderada / suma_pesos, 2)
                )
        return resultado

    # -- cálculo agregado: nota final del módulo en una evaluación (NUEVO) ---
    #
    # Segundo nivel de la cascada: la nota del módulo es la media
    # ponderada de sus RA (peso del RA dentro del módulo), redistribuida
    # dinámicamente entre los RA que el alumno SÍ tiene calificados.

    def calcular_notas_modulo_evaluacion(
        self, evaluacion_id: int, modulo_id: int
    ) -> dict[int, float | None]:
        """Devuelve {alumno_id: nota_0_10 o None} con la nota del módulo
        para cada alumno, en una evaluación concreta.
        """
        notas_ra = self.calcular_notas_ra_evaluacion(evaluacion_id, modulo_id)
        alumnos = self.listar_alumnos(modulo_id)
        ras = self.listar_ra(modulo_id)

        resultado: dict[int, float | None] = {}
        for alumno in alumnos:
            suma_pesos = 0.0
            suma_ponderada = 0.0
            for ra in ras:
                valor = notas_ra.get((ra.id, alumno.id))
                if valor is None:
                    continue
                suma_pesos += ra.peso
                suma_ponderada += valor * ra.peso
            resultado[alumno.id] = None if suma_pesos == 0 else round(suma_ponderada / suma_pesos, 2)
        return resultado

    # -- pesos de las evaluaciones parciales usados por FINAL ----------------

    def obtener_pesos_evaluaciones_final(self, modulo_id: int) -> dict[int, float]:
        """Devuelve {evaluacion_id: peso} para las evaluaciones PARCIALES
        de un módulo (no incluye FINAL). Si todavía no se han guardado,
        se inicializan con peso 1 (igual entre todas) por defecto.
        """
        parciales = self.listar_evaluaciones_parciales(modulo_id)
        cur = self.conexion.execute(
            "SELECT evaluacion_id, peso FROM peso_evaluacion_final WHERE modulo_id = ?;",
            (modulo_id,),
        )
        guardados = {r[0]: r[1] for r in cur.fetchall()}
        return {ev.id: guardados.get(ev.id, 1.0) for ev in parciales}

    def actualizar_peso_evaluacion_final(self, modulo_id: int, evaluacion_id: int, peso: float):
        self.conexion.execute(
            """INSERT INTO peso_evaluacion_final (modulo_id, evaluacion_id, peso)
               VALUES (?, ?, ?)
               ON CONFLICT(modulo_id, evaluacion_id) DO UPDATE SET peso = excluded.peso;""",
            (modulo_id, evaluacion_id, peso),
        )
        self.conexion.commit()

    # -- cálculo de FINAL: misma mecánica en cascada, agregando las evaluaciones parciales --
    #
    # FINAL no tiene instrumentos propios: trata a las evaluaciones
    # parciales como si fueran "instrumentos" de la nota de criterio,
    # usando su peso (configurable, por defecto igual entre todas) y
    # redistribuyendo dinámicamente entre las que sí tienen nota para ese
    # alumno en ese criterio. A partir de ahí, RA y módulo se calculan
    # igual que en cualquier evaluación.

    def calcular_notas_criterios_final(self, modulo_id: int) -> dict[tuple[int, int], float | None]:
        """Devuelve {(criterio_id, alumno_id): nota_0_10 o None} para
        FINAL, agregando las notas de criterio de todas las evaluaciones
        parciales del módulo.
        """
        criterios_con_ra = self.listar_criterios_de_modulo(modulo_id)
        alumnos = self.listar_alumnos(modulo_id)
        parciales = self.listar_evaluaciones_parciales(modulo_id)
        pesos_evaluaciones = self.obtener_pesos_evaluaciones_final(modulo_id)

        notas_por_evaluacion = {
            ev.id: self.calcular_notas_criterios_evaluacion(ev.id, modulo_id) for ev in parciales
        }

        resultado: dict[tuple[int, int], float | None] = {}
        for _ra, criterio in criterios_con_ra:
            for alumno in alumnos:
                suma_pesos = 0.0
                suma_ponderada = 0.0
                for ev in parciales:
                    valor = notas_por_evaluacion[ev.id].get((criterio.id, alumno.id))
                    if valor is None:
                        continue
                    peso_ev = pesos_evaluaciones.get(ev.id, 1.0)
                    suma_pesos += peso_ev
                    suma_ponderada += valor * peso_ev
                resultado[(criterio.id, alumno.id)] = (
                    None if suma_pesos == 0 else round(suma_ponderada / suma_pesos, 2)
                )
        return resultado

    def calcular_notas_ra_final(self, modulo_id: int) -> dict[tuple[int, int], float | None]:
        """Igual que calcular_notas_ra_evaluacion, pero a partir de las
        notas de criterio combinadas de FINAL.
        """
        notas_criterio = self.calcular_notas_criterios_final(modulo_id)
        alumnos = self.listar_alumnos(modulo_id)
        ras = self.listar_ra(modulo_id)

        resultado: dict[tuple[int, int], float | None] = {}
        for ra in ras:
            criterios_del_ra = self.listar_criterios_de_ra(ra.id)
            for alumno in alumnos:
                suma_pesos = 0.0
                suma_ponderada = 0.0
                for criterio in criterios_del_ra:
                    valor = notas_criterio.get((criterio.id, alumno.id))
                    if valor is None:
                        continue
                    suma_pesos += criterio.peso
                    suma_ponderada += valor * criterio.peso
                resultado[(ra.id, alumno.id)] = (
                    None if suma_pesos == 0 else round(suma_ponderada / suma_pesos, 2)
                )
        return resultado

    def calcular_notas_modulo_final(self, modulo_id: int) -> dict[int, float | None]:
        """Nota final de curso del módulo, para cada alumno."""
        notas_ra = self.calcular_notas_ra_final(modulo_id)
        alumnos = self.listar_alumnos(modulo_id)
        ras = self.listar_ra(modulo_id)

        resultado: dict[int, float | None] = {}
        for alumno in alumnos:
            suma_pesos = 0.0
            suma_ponderada = 0.0
            for ra in ras:
                valor = notas_ra.get((ra.id, alumno.id))
                if valor is None:
                    continue
                suma_pesos += ra.peso
                suma_ponderada += valor * ra.peso
            resultado[alumno.id] = None if suma_pesos == 0 else round(suma_ponderada / suma_pesos, 2)
        return resultado


    # -- "deshacer" de eliminaciones -----------------------------------------
    #
    # Igual mecanismo que en EVACYL: antes de borrar un alumno, criterio o
    # instrumento, se captura ese registro y todo lo que depende de él en
    # cascada, para poder reinsertarlo exactamente igual si el docente
    # pulsa "deshacer". Solo se conserva el último elemento borrado.

    _TABLAS_DEPENDIENTES = {
        "alumno": [
            ("nota_prueba", "alumno_id"),
            ("nota_instrumento_alumno", "alumno_id"),
            ("nota_criterio_instrumento_alumno", "alumno_id"),
        ],
        "criterio": [
            ("instrumento_criterio", "criterio_id"),
            ("nota_criterio_instrumento_alumno", "criterio_id"),
        ],
        "instrumento_evaluacion": [
            ("prueba_instrumento", "instrumento_id"),
            ("instrumento_criterio", "instrumento_id"),
            ("nota_instrumento_alumno", "instrumento_id"),
            ("nota_criterio_instrumento_alumno", "instrumento_id"),
        ],
    }

    def _capturar_subarbol(self, tabla_principal: str, id_principal: int) -> dict | None:
        cur = self.conexion.execute(f"SELECT * FROM {tabla_principal} WHERE id = ?;", (id_principal,))
        columnas = [d[0] for d in cur.description]
        fila = cur.fetchone()
        if fila is None:
            return None
        captura = {
            "tabla_principal": tabla_principal,
            "fila_principal": dict(zip(columnas, fila)),
            "dependientes": [],
        }

        if tabla_principal == "instrumento_evaluacion":
            cur_pruebas = self.conexion.execute(
                "SELECT * FROM prueba_instrumento WHERE instrumento_id = ?;", (id_principal,)
            )
            columnas_p = [d[0] for d in cur_pruebas.description]
            filas_pruebas = [dict(zip(columnas_p, f)) for f in cur_pruebas.fetchall()]
            captura["dependientes"].append(("prueba_instrumento", filas_pruebas))

            for fila_prueba in filas_pruebas:
                cur_np = self.conexion.execute(
                    "SELECT * FROM nota_prueba WHERE prueba_id = ?;", (fila_prueba["id"],)
                )
                columnas_np = [d[0] for d in cur_np.description]
                filas_np = [dict(zip(columnas_np, f)) for f in cur_np.fetchall()]
                captura["dependientes"].append(("nota_prueba", filas_np))

            for tabla_dep, columna_fk in [
                ("instrumento_criterio", "instrumento_id"),
                ("nota_instrumento_alumno", "instrumento_id"),
                ("nota_criterio_instrumento_alumno", "instrumento_id"),
            ]:
                cur_dep = self.conexion.execute(
                    f"SELECT * FROM {tabla_dep} WHERE {columna_fk} = ?;", (id_principal,)
                )
                columnas_dep = [d[0] for d in cur_dep.description]
                filas_dep = [dict(zip(columnas_dep, f)) for f in cur_dep.fetchall()]
                captura["dependientes"].append((tabla_dep, filas_dep))
        else:
            for tabla_dep, columna_fk in self._TABLAS_DEPENDIENTES.get(tabla_principal, []):
                cur_dep = self.conexion.execute(
                    f"SELECT * FROM {tabla_dep} WHERE {columna_fk} = ?;", (id_principal,)
                )
                columnas_dep = [d[0] for d in cur_dep.description]
                filas_dep = [dict(zip(columnas_dep, f)) for f in cur_dep.fetchall()]
                captura["dependientes"].append((tabla_dep, filas_dep))

        return captura

    def _restaurar_subarbol(self, captura: dict):
        tabla_principal = captura["tabla_principal"]
        fila_principal = captura["fila_principal"]
        columnas = list(fila_principal.keys())
        marcadores = ", ".join("?" for _ in columnas)
        nombres_columnas = ", ".join(columnas)
        self.conexion.execute(
            f"INSERT INTO {tabla_principal} ({nombres_columnas}) VALUES ({marcadores});",
            [fila_principal[c] for c in columnas],
        )
        for tabla_dep, filas_dep in captura["dependientes"]:
            for fila_dep in filas_dep:
                columnas_dep = list(fila_dep.keys())
                marcadores_dep = ", ".join("?" for _ in columnas_dep)
                nombres_columnas_dep = ", ".join(columnas_dep)
                self.conexion.execute(
                    f"INSERT INTO {tabla_dep} ({nombres_columnas_dep}) VALUES ({marcadores_dep});",
                    [fila_dep[c] for c in columnas_dep],
                )
        self.conexion.commit()

    def eliminar_alumno_con_deshacer(self, alumno_id: int) -> dict | None:
        captura = self._capturar_subarbol("alumno", alumno_id)
        self.eliminar_alumno(alumno_id)
        return captura

    def eliminar_criterio_con_deshacer(self, criterio_id: int) -> dict | None:
        captura = self._capturar_subarbol("criterio", criterio_id)
        self.eliminar_criterio(criterio_id)
        return captura

    def eliminar_instrumento_con_deshacer(self, instrumento_id: int) -> dict | None:
        captura = self._capturar_subarbol("instrumento_evaluacion", instrumento_id)
        self.eliminar_instrumento(instrumento_id)
        return captura

    def restaurar_eliminacion(self, captura: dict):
        self._restaurar_subarbol(captura)

    # -- copiar estructura de un módulo a otro (misma BD u otro curso) ------
    #
    # Pensado para cuando un docente imparte el mismo módulo en varios
    # grupos, o repite estructura curso tras curso: en vez de montar RA,
    # criterios e instrumentos desde cero cada vez, copia la estructura ya
    # hecha de un módulo existente a un módulo nuevo (vacío de alumnado y
    # notas). base_datos_origen y self pueden ser la misma instancia
    # (copiar dentro del mismo curso.db) o instancias distintas abiertas
    # sobre dos archivos .db diferentes (copiar entre cursos académicos
    # distintos). Siempre se copian TODOS los RA del módulo origen.

    def copiar_ra_y_criterios_desde(
        self, base_datos_origen: "BaseDatosModulo", modulo_origen_id: int, modulo_destino_id: int
    ) -> dict[int, int]:
        """Copia todos los RA (número, descripción, peso) y sus
        criterios (letra + peso) del módulo origen al módulo destino,
        sin tocar alumnado ni notas. Devuelve {criterio_id_origen:
        criterio_id_destino}, útil para copiar_instrumentos_desde si se
        llama justo después.
        """
        mapa_criterios: dict[int, int] = {}
        for ra_origen in base_datos_origen.listar_ra(modulo_origen_id):
            ra_destino = self.agregar_ra(
                modulo_destino_id, ra_origen.numero, ra_origen.descripcion, ra_origen.peso
            )
            for criterio_origen in base_datos_origen.listar_criterios_de_ra(ra_origen.id):
                criterio_destino = self.agregar_criterio_manual(
                    ra_destino.id, criterio_origen.letra, criterio_origen.peso
                )
                mapa_criterios[criterio_origen.id] = criterio_destino.id
        return mapa_criterios

    def copiar_instrumentos_desde(
        self,
        base_datos_origen: "BaseDatosModulo",
        modulo_origen_id: int,
        modulo_destino_id: int,
        mapa_criterios: dict[int, int],
    ):
        """Copia los instrumentos de evaluación de cada evaluación
        parcial del módulo origen al módulo destino: su nombre, tipo,
        peso y nota máxima; sus pruebas con su peso; y qué criterios
        marca cada uno, con el peso de esa relación. No copia ninguna
        nota de alumnado.

        Requiere que ambos módulos tengan el MISMO número de
        evaluaciones parciales (se emparejan por su posición: la 1ª
        evaluación del origen con la 1ª del destino, etc.) — comprobar
        esto antes de llamar con puede_copiar_instrumentos().

        mapa_criterios debe ser el devuelto por
        copiar_ra_y_criterios_desde, para traducir los ids de criterio
        de origen a los del destino (son distintos aunque la letra y el
        RA sean los mismos).
        """
        evaluaciones_origen = base_datos_origen.listar_evaluaciones_parciales(modulo_origen_id)
        evaluaciones_destino = self.listar_evaluaciones_parciales(modulo_destino_id)
        evaluaciones_destino_por_orden = {ev.orden: ev for ev in evaluaciones_destino}

        for evaluacion_origen in evaluaciones_origen:
            evaluacion_destino = evaluaciones_destino_por_orden.get(evaluacion_origen.orden)
            if evaluacion_destino is None:
                continue  # no debería ocurrir si se comprobó puede_copiar_instrumentos() antes

            for instrumento_origen in base_datos_origen.listar_instrumentos(evaluacion_origen.id):
                instrumento_destino = self.crear_instrumento(
                    evaluacion_destino.id,
                    instrumento_origen.nombre,
                    instrumento_origen.tipo,
                    instrumento_origen.nota_maxima,
                )
                self.actualizar_instrumento(
                    instrumento_destino.id,
                    instrumento_origen.nombre,
                    instrumento_origen.peso,
                    instrumento_origen.nota_maxima,
                )

                for prueba_origen in base_datos_origen.listar_pruebas(instrumento_origen.id):
                    prueba_destino = self.agregar_prueba(instrumento_destino.id, prueba_origen.nombre)
                    self.actualizar_prueba(prueba_destino.id, prueba_origen.nombre, prueba_origen.peso)

                for relacion_origen in base_datos_origen.listar_criterios_de_instrumento(instrumento_origen.id):
                    criterio_destino_id = mapa_criterios.get(relacion_origen.criterio_id)
                    if criterio_destino_id is None:
                        continue
                    self.marcar_criterio_en_instrumento(
                        instrumento_destino.id, criterio_destino_id, peso=relacion_origen.peso
                    )

    def puede_copiar_instrumentos(
        self, base_datos_origen: "BaseDatosModulo", modulo_origen_id: int, modulo_destino_id: int
    ) -> bool:
        """True si el módulo origen y el módulo destino tienen el mismo
        número de evaluaciones parciales (condición necesaria para que
        copiar_instrumentos_desde pueda emparejarlas por posición).
        """
        n_origen = len(base_datos_origen.listar_evaluaciones_parciales(modulo_origen_id))
        n_destino = len(self.listar_evaluaciones_parciales(modulo_destino_id))
        return n_origen == n_destino

    # -- trazabilidad: qué instrumento/evaluación evalúa cada criterio ------

    def trazabilidad_criterios_instrumentos(
        self, evaluacion_id: int, modulo_id: int
    ) -> tuple[list[tuple[ResultadoAprendizaje, Criterio]], list[InstrumentoEvaluacion], dict[tuple[int, int], float | None]]:
        """Para una evaluación parcial: devuelve (criterios_con_ra,
        instrumentos, pesos), donde pesos[(criterio_id, instrumento_id)]
        es el peso de ese instrumento para ese criterio (ya calculado
        automáticamente a partir del peso del criterio en su RA), o
        None si ese instrumento no evalúa ese criterio. Reutilizado
        tanto por la exportación a Excel como por la pestaña de
        Trazabilidad en pantalla.
        """
        criterios_con_ra = self.listar_criterios_de_modulo(modulo_id)
        instrumentos = self.listar_instrumentos(evaluacion_id)
        pesos_por_instrumento = {
            instrumento.id: {
                ic.criterio_id: ic.peso for ic in self.listar_criterios_de_instrumento(instrumento.id)
            }
            for instrumento in instrumentos
        }
        pesos: dict[tuple[int, int], float | None] = {}
        for _ra, criterio in criterios_con_ra:
            for instrumento in instrumentos:
                pesos[(criterio.id, instrumento.id)] = pesos_por_instrumento.get(instrumento.id, {}).get(
                    criterio.id
                )
        return criterios_con_ra, instrumentos, pesos

    def trazabilidad_criterios_evaluaciones(
        self, modulo_id: int
    ) -> tuple[list[tuple[ResultadoAprendizaje, Criterio]], list[Evaluacion], dict[tuple[int, int], bool]]:
        """Para FINAL: devuelve (criterios_con_ra, evaluaciones_parciales,
        evaluado), donde evaluado[(criterio_id, evaluacion_id)] indica
        si ese criterio tuvo alguna nota calculada en esa evaluación
        parcial (para algún alumno).
        """
        criterios_con_ra = self.listar_criterios_de_modulo(modulo_id)
        evaluaciones = self.listar_evaluaciones_parciales(modulo_id)

        criterios_evaluados_por_evaluacion: dict[int, set[int]] = {}
        for evaluacion in evaluaciones:
            notas = self.calcular_notas_criterios_evaluacion(evaluacion.id, modulo_id)
            criterios_evaluados_por_evaluacion[evaluacion.id] = {
                criterio_id for (criterio_id, _alumno_id), valor in notas.items() if valor is not None
            }

        evaluado: dict[tuple[int, int], bool] = {}
        for _ra, criterio in criterios_con_ra:
            for evaluacion in evaluaciones:
                evaluado[(criterio.id, evaluacion.id)] = (
                    criterio.id in criterios_evaluados_por_evaluacion[evaluacion.id]
                )
        return criterios_con_ra, evaluaciones, evaluado
