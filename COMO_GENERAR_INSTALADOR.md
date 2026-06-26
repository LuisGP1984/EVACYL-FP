# Cómo generar el instalador de Windows

Esta guía explica cómo convertir la aplicación en un instalador normal
de Windows (`Instalador_EVACYL_FP.exe`), que cualquier compañero docente
pueda ejecutar con doble clic, sin tocar cmd ni instalar Python. Se hace
en **tu** ordenador, una sola vez por cada versión nueva que quieras
distribuir; el resultado ya es autónomo.

Son dos fases: primero PyInstaller convierte el código Python en un
`.exe`; después Inno Setup empaqueta ese `.exe` en un instalador de
verdad (con icono, accesos directos y desinstalador).

## Fase 1 — Generar el ejecutable con PyInstaller

1. Asegúrate de que la aplicación funciona normalmente con
   `python main.py` antes de empezar (si hay un error aquí, también lo
   habrá en el empaquetado).

2. Instala las dependencias y PyInstaller (solo la primera vez):
   ```
   pip install -r requirements.txt
   pip install pyinstaller
   ```

3. Desde la carpeta del proyecto (`evafp`), ejecuta:
   ```
   pyinstaller empaquetado.spec
   ```

4. Espera a que termine (puede tardar uno o dos minutos). Al acabar,
   tendrás una carpeta nueva:
   ```
   dist\EVACYL_FP\
   ```
   Dentro está `EVACYL_FP.exe` junto con todo lo que necesita para
   funcionar (incluida la imagen de fondo, el logo, etc. — el archivo
   `.spec` ya se encarga de incluirlos).

5. **Prueba este `.exe` antes de seguir**: haz doble clic en
   `dist\EVACYL_FP\EVACYL_FP.exe` y comprueba que la aplicación arranca
   y funciona igual que con `python main.py` — incluyendo generar un
   informe de alumno en PDF y en Word, que es el punto donde más
   fácilmente se cuela algo al empaquetar (reportlab y python-docx
   cargan ciertas piezas de forma dinámica). Si algo falla aquí, es más
   fácil solucionarlo antes de pasar a la fase 2.

## Fase 2 — Crear el instalador con Inno Setup

1. Descarga e instala Inno Setup (gratuito, el mismo que ya usaste para
   EVACYL si lo tienes instalado no hace falta repetir este paso): busca
   "Inno Setup download" o ve directamente a
   https://jrsoftware.org/isdl.php

2. Abre el archivo `instalador_windows.iss` (que está en la carpeta del
   proyecto `evafp`) con Inno Setup: clic derecho sobre el archivo →
   "Abrir con" → "Inno Setup Compiler".

3. Dentro de Inno Setup, pulsa el botón **"Compile"** (o `Ctrl+F9`).

4. Si todo va bien, se habrá creado una carpeta nueva:
   ```
   instalador_salida\Instalador_EVACYL_FP.exe
   ```

Ese archivo es **el instalador final**. Al ejecutarlo, el docente verá
un asistente de instalación normal de Windows, y al terminar tendrá la
aplicación en su menú de inicio, con icono propio, lista para usar.

## EVACYL y EVACYL FP en el mismo ordenador

Si un docente tiene (o instala) ambas aplicaciones en el mismo
ordenador, no hay ningún conflicto entre ellas:

- Cada una tiene su propio `AppId` en el instalador, así que Windows las
  trata como aplicaciones completamente independientes: instalar,
  actualizar o desinstalar una no afecta a la otra.
- Cada una guarda su configuración (la carpeta de trabajo elegida) en
  una ubicación separada de `%APPDATA%` (`EVACYL` y `EVACYL_FP`
  respectivamente), así que no comparten ni mezclan datos.
- Cada una se instala en su propia carpeta de programa (`EVACYL` y
  `EVACYL FP` dentro de Archivos de programa).

## Si quieres cambiar la versión más adelante

1. Sustituye los archivos del proyecto por los nuevos.
2. Repite la Fase 1 (`pyinstaller empaquetado.spec`).
3. Repite la Fase 2 (abrir el `.iss` y pulsar Compile).

Para que el número de versión se vea distinto en cada entrega, cambia
la línea `#define MiVersion "1.0"` al principio de
`instalador_windows.iss` antes de compilar.

## Solución de problemas habituales

- **"No se encuentra el módulo PySide6" (o reportlab, o docx) al
  ejecutar el .exe generado**: asegúrate de haber instalado las
  dependencias (`pip install -r requirements.txt`) en el mismo entorno
  de Python desde el que ejecutas PyInstaller.
- **El icono no aparece o aparece genérico**: comprueba que el archivo
  `recursos/icono_app.ico` existe en la carpeta del proyecto antes de
  ejecutar `pyinstaller empaquetado.spec`.
- **Falla "no se encuentra recursos/fondo.png" al abrir el .exe
  generado**: significa que el `.spec` no incluyó la carpeta `recursos`
  correctamente; revisa que ejecutas `pyinstaller empaquetado.spec`
  exactamente como se indica (no `pyinstaller main.py` directamente).
- **Error al generar un informe PDF o Word solo en el .exe empaquetado
  (pero funciona bien con `python main.py`)**: probablemente falta
  declarar algún submódulo de reportlab o python-docx en
  `hiddenimports` dentro de `empaquetado.spec`. Anota el mensaje de
  error exacto (suele mencionar el nombre del módulo que falta) y
  añádelo a la lista de `hiddenimports`.
- **Inno Setup da error "no se encuentra dist\EVACYL_FP"**: significa
  que la Fase 1 no se completó correctamente antes de pasar a la
  Fase 2. Repite la Fase 1 y comprueba que la carpeta `dist\...` existe
  y tiene el `.exe` dentro.
