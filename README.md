# Software de Gestión de Tráfico Vehicular con IoT (SGT) — Prototipo SUMO + Pipeline CI/CD

**Institución Universitaria EAM — Facultad de Ingeniería**  
**Asignatura:** Ingeniería de Software III  
**Docente:** Deivid Octavio Riascos Botero  
**Integrantes:**
- Laura Valeria Valencia González (`240220231068`) — Product Owner / Documentación
- Luis Miguel Sepúlveda Quintero (`240220231012`) — Desarrollador / Programador
- Juan Camilo Soto Soto (`240220231028`) — Tester / Analista de Resultados

---

## 1. Descripción del Aplicativo y Stack Tecnológico

El aplicativo **SGT (Software de Gestión de Tráfico Vehicular con Internet de las Cosas)** modela una intersección semaforizada crítica de 4 accesos (Norte, Sur, Este y Oeste, con 2 carriles por sentido y 300 m de longitud) y compara el desempeño de un **semáforo de tiempo fijo** frente a un **controlador adaptativo en Python conectado vía TraCI**, el cual lee detectores inductivos `E1` (sensores IoT simulados) en cada paso de simulación.

### Stack de Tecnologías Empleado
- **Lenguaje de programación:** Python 3.11+
- **Simulación y comunicación IoT/TraCI:** Eclipse SUMO + librería `traci>=1.20.0`
- **Procesamiento y visualización de métricas:** `xml.etree.ElementTree` + `matplotlib>=3.8.0`
- **Framework de pruebas unitarias y mocks:** `pytest>=8.0`, `unittest.mock` (`patch`, `MagicMock`), `pytest-cov>=5.0`
- **Contenerización y CI/CD Pipeline:** Docker (`python:3.11-slim`), GitHub Actions (`.github/workflows/ci.yml`), GitHub Container Registry (`ghcr.io`) y orquestador local (`run_pipeline.py`).

---

## 2. Estructura del Proyecto

```text
traffic_sumo/
├── .github/workflows/
│   └── ci.yml                       # Pipeline CI/CD automatizado en GitHub Actions (3 Jobs, 6 Steps)
├── controller/
│   └── adaptive_controller.py       # Controlador adaptativo: leer_detectores_eje(), decidir_accion(),
│                                    # validar_parametros(), GapOutTracker y PhaseSwitchTracker
├── analysis/
│   └── run_comparison.py            # Análisis: parse_tripinfo(), calcular_mejora(),
│                                    # generar_grafica() e imprimir_resumen()
├── tools/
│   └── validar_config.py            # Validadores XML: validar_red() y validar_demanda()
├── network/
│   ├── nodes.nod.xml                # Nodos: centro semaforizado (C) + 4 extremos (N, S, E, W)
│   ├── edges.edg.xml                # Tramos viales de 2 carriles y 300 m
│   ├── detectors.add.xml            # 8 detectores IoT E1 (4 en eje NS, 4 en eje EW)
│   └── intersection.net.xml         # Red vial compilada con netconvert
├── demand/
│   └── routes.rou.xml               # Flujos vehiculares de hora pico (predominio en eje NS)
├── scenarios/
│   ├── baseline.sumocfg             # Escenario base (semáforo de tiempo fijo)
│   └── adaptive.sumocfg             # Escenario adaptativo (controlado por TraCI)
├── results/
│   ├── baseline_tripinfo.xml        # Resultados de viaje del escenario fijo
│   ├── adaptive_tripinfo.xml        # Resultados de viaje del escenario adaptativo
│   └── comparacion.png              # Gráfica comparativa de espera y pérdida de tiempo
├── tests/
│   ├── unit/                        # 33 Pruebas Unitarias (Formatos PU-01 a PU-04)
│   │   ├── test_sensores.py         # PU-01: 5 casos (CP1 a CP5) — leer_detectores_eje()
│   │   ├── test_decision.py         # PU-02: 11 casos (CP1 a CP11) — decidir_accion() y trackers
│   │   ├── test_analisis.py         # PU-03: 10 casos (CP1 a CP10) — métricas, mejora y gráfica
│   │   └── test_validadores.py      # PU-04: 7 casos (CP1 a CP7) — validar_red() y validar_demanda()
│   └── blackbox/
│       └── test_caja_negra.py       # 4 Pruebas de Caja Negra automatizadas (PCN-01 a PCN-04)
├── docs/                            # Documentación formal del Plan de Pruebas y Guía del Pipeline en PDF
├── Dockerfile                       # Definición de imagen Docker para pruebas y despliegue
├── requirements.txt                 # Dependencias del proyecto y del Pipeline
├── pytest.ini                       # Configuración de pytest (testpaths = tests/unit)
├── run_tests.py                     # Ejecutor directo de las 33 pruebas unitarias
├── run_blackbox_tests.py            # Ejecutor de pruebas de caja negra
├── run_pipeline.py                  # Ejecutor local del Pipeline CI/CD completo (3 Jobs / 6 Steps)
└── COMO_EJECUTAR_LAS_PRUEBAS.md     # Guía detallada de instalación, configuración y evaluación docente
```

---

## 3. Trazabilidad de las 33 Pruebas Unitarias con el Plan de Pruebas (`docs/Plan_de_Pruebas.pdf`)

Todas las pruebas unitarias especificadas en `docs/Plan_de_Pruebas.pdf` están implementadas y pasan al **100 % (`33 passed`)**:

| Formato | Archivo de Prueba | Función / Clase Bajo Prueba | Casos Implementados | Estado |
| :---: | :--- | :--- | :---: | :---: |
| **PU-01** | `tests/unit/test_sensores.py` | `leer_detectores_eje()` con mock de `traci.inductionloop` | `CP1` a `CP5` (**5 casos**) | **5 / 5 PASSED** |
| **PU-02** | `tests/unit/test_decision.py` | `decidir_accion()`, `GapOutTracker`, `PhaseSwitchTracker`, `validar_parametros()` | `CP1` a `CP11` (**11 casos**) | **11 / 11 PASSED** |
| **PU-03** | `tests/unit/test_analisis.py` | `parse_tripinfo()`, `calcular_mejora()`, `generar_grafica()`, `imprimir_resumen()` | `CP1` a `CP10` (**10 casos**) | **10 / 10 PASSED** |
| **PU-04** | `tests/unit/test_validadores.py` | `validar_red()`, `validar_demanda()` | `CP1` a `CP7` (**7 casos**) | **7 / 7 PASSED** |
| **TOTAL** | **`tests/unit/`** | **Suite completa de Pruebas Unitarias** | **33 Casos de Prueba** | **33 / 33 PASSED (100 %)** |

---

## 4. Inicio Rápido: Instalación, Ejecución de Pruebas y Pipeline

> Para la guía completa de instalación, configuración de parámetros del pipeline y la **prueba de evaluación para el docente (modificación intencional de pruebas unitarias para que fallen)**, consulte **[COMO_EJECUTAR_LAS_PRUEBAS.md](./COMO_EJECUTAR_LAS_PRUEBAS.md)** o el PDF **`docs/Guia_Instalacion_Configuracion_y_Evaluacion_Pipeline.pdf`**.

### Paso 1: Instalar dependencias
```bash
cd traffic_sumo
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 2: Ejecutar las 33 Pruebas Unitarias (`PU-01` a `PU-04`)
```bash
pytest tests/unit/ -v
# O con reporte de cobertura:
pytest tests/unit/ -v --cov=controller --cov=analysis --cov=tools --cov-report=term-missing
# O mediante el script resumido:
python run_tests.py
```

### Paso 3: Ejecutar el Pipeline CI/CD Completo Localmente (3 Jobs · 6 Steps)
```bash
python run_pipeline.py
```
Este comando ejecuta en orden los 3 Jobs definidos en `.github/workflows/ci.yml`:
1. **Job 1 (`test`):** Instala/verifica entorno y ejecuta las 33 pruebas unitarias (`PU-01` a `PU-04`) generando `coverage.xml`. Si alguna prueba falla, el pipeline se detiene inmediatamente con código `!= 0`.
2. **Job 2 (`docker`):** Construye la imagen Docker (`traffic-sumo:local`), corre las 33 pruebas dentro del contenedor Linux y ejecuta el Smoke Test.
3. **Job 3 (`deploy`):** Despliega el contenedor en ambiente de ejecución, captura `runtime.log` y verifica la respuesta `SGT listo: EXTENDER True`.
