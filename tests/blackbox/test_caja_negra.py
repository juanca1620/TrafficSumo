"""
Módulo de Pruebas de Caja Negra (Black-Box Testing)
Evalúa el comportamiento del sistema desde la interfaz externa (CLI, binarios de SUMO, netconvert y archivos generados),
sin inspeccionar el código interno ni utilizar mocks.
Alineado con los formatos PCN-01, PCN-02 y PCN-04 de Plan_de_Pruebas.pdf.
"""
import os
import shutil
import subprocess
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NET_DIR = os.path.join(ROOT, "network")
SCENARIOS_DIR = os.path.join(ROOT, "scenarios")
RESULTS_DIR = os.path.join(ROOT, "results")


@pytest.mark.skipif(shutil.which("netconvert") is None, reason="netconvert (SUMO) no está instalado en el PATH")
def test_pcn01_cn01_compilacion_red_netconvert():
    """
    PCN-01 / CN-01 - Válido: Compilar la red vial con netconvert.
    Entrada: nodes.nod.xml + edges.edg.xml (intersección 4 accesos, 2 carriles).
    Salida esperada: netconvert termina sin errores (código 0) y genera intersection.net.xml.
    """
    nodes_file = os.path.join(NET_DIR, "nodes.nod.xml")
    edges_file = os.path.join(NET_DIR, "edges.edg.xml")
    out_net = os.path.join(NET_DIR, "intersection.net.xml")

    cmd = [
        "netconvert",
        "--node-files", nodes_file,
        "--edge-files", edges_file,
        "--output-file", out_net,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"netconvert falló con código {res.returncode}: {res.stderr}"
    assert os.path.exists(out_net), "No se generó el archivo de red intersection.net.xml"
    assert os.path.getsize(out_net) > 1000, "El archivo de red generado está vacío o corrupto"


@pytest.mark.skipif(shutil.which("sumo") is None, reason="sumo no está instalado en el PATH")
def test_pcn02_cn09_ejecucion_escenario_base_sumo():
    """
    PCN-02 / CN-09 - Válido: Ejecutar simulación base en SUMO.
    Entrada: scenarios/baseline.sumocfg (semáforo de tiempo fijo, 3600 s).
    Salida esperada: corre sin errores en SUMO y genera results/baseline_tripinfo.xml.
    """
    cfg_file = os.path.join(SCENARIOS_DIR, "baseline.sumocfg")
    tripinfo_file = os.path.join(RESULTS_DIR, "baseline_tripinfo.xml")

    # Ejecutar SUMO en modo headless
    cmd = ["sumo", "-c", cfg_file, "--no-step-log", "true"]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)

    assert res.returncode == 0, f"SUMO finalizó con error {res.returncode}: {res.stderr}"
    assert os.path.exists(tripinfo_file), "No se generó el archivo baseline_tripinfo.xml"
    assert os.path.getsize(tripinfo_file) > 1000, "El archivo tripinfo generado está vacío"


@pytest.mark.skipif(shutil.which("sumo") is None, reason="sumo no está instalado en el PATH")
def test_pcn02_cn12_ejecucion_configuracion_inexistente():
    """
    PCN-02 / CN-12 - Inválido: Ejecutar SUMO con archivo de configuración inexistente.
    Entrada: archivo 'no_existe.sumocfg'.
    Salida esperada: error claro de SUMO en consola, código != 0 y sin procesos colgados.
    """
    cmd = ["sumo", "-c", "no_existe_archivo.sumocfg"]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)

    assert res.returncode != 0, "SUMO debió fallar ante un archivo de configuración inexistente"
    assert ("Error" in res.stderr or "Error" in res.stdout or "not found" in res.stderr.lower() or "not found" in res.stdout.lower()), (
        "SUMO no emitió mensaje de error identificando el archivo faltante"
    )


def test_pcn04_cn26_generacion_grafica_comparativa():
    """
    PCN-04 / CN-26 - Válido: Generación automática de la gráfica comparativa.
    Salida esperada: el archivo results/comparacion.png existe, tiene formato PNG válido y tamaño > 0 bytes.
    """
    img_path = os.path.join(RESULTS_DIR, "comparacion.png")
    assert os.path.exists(img_path), "La gráfica comparacion.png no fue encontrada en results/"
    assert os.path.getsize(img_path) > 5000, "El archivo comparacion.png tiene un tamaño insuficiente"

    # Verificar cabecera mágica de archivo PNG (\x89PNG)
    with open(img_path, "rb") as f:
        header = f.read(4)
        assert header == b"\x89PNG", "El archivo generado no tiene cabecera válida de imagen PNG"
