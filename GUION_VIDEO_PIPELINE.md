# GUION PASO A PASO PARA EL VIDEO EXPLICATIVO Y SUBIDA A GITHUB

Este documento contiene:
1. **Los comandos exactos para subir el proyecto a un repositorio público de GitHub** (y activar GitHub Actions automáticamente).
2. **El guion minuto a minuto para grabar el video explicativo** exigido en la entrega (*"Al finalizar la ejecución de las pruebas Unitarias... Los estudiantes deberán proveer un video explicativo mostrando la ejecución del Pipeline"*).

---

## PARTE 1: Cómo subir el proyecto a un repositorio público de GitHub

1. Ingresa a [https://github.com/new](https://github.com/new) desde tu navegador.
2. En **Repository name**, escribe: `traffic-sumo-sgt` (o el nombre que prefieras).
3. Selecciona visibilidad **Public** (Público — requisito obligatorio del enunciado).
4. **No** marques "Add a README file" ni ".gitignore" (ya están creados en el proyecto). Haz clic en **Create repository**.
5. Abre una terminal PowerShell en la carpeta del proyecto y ejecuta:

```powershell
cd "d:\U\8VOSEMESTRE\Ing 3\traffic_sumo_prototipo\traffic_sumo"
git init
git branch -M main
git add .
git commit -m "Implementacion SGT SUMO, 33 pruebas unitarias (PU-01 a PU-04) y Pipeline CI/CD"
git remote add origin https://github.com/<TU_USUARIO>/traffic-sumo-sgt.git
git push -u origin main
```

6. Apenas termine el `git push`, entra a la pestaña **Actions** de tu repositorio en GitHub (`https://github.com/<TU_USUARIO>/traffic-sumo-sgt/actions`) y verás el workflow **"CI Pipeline - SGT Traffic SUMO"** ejecutando los 3 Jobs en vivo:
   - **Job 1:** `Ejecutar Plan de Pruebas` (33 pruebas unitarias `PU-01` a `PU-04` + artefacto `coverage-report`).
   - **Job 2:** `Construir y Probar Dockerfile` (imagen Docker + 33 pruebas dentro del contenedor + Smoke Test).
   - **Job 3:** `Desplegar en GHCR y Validar Runtime` (publicación en `ghcr.io` y validación de `SGT listo: EXTENDER True`).

---

## PARTE 2: Guion para Grabar el Video Explicativo (Duración sugerida: 4 a 6 minutos)

### Minuto 0:00 – 0:45 | Presentación del Equipo, Aplicativo y Plan de Pruebas
- **Qué mostrar en pantalla:**
  - El documento `docs/Plan_de_Pruebas (1) (2).pdf` (o `docs/Plan_de_Pruebas_Unitarias.pdf` y `docs/Plan_de_Pruebas_Pipeline.pdf`) y el repositorio en VS Code.
- **Qué explicar:**
  - *"Buenas tardes profesor Deivid, somos Laura Valeria Valencia, Luis Miguel Sepúlveda y Juan Camilo Soto. Presentamos la implementación del aplicativo SGT (Software de Gestión de Tráfico Vehicular con IoT en SUMO y Python/TraCI) junto con la ejecución de las 33 Pruebas Unitarias definidas en el Plan de Pruebas y su Pipeline CI/CD automatizado."*
  - Mostrar brevemente los 3 módulos del aplicativo:
    1. `controller/adaptive_controller.py` (`leer_detectores_eje`, `decidir_accion`, `validar_parametros`, `GapOutTracker`, `PhaseSwitchTracker`).
    2. `analysis/run_comparison.py` (`parse_tripinfo`, `calcular_mejora`, `generar_grafica`, `imprimir_resumen`).
    3. `tools/validar_config.py` (`validar_red`, `validar_demanda`).

### Minuto 0:45 – 1:45 | Explicación de las 33 Pruebas Unitarias (`PU-01` a `PU-04`)
- **Qué mostrar en pantalla:**
  - Abrir la carpeta `tests/unit/` y mostrar los 4 archivos que corresponden exactamente a los 4 formatos del Plan de Pruebas:
    - `test_sensores.py` (`PU-01`: 5 casos `CP1` a `CP5` con `unittest.mock` aislando TraCI).
    - `test_decision.py` (`PU-02`: 11 casos `CP1` a `CP11` evaluando verde mínimo 10s, máximo 45s, gap-out 3s y validación de parámetros).
    - `test_analisis.py` (`PU-03`: 10 casos `CP1` a `CP10` evaluando lectura de XML, porcentaje de mejora 50.8% y 37.1%, división por cero y generación de `comparacion.png`).
    - `test_validadores.py` (`PU-04`: 7 casos `CP1` a `CP7` validando los 4 accesos de 2 carriles y predominio de demanda Norte-Sur).

### Minuto 1:45 – 3:00 | Explicación del Archivo del Pipeline (`.github/workflows/ci.yml` y `Dockerfile`)
- **Qué mostrar en pantalla:**
  - Abrir `.github/workflows/ci.yml` y `Dockerfile`.
- **Qué explicar:**
  - Explicar que el Pipeline sigue exactamente el flujo de 3 Jobs encadenados mediante `needs`:
    - **Job 1 (`test`):** Descarga el código, instala Python 3.11 y `requirements.txt`, ejecuta las 33 pruebas unitarias con `pytest` y genera el reporte de cobertura `coverage.xml`.
    - **Job 2 (`docker`):** Solo se ejecuta si el Job 1 pasa al 100% (`needs: test`). Construye la imagen Docker, ejecuta las 33 pruebas dentro del contenedor y corre el Smoke Test.
    - **Job 3 (`deploy`):** Solo se ejecuta si el Job 2 pasa (`needs: docker`). Publica la imagen en GitHub Container Registry (`ghcr.io`), despliega el contenedor en Runtime y verifica con `grep` que responda `"SGT listo: EXTENDER True"`.

### Minuto 3:00 – 4:15 | Demostración en Vivo 1: Ejecución Exitosa del Pipeline (`33 passed`)
- **Qué hacer en la terminal de VS Code:**
  Ejecutar el pipeline completo:
  ```powershell
  python run_pipeline.py
  ```
- **Qué destacar mientras corre:**
  - Mostrar cómo en el **Job 1** se ejecutan los 33 casos de prueba (`33 passed`) con su tabla de cobertura.
  - Mostrar cómo en el **Job 2** Docker Desktop construye la imagen `traffic-sumo:local`, corre las 33 pruebas dentro del contenedor Linux y valida el Smoke Test.
  - Mostrar cómo en el **Job 3** se genera `runtime.log` y el pipeline termina con `RESULTADO FINAL DEL PIPELINE CI/CD: SUCCESS (3/3 JOBS · 6/6 STEPS EN VERDE)`.
  - Mostrar también la pestaña **Actions** en GitHub con los 3 chulos verdes (`test` -> `docker` -> `deploy`).

### Minuto 4:15 – 5:30 | Demostración en Vivo 2: Fallo Intencional de una Prueba Unitaria Deteniendo el Pipeline
- **Qué hacer en VS Code:**
  1. Abrir `tests/unit/test_sensores.py` en la línea 53 (`test_pu01_cp1_vehiculos_ambos_ejes`).
  2. Cambiar `assert resultado == {"NS": 5, "EW": 1}` por `assert resultado == {"NS": 99, "EW": 1}` y guardar (`Ctrl + S`).
  3. Ejecutar nuevamente en la terminal:
     ```powershell
     python run_pipeline.py
     ```
  4. **Mostrar cómo el Pipeline falla en el Job 1 (`1 failed, 32 passed`)** e imprime:
     `[PIPELINE DETENIDO - CRITERIO DE RECHAZO ACTIVADO]`, abortando la construcción de Docker y el despliegue.
  5. Revertir el cambio a `"NS": 5`, guardar y volver a correr `python run_pipeline.py` para dejar el proyecto en verde (`33 passed`).
