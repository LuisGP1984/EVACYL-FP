# EVACYL FP

**Evaluación que conecta · Futuro que transforma**

Aplicación de escritorio para Windows, hermana de [EVACYL](https://github.com/LuisGP1984/EVACYL), pensada para la evaluación de **módulos de Formación Profesional**: organiza cada módulo en Resultados de Aprendizaje (RA) y sus criterios de evaluación, registra las notas de tus instrumentos de evaluación, calcula automáticamente las calificaciones por RA y la nota final, y genera informes y exportaciones a Excel.

## 📥 Descarga e instalación

1. Ve a la sección [**Releases**](../../releases) de este repositorio.
2. Descarga el archivo `Instalador_EVACYL_FP.exe` de la última versión.
3. Ejecútalo y sigue el asistente de instalación (no requiere permisos de administrador).
4. Al terminar, encontrarás **EVACYL FP** en el menú de inicio de Windows.

📖 También puedes descargar la **guía del docente en PDF** desde la misma sección de Releases, con explicaciones paso a paso e imágenes de cada pantalla.

> ℹ️ Si ya tienes instalado **EVACYL** (la versión para Primaria, Secundaria, Bachillerato y ESPA), no hay ningún conflicto: ambas aplicaciones son completamente independientes entre sí, cada una con su propia carpeta de instalación y su propia configuración.

## ✨ Qué incluye

- Cada módulo se organiza en **Resultados de Aprendizaje (RA)**, cada uno con su peso, y sus criterios de evaluación generados automáticamente con código `numero.letra` (1.a, 1.b, 2.a...).
- Número de **evaluaciones parciales configurable** por módulo (2, 3, o las que correspondan según tu programación), más una evaluación FINAL que las combina.
- Cuatro tipos de instrumentos de evaluación: manual, examen, media aritmética y media ponderada.
- Al marcar un RA en un instrumento se marcan automáticamente todos sus criterios; el peso de cada criterio dentro del instrumento se calcula solo, sin tener que ajustarlo a mano.
- Dos tablas de calificaciones: nota por RA (la vista principal) y detalle por criterio.
- En FINAL, columna **"RA SUPERADOS"**: indica de un vistazo si el alumno tiene todos los RA superados o cuáles le faltan.
- Exportación a Excel con las mismas dos tablas (RA y Criterios).
- Informes individuales de alumno en PDF y Word.
- Copias de seguridad automáticas y sistema de deshacer.
- Todos los datos se guardan en tu propio ordenador — la aplicación no necesita conexión a internet.

## 🛠️ Para desarrolladores

El código fuente completo está en este repositorio. Si quieres ejecutarlo directamente con Python en lugar de usar el instalador:

```
pip install -r requirements.txt
python main.py
```

Si quieres generar tú mismo el `.exe` y el instalador, consulta [`COMO_GENERAR_INSTALADOR.md`](COMO_GENERAR_INSTALADOR.md).

## 👤 Autor

**Luis González Posada**
📧 luis.gonpos@educa.jcyl.es

Con la colaboración del IES Virgen de la Calle, en Palencia.

## 📄 Licencia

Esta obra puede reutilizarse citando al autor y sin fines lucrativos (CC BY-NC).
