"""
Punto de entrada de la aplicación.

Ejecutar con:  python main.py

El flujo de arranque es:
  1. VentanaBienvenida      — título, autor, contacto y licencia.
  2. VentanaCarpetaDocente  — elegir (una vez) la carpeta general del
     docente; se recuerda entre ejecuciones.
  3. VentanaInicio          — lista los cursos académicos dentro de esa
     carpeta (cada uno es una subcarpeta con su propio curso.db);
     permite crear uno nuevo o abrir uno existente.
  4. VentanaCurso           — listado de materias del curso académico.

Todas las ventanas se abren maximizadas.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ui.estilos import HOJA_ESTILOS
from ui.ventana_bienvenida import VentanaBienvenida
from ui.ventana_carpeta_docente import VentanaCarpetaDocente
from ui.ventana_inicio import VentanaInicio


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(HOJA_ESTILOS)

    # "Caja" para mantener viva una referencia a la ventana actualmente
    # mostrada; si no se guardara aquí, Python la recolectaría en cuanto
    # saliera de la función que la crea y la ventana se cerraría sola.
    referencia_ventana = {}

    def mostrar_bienvenida(ventana_a_cerrar=None):
        ventana_bienvenida = VentanaBienvenida()
        ventana_bienvenida.conectar_continuar(
            lambda: mostrar_carpeta_docente(ventana_bienvenida)
        )
        ventana_bienvenida.showMaximized()
        referencia_ventana["actual"] = ventana_bienvenida
        if ventana_a_cerrar is not None:
            ventana_a_cerrar.close()

    def mostrar_carpeta_docente(ventana_a_cerrar=None):
        ventana_carpeta = VentanaCarpetaDocente()
        ventana_carpeta.conectar_continuar(
            lambda carpeta: mostrar_ventana_inicio(carpeta, ventana_carpeta)
        )
        ventana_carpeta.showMaximized()
        referencia_ventana["actual"] = ventana_carpeta
        if ventana_a_cerrar is not None:
            ventana_a_cerrar.close()

    def mostrar_ventana_inicio(carpeta_docente, ventana_a_cerrar=None):
        ventana_inicio = VentanaInicio(carpeta_docente)
        ventana_inicio.conectar_ir_a_inicio(lambda: mostrar_bienvenida(ventana_inicio))
        ventana_inicio.showMaximized()
        referencia_ventana["actual"] = ventana_inicio
        if ventana_a_cerrar is not None:
            ventana_a_cerrar.close()

    mostrar_bienvenida()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
