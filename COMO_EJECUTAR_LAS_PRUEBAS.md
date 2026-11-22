# GUÍA DETALLADA DE INSTALACIÓN, CONFIGURACIÓN DEL AMBIENTE, PARÁMETROS DEL PIPELINE Y EVALUACIÓN DOCENTE

**Proyecto:** Software de Gestión de Tráfico Vehicular con Internet de las Cosas (SGT) — Prototipo SUMO + TraCI  
**Institución Universitaria EAM — Facultad de Ingeniería — Ingeniería de Software III**  
**Docente:** Deivid Octavio Riascos Botero  
**Integrantes:**
- Laura Valeria Valencia González (`240220231068`)
- Luis Miguel Sepúlveda Quintero (`240220231012`)
- Juan Camilo Soto Soto (`240220231028`)

---

## 1. Requisitos e Instalación del Ambiente

Para ejecutar las **33 Pruebas Unitarias (`PU-01` a `PU-04`)** y el **Pipeline CI/CD**, las pruebas unitarias están aisladas mediante `unittest.mock` y archivos XML sintéticos (`tmp_path`), por lo que **no requieren tener instalado el simulador SUMO** en la máquina evaluadora.

### 1.1. Software Requerido
1. **Git:** Versión `2.30+` (para clonar el repositorio desde GitHub).
2. **Python:** Versión `3.10`, `3.11`, `3.12` o superior (con `pip` habilitado).
3. **Docker Desktop (Opcional pero recomendado):** Para ejecutar los Jobs 2 y 3 del Pipeline dentro de contenedores Linux (`python:3.11-slim`). Si Docker Desktop no está instalado o activo, `run_pipeline.py` ejecuta automáticamente la validación del Smoke Test y Runtime en el entorno local de Python.
4. **Eclipse SUMO 1.20+ (Opcional):** Únicamente necesario si se desea correr la simulación gráfica `sumo-gui` o las pruebas externas de caja negra (`netconvert`/`sumo`).

### 1.2. Proceso Paso a Paso de Instalación y Configuración del Ambiente

#### Paso 1: Descargar o clonar el repositorio
```bash
git clone <URL_DEL_REPOSITORIO_GITHUB>
cd traffic_sumo_prototipo/traffic_sumo
```
*(Nota: Si el repositorio se clonó directamente sobre la carpeta `traffic_sumo`, basta con `cd traffic_sumo`).*

#### Paso 2: Crear y activar un entorno virtual limpio (Recomendado)
En **Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
En **Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```
En **Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Paso 3: Instalar las dependencias del proyecto
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Esto instalará los paquetes exactos definidos en `requirements.txt`:
- `pytest>=8.0` (motor de ejecución de pruebas unitarias)
- `pytest-cov>=5.0` (cálculo de cobertura de código y exportación a `coverage.xml`)
- `matplotlib>=3.8.0` (generación de la gráfica comparativa `comparacion.png` evaluada en `PU-03 CP9`)
- `traci>=1.20.0` (interfaz Python de comunicación con SUMO sustituida con `unittest.mock` en `PU-01`)

---

## 2. Configuración de los Parámetros del Pipeline CI/CD

El Pipeline está implementado en dos modalidades equivalentes que reflejan exactamente el mismo flujo de 3 trabajos (**Jobs**) y 6 pasos (**Steps**):
1. **En la nube (GitHub Actions):** Archivo [`.github/workflows/ci.yml`](./.github/workflows/ci.yml).
2. **En entorno local (CLI / Docker Desktop):** Script [`run_pipeline.py`](./run_pipeline.py) y [`Dockerfile`](./Dockerfile).

### 2.1. Parámetros Configurables en `.github/workflows/ci.yml`

| Parámetro / Clave | Ubicación en `ci.yml` | Valor Configurado | Descripción y Propósito |
| :--- | :--- | :--- | :--- |
| **Disparadores (`on`)** | Líneas 3–8 | `push`, `pull_request` (todas las ramas `"**"`) y `workflow_dispatch` | Ejecuta el pipeline automáticamente al subir cualquier commit o manualmente desde el botón **"Run workflow"** en GitHub. |
| **Sistema Operativo (`runs-on`)** | Líneas 13, 46, 70 | `ubuntu-latest` | Ambiente Linux limpio aprovisionado por GitHub Actions para cada Job. |
| **Versión de Python (`python-version`)** | Línea 22 | `"3.11"` | Versión de Python utilizada tanto en el runner de GitHub Actions como en la imagen base `python:3.11-slim` del `Dockerfile`. |
| **Parámetros de `pytest` y Cobertura** | Línea 33 | `pytest tests/unit/ -v --cov=controller --cov=analysis --cov=tools --cov-report=term-missing --cov-report=xml:coverage.xml` | Ejecuta las 33 pruebas unitarias (`PU-01` a `PU-04`), mide cobertura sobre los 3 paquetes del aplicativo y exporta el artefacto `coverage.xml`. |
| **Encadenamiento de Jobs (`needs`)** | Líneas 47 y 71 | `needs: test` (en Job 2) y `needs: docker` (en Job 3) | **Bloqueo de seguridad (Quality Gate):** Si al menos 1 de las 33 pruebas unitarias falla en el Job 1 (`test`), el Job 2 (`docker`) y el Job 3 (`deploy`) se cancelan automáticamente. |
| **Permisos de Registro (`permissions`)** | Líneas 73–75 | `contents: read`, `packages: write` | Autoriza al `GITHUB_TOKEN` automático del repositorio a publicar la imagen Docker en `ghcr.io/<usuario>/traffic-sumo:latest`. |
| **Validación de Runtime (Health-Check)** | Línea 111 | `grep -q "SGT listo: EXTENDER True" runtime.log` | Verifica que el contenedor desplegado importe los módulos y responda con la decisión esperada antes de aprobar el despliegue. |

### 2.2. Parámetros Configurables en `pytest.ini` y `Dockerfile`
- **`pytest.ini`:**
  ```ini
  [pytest]
  testpaths = tests/unit
  pythonpath = .
  addopts = -v
  ```
  Permite que al ejecutar simplemente `pytest` en la raíz de `traffic_sumo/`, se descubran y ejecuten de forma automática las 33 pruebas unitarias de `tests/unit/` en modo detallado (`-v`).
- **`Dockerfile`:**
  Empaqueta el código fuente (`controller/`, `analysis/`, `tools/`, `network/`, `demand/`, `scenarios/`) y la suite `tests/` sobre `python:3.11-slim`, definiendo como `CMD` el comando de validación de estado (`SGT listo: EXTENDER True`).

---

## 3. Ejecución Normal del Pipeline (100 % Exitoso — 33/33 Pruebas Unitarias PASSED)

Ubicado en la carpeta `traffic_sumo/`:

### Opción A: Ejecutar el Pipeline CI/CD Completo Localmente
```bash
python run_pipeline.py
```
**Flujo que observará en consola:**
1. **`[JOB 1: test · STEP 1/6]`:** Verifica la versión de Python y rutas del entorno.
2. **`[JOB 1: test · STEP 2/6]`:** Ejecuta `pytest tests/unit/ -v --cov=controller --cov=analysis --cov=tools`. Las **33 pruebas unitarias (`PU-01` a `PU-04`)** pasan en verde (`33 passed`) y se genera `coverage.xml`.
3. **`[JOB 2: docker · STEP 3/6]`:** Construye la imagen `traffic-sumo:local` con Docker Desktop y ejecuta las 33 pruebas unitarias dentro del contenedor Linux.
4. **`[JOB 2: docker · STEP 4/6]`:** Ejecuta el Smoke Test del contenedor (`SGT listo: EXTENDER True`).
5. **`[JOB 3: deploy · STEP 5/6]`:** Despliega la ejecución y guarda la salida en `runtime.log`.
6. **`[JOB 3: deploy · STEP 6/6]`:** Verifica la cadena `"SGT listo: EXTENDER True"` en `runtime.log` y finaliza con:
   `RESULTADO FINAL DEL PIPELINE CI/CD: SUCCESS (3/3 JOBS · 6/6 STEPS EN VERDE)`.

### Opción B: Ejecutar únicamente las 33 Pruebas Unitarias
```bash
pytest tests/unit/ -v
```
*(O bien `python run_tests.py`).*

### Opción C: Ejecutar manualmente los pasos con Docker Desktop
```bash
docker build -t traffic-sumo:local .
docker run --rm traffic-sumo:local pytest tests/unit/ -v
docker run --rm traffic-sumo:local
```

---

## 4. Guía para la Evaluación del Docente: Modificación Intencional de Pruebas Unitarias para Provocar el Fallo del Pipeline

Conforme a lo indicado en la guía de la actividad:
> *"Para la evaluación el docente descargará el proyecto del repositorio y siguiendo los pasos de la guía entregada, procederá a ejecutar el pipeline e intencionalmente realizará modificaciones en las Pruebas Unitarias para que estas fallen durante la ejecución."*

A continuación se presentan **4 pruebas de fallo intencional** (una por cada formato `PU-01`, `PU-02`, `PU-03` y `PU-04`) que el docente puede aplicar para comprobar cómo el Pipeline detecta inmediatamente la falla, reporta la línea exacta del error y **bloquea los Jobs siguientes (`docker` y `deploy`)**.

---

### Caso de Fallo Intencional 1 — Módulo `PU-01` (Sensores IoT: `tests/unit/test_sensores.py`)

1. Abra el archivo [`tests/unit/test_sensores.py`](./tests/unit/test_sensores.py).
2. Ubique la prueba `test_pu01_cp1_vehiculos_ambos_ejes` (línea 53):
   ```python
   # Valor original correcto (3 + 2 = 5 en NS; 1 + 0 = 1 en EW):
   assert resultado == {"NS": 5, "EW": 1}, f"Se esperaba {{'NS': 5, 'EW': 1}}, obtenido {resultado}"
   ```
3. **Modifíquelo intencionalmente** cambiando `"NS": 5` por `"NS": 99`:
   ```python
   assert resultado == {"NS": 99, "EW": 1}, f"Se esperaba {{'NS': 99, 'EW': 1}}, obtenido {resultado}"
   ```
4. Ejecute el Pipeline:
   ```bash
   python run_pipeline.py
   ```
   *(O si lo sube a GitHub con `git commit -am "Prueba fallo PU-01" && git push`, obsérvelo en la pestaña **Actions**).*
5. **Resultado esperado durante el fallo:**
   - `pytest` marca `FAILED tests/unit/test_sensores.py::test_pu01_cp1_vehiculos_ambos_ejes` (`1 failed, 32 passed`).
   - El Pipeline imprime:
     `[PIPELINE DETENIDO - CRITERIO DE RECHAZO ACTIVADO]` y **NO construye la imagen Docker (Job 2) ni ejecuta el despliegue (Job 3)**.
6. **Restaurar:** Vuelva a colocar `"NS": 5` y ejecute `python run_pipeline.py` para verificar que vuelve a `33 passed`.

---

### Caso de Fallo Intencional 2 — Módulo `PU-02` (Decisión Semafórica: `tests/unit/test_decision.py`)

1. Abra el archivo [`tests/unit/test_decision.py`](./tests/unit/test_decision.py).
2. Ubique la prueba `test_pu02_cp1_limite_inferior_no_cortar_antes_minimo` (líneas 34–35):
   ```python
   # Original: Con t_verde=9s (< 10s mínimo), el semáforo NUNCA debe cortar el verde:
   accion = decidir_accion(t_verde=9, seg_sin_deteccion=5, hay_demanda_opuesta=True)
   assert accion == "EXTENDER"
   ```
3. **Modifíquelo intencionalmente** cambiando `"EXTENDER"` por `"CAMBIAR"`:
   ```python
   assert accion == "CAMBIAR"
   ```
4. Ejecute el Pipeline:
   ```bash
   python run_pipeline.py
   ```
5. **Resultado esperado:** El Job 1 falla con `AssertionError: assert 'EXTENDER' == 'CAMBIAR'` y detiene el Pipeline en el Paso 2/6.
6. **Restaurar:** Vuelva a colocar `assert accion == "EXTENDER"`.

---

### Caso de Fallo Intencional 3 — Módulo `PU-03` (Análisis de Resultados: `tests/unit/test_analisis.py`)

1. Abra el archivo [`tests/unit/test_analisis.py`](./tests/unit/test_analisis.py).
2. Ubique la prueba `test_pu03_cp5_porcentaje_mejora_espera` (líneas 86–87):
   ```python
   # Original: De 100.0 s a 49.2 s la mejora es del 50.8 %
   mejora = calcular_mejora(base=100.0, adaptativo=49.2)
   assert mejora == pytest.approx(50.8, 0.1)
   ```
3. **Modifíquelo intencionalmente** cambiando `50.8` por `80.0`:
   ```python
   assert mejora == pytest.approx(80.0, 0.1)
   ```
4. Ejecute `python run_pipeline.py` y verifique que el Pipeline se detiene reportando `1 failed, 32 passed`. Luego restaure `50.8`.

---

### Caso de Fallo Intencional 4 — Módulo `PU-04` (Validadores de Configuración: `tests/unit/test_validadores.py`)

1. Abra el archivo [`tests/unit/test_validadores.py`](./tests/unit/test_validadores.py).
2. Ubique la prueba `test_pu04_cp2_limite_acceso_con_un_carril` (líneas 71–72):
   ```python
   # Original: Una red con un acceso de solo 1 carril debe ser rechazada (es_valido is False)
   es_valido, mensaje = validar_red(str(net_file))
   assert es_valido is False
   ```
3. **Modifíquelo intencionalmente** cambiando `False` por `True`:
   ```python
   assert es_valido is True
   ```
4. Ejecute `python run_pipeline.py`, observe la detención automática del Pipeline por fallo en `PU-04 CP2`, y restaure `assert es_valido is False`.
