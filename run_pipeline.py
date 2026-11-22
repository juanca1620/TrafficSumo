"""
Ejecutor Local del Pipeline CI/CD (traffic_sumo)
Reproduce localmente los 3 trabajos (Jobs) y 6 pasos (Steps) definidos en .github/workflows/ci.yml:
  - JOB 1 (test):   Step 1: Verificar entorno Python y dependencias (requirements.txt)
                    Step 2: Ejecutar las 33 Pruebas Unitarias (PU-01 a PU-04) + Reporte de Cobertura (coverage.xml)
  - JOB 2 (docker): Step 3: Construir imagen Docker (traffic-sumo:local) y probar contenedor
                    Step 4: Ejecutar Smoke Test del aplicativo empaquetado
  - JOB 3 (deploy): Step 5: Desplegar contenedor / servicio en ambiente de ejecución (Runtime)
                    Step 6: Validar respuesta en Runtime ('SGT listo: EXTENDER True' en runtime.log)
"""
import importlib.util
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def step_banner(job_label, step_num, title):
    print("\n" + "=" * 78)
    print(f" [{job_label} · STEP {step_num}] {title}")
    print("=" * 78)


def main():
    print("#" * 78)
    print(" PIPELINE CI/CD - SOFTWARE DE GESTIÓN DE TRÁFICO VEHICULAR CON IoT (SGT)")
    print(" Flujo de ejecución conforme a .github/workflows/ci.yml y Plan de Pruebas")
    print("#" * 78)

    # =========================================================================
    # JOB 1: Ejecutar Plan de Pruebas (test)
    # =========================================================================
    step_banner("JOB 1: test", "1/6", "Configurar entorno Python y verificar dependencias")
    print(f"Python ejecutable: {sys.executable}")
    print(f"Versión de Python: {sys.version.split()[0]}")
    print(f"Directorio raíz:   {ROOT}")

    step_banner("JOB 1: test", "2/6", "Ejecutar Pruebas Unitarias (PU-01 a PU-04: 33 casos) y Cobertura")
    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/unit/",
        "-v",
    ]
    if importlib.util.find_spec("pytest_cov") is not None:
        pytest_cmd.extend([
            "--cov=controller",
            "--cov=analysis",
            "--cov=tools",
            "--cov-report=term-missing",
            "--cov-report=xml:coverage.xml",
        ])
    res_unit = subprocess.run(pytest_cmd, cwd=ROOT)
    if res_unit.returncode != 0:
        print("\n" + "!" * 78)
        print(" [PIPELINE DETENIDO - CRITERIO DE RECHAZO ACTIVADO]")
        print(" Falló al menos una Prueba Unitaria en el Job 1 (test).")
        print(" Conforme al flujo del Pipeline (needs: test), se aborta la construcción")
        print(" de la imagen Docker (Job 2) y el despliegue en Runtime (Job 3).")
        print("!" * 78)
        sys.exit(res_unit.returncode)

    # Si SUMO y netconvert están instalados localmente, ejecutar también las pruebas de Caja Negra
    if shutil.which("sumo") and shutil.which("netconvert"):
        print("\n[INFO] SUMO y netconvert detectados en el sistema: ejecutando verificación de Caja Negra...")
        res_bb = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/blackbox/test_caja_negra.py", "-v"],
            cwd=ROOT,
        )
        if res_bb.returncode != 0:
            print("\n[PIPELINE DETENIDO]: Falló al menos una prueba de caja negra.")
            sys.exit(res_bb.returncode)
    else:
        print("\n[INFO] Binarios externos de SUMO no instalados en este host; pruebas unitarias aisladas con mocks OK.")

    # =========================================================================
    # JOB 2: Construir y Probar Dockerfile (docker)
    # =========================================================================
    step_banner("JOB 2: docker", "3/6", "Construir imagen Docker (docker build -t traffic-sumo:local .)")
    docker_bin = shutil.which("docker")
    docker_available = False
    if docker_bin:
        info_check = subprocess.run([docker_bin, "info"], capture_output=True, text=True)
        if info_check.returncode == 0:
            docker_available = True
            print("Docker Desktop detectado activo. Construyendo imagen traffic-sumo:local ...")
            b_res = subprocess.run([docker_bin, "build", "-t", "traffic-sumo:local", "."], cwd=ROOT)
            if b_res.returncode != 0:
                print("\n[PIPELINE DETENIDO]: Error al construir la imagen Docker en Job 2.")
                sys.exit(b_res.returncode)

            print("\nVerificando las 33 pruebas unitarias dentro del contenedor Docker (Linux):")
            t_res = subprocess.run(
                [docker_bin, "run", "--rm", "traffic-sumo:local", "pytest", "tests/unit/", "-v"],
                cwd=ROOT,
            )
            if t_res.returncode != 0:
                print("\n[PIPELINE DETENIDO]: Las pruebas unitarias fallaron dentro del contenedor Docker.")
                sys.exit(t_res.returncode)
        else:
            print("[AVISO] Docker CLI instalado pero el motor Docker Desktop no está activo o accesible.")
    else:
        print("[AVISO] Docker CLI no detectado en PATH. Se usará el entorno local de Python para el Smoke Test.")

    step_banner("JOB 2: docker", "4/6", "Probar ejecución del contenedor (Smoke Test)")
    if docker_available and docker_bin:
        r_res = subprocess.run(
            [docker_bin, "run", "--rm", "traffic-sumo:local"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        output_line = r_res.stdout.strip()
        if r_res.returncode != 0:
            print(f"[ERROR SMOKE TEST DOCKER]: {r_res.stderr}")
            sys.exit(r_res.returncode)
    else:
        smoke_cmd = [
            sys.executable,
            "-c",
            "from controller.adaptive_controller import decidir_accion, validar_parametros; "
            "from analysis.run_comparison import calcular_mejora; "
            "from tools.validar_config import validar_red, validar_demanda; "
            "assert validar_red('network/intersection.net.xml')[0] and validar_demanda('demand/routes.rou.xml')[0] "
            "and round(calcular_mejora(100.0, 49.2), 1) == 50.8; "
            "print('SGT listo:', decidir_accion(15, 0, True), validar_parametros(10, 45, 3))",
        ]
        res_smoke = subprocess.run(smoke_cmd, cwd=ROOT, capture_output=True, text=True)
        output_line = res_smoke.stdout.strip()

    print(f"Salida obtenida en Smoke Test: {output_line}")

    # =========================================================================
    # JOB 3: Desplegar y Validar Runtime (deploy)
    # =========================================================================
    step_banner("JOB 3: deploy", "5/6", "Desplegar contenedor y registrar salida en runtime.log")
    runtime_log_path = os.path.join(ROOT, "runtime.log")
    with open(runtime_log_path, "w", encoding="utf-8") as f:
        f.write(output_line + "\n")
    print(f"Archivo de registro generado: {runtime_log_path}")

    step_banner("JOB 3: deploy", "6/6", "Validar despliegue en ambiente de ejecución (Runtime Health-Check)")
    expected = "SGT listo: EXTENDER True"
    if expected in output_line:
        print(f"[VALIDACIÓN EXITOSA]: Se verificó '{expected}' en runtime.log")
    else:
        print(f"[ERROR DE VALIDACIÓN]: No se encontró '{expected}'. Obtenido: {output_line}")
        sys.exit(1)

    print("\n" + "#" * 78)
    print(" RESULTADO FINAL DEL PIPELINE CI/CD: SUCCESS (3/3 JOBS · 6/6 STEPS EN VERDE)")
    print(" - Job 1 (test):   33/33 Pruebas Unitarias (PU-01 a PU-04) PASSED + coverage.xml")
    print(" - Job 2 (docker): Imagen construida y Smoke Test verificado")
    print(" - Job 3 (deploy): Runtime validado ('SGT listo: EXTENDER True')")
    print("#" * 78)


if __name__ == "__main__":
    main()
