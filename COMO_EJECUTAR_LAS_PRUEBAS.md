# GUÍA DETALLADA DE INSTALACIÓN, CONFIGURACIÓN DEL AMBIENTE, PARÁMETROS DEL PIPELINE Y EVALUACIÓN DOCENTE

**Proyecto:** Software de Gestión de Tráfico Vehicular con Internet de las Cosas (SGT) — Prototipo SUMO + TraCI  
**Repositorio Oficial en GitHub:** https://github.com/juanca1620/TrafficSumo  
**Institución Universitaria EAM — Facultad de Ingeniería — Ingeniería de Software III**  
**Docente:** Deivid Octavio Riascos Botero  
**Integrantes:**
- Laura Valeria Valencia González (`240220231068`) — Product Owner / Documentación
- Luis Miguel Sepúlveda Quintero (`240220231012`) — Desarrollador / Programador
- Juan Camilo Soto Soto (`240220231028`) — Tester / Analista de Resultados

---

## 1. Requisitos e Instalación del Ambiente

Las **33 Pruebas Unitarias (`PU-01` a `PU-04`)** del proyecto están aisladas mediante `unittest.mock` y archivos XML sintéticos generados en directorios temporales (`tmp_path`), por lo que el docente puede descargar el proyecto y ejecutar la totalidad de las pruebas unitarias y el Pipeline CI/CD sin necesidad de instalar el simulador Eclipse SUMO.

### 1.1. Software Requerido en la Máquina Evaluadora
1. **Git:** Versión `2.30` o superior.
2. **Python:** Versión `3.10`, `3.11`, `3.12` o superior (con `pip` incluido).
3. **Docker Desktop:** Requerido únicamente si se desea construir y ejecutar el contenedor Linux local (`traffic-sumo:local`) en los Jobs 2 y 3. Si Docker Desktop no está abierto, `run_pipeline.py` ejecuta automáticamente el Smoke Test y la validación de Runtime sobre el intérprete local de Python.

---

### 1.2. Proceso Paso a Paso de Instalación y Configuración del Ambiente

Ejecute los siguientes comandos en orden dentro de su terminal:

#### Paso 1: Clonar el repositorio oficial desde GitHub e ingresar al directorio del proyecto
```bash
git clone https://github.com/juanca1620/TrafficSumo.git
cd TrafficSumo
```

#### Paso 2: Crear y activar el entorno virtual de Python
- **En Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **En Windows (CMD):**
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```
- **En Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

#### Paso 3: Actualizar `pip` e instalar las dependencias desde `requirements.txt`
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Este comando instala las 4 dependencias exactas declaradas en [`requirements.txt`](./requirements.txt):
- `pytest>=8.0` — Framework de ejecución de las 33 pruebas unitarias.
- `pytest-cov>=5.0` — Motor de cobertura de código y generación del reporte `coverage.xml`.
- `matplotlib>=3.8.0` — Librería de generación de la gráfica comparativa `results/comparacion.png` (`PU-03 CP9`).
- `traci>=1.20.0` — Librería cliente de comunicación con SUMO reemplazada mediante `unittest.mock.patch` en `PU-01`.

---

## 2. Configuración de los Parámetros del Pipeline CI/CD

El Pipeline CI/CD se encuentra configurado en el archivo [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) para ejecución en **GitHub Actions** y cuenta con su espejo exacto en el script [`run_pipeline.py`](./run_pipeline.py) para ejecución en la máquina local del docente.

### 2.1. Tabla Detallada de Parámetros en `.github/workflows/ci.yml`

| Parámetro / Clave | Ubicación en `.github/workflows/ci.yml` | Valor Exacto Configurado | Función dentro del Pipeline |
| :--- | :--- | :--- | :--- |
| **`name`** | Línea 1 | `CI Pipeline - SGT Traffic SUMO` | Identificador del flujo de trabajo en la pestaña **Actions** de GitHub. |
| **`on` (Disparadores)** | Líneas 3–8 | `push: branches: [ "**" ]`, `pull_request: branches: [ "**" ]`, `workflow_dispatch:` | Dispara el pipeline automáticamente ante cualquier `push` o `pull_request` en cualquier rama, o manualmente mediante el botón **Run workflow**. |
| **`runs-on`** | Líneas 13, 44, 64 | `ubuntu-latest` | Máquina virtual Linux aprovisionada en limpio para cada uno de los 3 Jobs (`test`, `docker`, `deploy`). |
| **`python-version` y `cache`** | Líneas 20–23 | `python-version: "3.11"`, `cache: "pip"` | Configura Python 3.11 mediante `actions/setup-python@v5` y almacena en caché los paquetes de `pip`. |
| **Comando de Pruebas Unitarias y Cobertura (Job 1 `test`)** | Línea 32 | `pytest tests/unit/ -v --cov=controller --cov=analysis --cov=tools --cov-report=term-missing --cov-report=xml:coverage.xml` | Ejecuta las 33 pruebas unitarias (`PU-01` a `PU-04`), muestra en consola las líneas cubiertas de los 3 módulos del aplicativo y genera `coverage.xml`. |
| **Artefacto de Cobertura** | Líneas 34–40 | `name: coverage-report`, `path: coverage.xml` | Sube el reporte XML de cobertura con `actions/upload-artifact@v4` (`if: always()`). |
| **Bloqueo entre Jobs (`needs`)** | Líneas 45 y 65 | `needs: test` (en Job `docker`) y `needs: docker` (en Job `deploy`) | **Quality Gate:** Si al menos 1 de las 33 pruebas unitarias falla en el Job 1 (`test`), GitHub Actions cancela automáticamente la construcción de Docker (Job 2) y el despliegue (Job 3). |
| **Construcción y Smoke Test de Contenedor (Job 2 `docker`)** | Líneas 56 y 60 | `docker build -t traffic-sumo:${{ github.sha }} .` y `docker run --rm traffic-sumo:${{ github.sha }}` | Construye la imagen Docker con el commit actual y verifica que el contenedor inicie y valide los módulos sin errores. |
| **Condición y Permisos de Despliegue (Job 3 `deploy`)** | Líneas 66–69 | `if: github.ref == 'refs/heads/main'`, `contents: read`, `packages: write` | Autoriza al `GITHUB_TOKEN` a publicar paquetes en GitHub Container Registry (`ghcr.io`) desde la rama `main`. |
| **Imágenes Publicadas en GHCR** | Líneas 96–97 | `ghcr.io/juanca1620/traffic-sumo:latest` y `ghcr.io/juanca1620/traffic-sumo:${{ github.sha }}` | Etiquetas publicadas en el registro de contenedores mediante `docker/build-push-action@v6`. |
| **Validación en Runtime (Health-Check)** | Líneas 101–106 | `docker run --rm ghcr.io/juanca1620/traffic-sumo:latest \| tee runtime.log` y `grep -q "SGT listo: EXTENDER True" runtime.log` | Descarga la imagen publicada, captura su salida estándar en `runtime.log` y comprueba la respuesta exacta `"SGT listo: EXTENDER True"`. |

---

### 2.2. Parámetros Configurados en `pytest.ini` y `Dockerfile`

1. **Archivo [`pytest.ini`](./pytest.ini):**
   ```ini
   [pytest]
   testpaths = tests/unit
   pythonpath = .
   addopts = -v
   ```
   - `testpaths = tests/unit`: Define la ruta por defecto donde `pytest` descubre los 4 archivos de pruebas unitarias (`test_sensores.py`, `test_decision.py`, `test_analisis.py`, `test_validadores.py`).
   - `pythonpath = .`: Garantiza que los paquetes `controller`, `analysis` y `tools` se importen directamente desde la raíz del proyecto.
   - `addopts = -v`: Activa la salida detallada con el nombre e indicador `PASSED` / `FAILED` de cada uno de los 33 casos de prueba.

2. **Archivo [`Dockerfile`](./Dockerfile):**
   - Imagen base: `FROM python:3.11-slim`.
   - Directorio de trabajo: `WORKDIR /app`.
   - Instala `requirements.txt` y copia las carpetas `controller/`, `analysis/`, `tools/`, `network/`, `demand/`, `scenarios/` y `tests/`.
   - Comando de inicio (`CMD`): Verifica la red vial (`validar_red`), la demanda vehicular (`validar_demanda`), el cálculo de mejora (`calcular_mejora`), la decisión semafórica (`decidir_accion(15, 0, True)`) y la validación de parámetros (`validar_parametros(10, 45, 3)`), imprimiendo `SGT listo: EXTENDER True`.

---

## 3. Ejecución Normal del Pipeline (Estado Exitoso: 33/33 Pruebas Unitarias PASSED)

Ubicado en la raíz del repositorio clonado (`TrafficSumo/`), puede ejecutar el Pipeline y las pruebas mediante cualquiera de los siguientes comandos:

### 3.1. Ejecutar el Pipeline CI/CD Completo Localmente (3 Jobs · 6 Steps)
```bash
python run_pipeline.py
```
**Resultado obtenido en consola:**
- **`[JOB 1: test · STEP 1/6]`:** Verifica el ejecutable de Python y el directorio raíz.
- **`[JOB 1: test · STEP 2/6]`:** Ejecuta las **33 Pruebas Unitarias (`PU-01` a `PU-04`)** con resultado **`33 passed`** y genera el archivo `coverage.xml`.
- **`[JOB 2: docker · STEP 3/6]`:** Construye la imagen `traffic-sumo:local` y ejecuta las 33 pruebas unitarias dentro del contenedor.
- **`[JOB 2: docker · STEP 4/6]`:** Ejecuta el Smoke Test obteniendo `Salida obtenida en Smoke Test: SGT listo: EXTENDER True`.
- **`[JOB 3: deploy · STEP 5/6]`:** Despliega la ejecución y escribe el archivo `runtime.log`.
- **`[JOB 3: deploy · STEP 6/6]`:** Verifica la existencia de `"SGT listo: EXTENDER True"` en `runtime.log` e imprime:
  `RESULTADO FINAL DEL PIPELINE CI/CD: SUCCESS (3/3 JOBS · 6/6 STEPS EN VERDE)`.

### 3.2. Ejecutar Únicamente la Suite de 33 Pruebas Unitarias
```bash
pytest tests/unit/ -v
```
O mediante el script con resumen de calidad:
```bash
python run_tests.py
```

### 3.3. Ejecutar las Pruebas Unitarias y el Smoke Test con Docker Desktop
```bash
docker build -t traffic-sumo:local .
docker run --rm traffic-sumo:local pytest tests/unit/ -v
docker run --rm traffic-sumo:local
```

---

## 4. Guía Paso a Paso para la Evaluación del Docente: Modificación Intencional de Pruebas Unitarias para Provocar el Fallo del Pipeline

Para verificar el cumplimiento del criterio de rechazo del Plan de Pruebas (*"al menos un caso falla porque el resultado obtenido difiere del esperado"*) y comprobar cómo el Pipeline detiene la ejecución, el docente puede realizar cualquiera de las siguientes **4 modificaciones intencionales** (una por cada formato `PU-01`, `PU-02`, `PU-03` y `PU-04`):

---

### Prueba de Fallo Intencional 1 — Formato `PU-01` (`tests/unit/test_sensores.py`)

1. **Archivo a editar:** [`tests/unit/test_sensores.py`](./tests/unit/test_sensores.py)
2. **Función y línea exacta:** `test_pu01_cp1_vehiculos_ambos_ejes` (**Línea 53**).
3. **Código original (Pasa):**
   ```python
   assert resultado == {"NS": 5, "EW": 1}, f"Se esperaba {{'NS': 5, 'EW': 1}}, obtenido {resultado}"
   ```
4. **Modificación intencional para provocar el fallo (cambiar `5` por `99`):**
   ```python
   assert resultado == {"NS": 99, "EW": 1}, f"Se esperaba {{'NS': 99, 'EW': 1}}, obtenido {resultado}"
   ```
5. **Comando a ejecutar para probar el fallo en el Pipeline:**
   ```bash
   python run_pipeline.py
   ```
6. **Resultado exacto que observará en consola:**
   - `pytest` reporta:
     `FAILED tests/unit/test_sensores.py::test_pu01_cp1_vehiculos_ambos_ejes`
     `AssertionError: Se esperaba {'NS': 99, 'EW': 1}, obtenido {'NS': 5, 'EW': 1}`
     `========================= 1 failed, 32 passed =========================`
   - El Pipeline se detiene inmediatamente en el **Job 1 (`STEP 2/6`)** con código de salida `1`, mostrando:
     `[PIPELINE DETENIDO - CRITERIO DE RECHAZO ACTIVADO]` y **abortando el Job 2 (`docker`) y el Job 3 (`deploy`)**.
7. **Restauración a estado exitoso:**
   Regrese la **Línea 53** de `tests/unit/test_sensores.py` a:
   ```python
   assert resultado == {"NS": 5, "EW": 1}, f"Se esperaba {{'NS': 5, 'EW': 1}}, obtenido {resultado}"
   ```
   y ejecute `python run_pipeline.py` para confirmar que las 33 pruebas vuelven a pasar (`33 passed`).

---

### Prueba de Fallo Intencional 2 — Formato `PU-02` (`tests/unit/test_decision.py`)

1. **Archivo a editar:** [`tests/unit/test_decision.py`](./tests/unit/test_decision.py)
2. **Función y línea exacta:** `test_pu02_cp1_limite_inferior_no_cortar_antes_minimo` (**Línea 35**).
3. **Código original (Pasa):**
   ```python
   accion = decidir_accion(t_verde=9, seg_sin_deteccion=5, hay_demanda_opuesta=True)
   assert accion == "EXTENDER"
   ```
4. **Modificación intencional para provocar el fallo (cambiar `"EXTENDER"` por `"CAMBIAR"`):**
   ```python
   accion = decidir_accion(t_verde=9, seg_sin_deteccion=5, hay_demanda_opuesta=True)
   assert accion == "CAMBIAR"
   ```
5. **Comando a ejecutar para probar el fallo en el Pipeline:**
   ```bash
   python run_pipeline.py
   ```
6. **Resultado exacto que observará en consola:**
   - `pytest` reporta:
     `FAILED tests/unit/test_decision.py::test_pu02_cp1_limite_inferior_no_cortar_antes_minimo`
     `AssertionError: assert 'EXTENDER' == 'CAMBIAR'`
     `========================= 1 failed, 32 passed =========================`
   - El Pipeline aborta en el **Job 1 (`STEP 2/6`)** sin ejecutar Docker ni Deploy.
7. **Restauración a estado exitoso:**
   Regrese la **Línea 35** de `tests/unit/test_decision.py` a:
   ```python
   assert accion == "EXTENDER"
   ```

---

### Prueba de Fallo Intencional 3 — Formato `PU-03` (`tests/unit/test_analisis.py`)

1. **Archivo a editar:** [`tests/unit/test_analisis.py`](./tests/unit/test_analisis.py)
2. **Función y línea exacta:** `test_pu03_cp5_porcentaje_mejora_espera` (**Línea 92**).
3. **Código original (Pasa):**
   ```python
   mejora = calcular_mejora(base=100.0, adaptativo=49.2)
   assert mejora == pytest.approx(50.8, 0.1)
   ```
4. **Modificación intencional para provocar el fallo (cambiar `50.8` por `80.0`):**
   ```python
   mejora = calcular_mejora(base=100.0, adaptativo=49.2)
   assert mejora == pytest.approx(80.0, 0.1)
   ```
5. **Comando a ejecutar para probar el fallo en el Pipeline:**
   ```bash
   python run_pipeline.py
   ```
6. **Resultado exacto que observará en consola:**
   - `pytest` reporta:
     `FAILED tests/unit/test_analisis.py::test_pu03_cp5_porcentaje_mejora_espera`
     `AssertionError: assert 50.8 == 80.0 ± 8.0e+00`
     `========================= 1 failed, 32 passed =========================`
   - El Pipeline aborta en el **Job 1 (`STEP 2/6`)** sin ejecutar Docker ni Deploy.
7. **Restauración a estado exitoso:**
   Regrese la **Línea 92** de `tests/unit/test_analisis.py` a:
   ```python
   assert mejora == pytest.approx(50.8, 0.1)
   ```

---

### Prueba de Fallo Intencional 4 — Formato `PU-04` (`tests/unit/test_validadores.py`)

1. **Archivo a editar:** [`tests/unit/test_validadores.py`](./tests/unit/test_validadores.py)
2. **Función y línea exacta:** `test_pu04_cp2_limite_acceso_con_un_carril` (**Línea 72**).
3. **Código original (Pasa):**
   ```python
   es_valido, mensaje = validar_red(str(net_file))
   assert es_valido is False
   ```
4. **Modificación intencional para provocar el fallo (cambiar `False` por `True`):**
   ```python
   es_valido, mensaje = validar_red(str(net_file))
   assert es_valido is True
   ```
5. **Comando a ejecutar para probar el fallo en el Pipeline:**
   ```bash
   python run_pipeline.py
   ```
6. **Resultado exacto que observará en consola:**
   - `pytest` reporta:
     `FAILED tests/unit/test_validadores.py::test_pu04_cp2_limite_acceso_con_un_carril`
     `AssertionError: assert False is True`
     `========================= 1 failed, 32 passed =========================`
   - El Pipeline aborta en el **Job 1 (`STEP 2/6`)** sin ejecutar Docker ni Deploy.
7. **Restauración a estado exitoso:**
   Regrese la **Línea 72** de `tests/unit/test_validadores.py` a:
   ```python
   assert es_valido is False
   ```
