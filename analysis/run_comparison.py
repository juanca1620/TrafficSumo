"""
Corre el escenario base (semaforo fijo) y el adaptativo (TraCI + sensores),
extrae metricas de results/*_tripinfo.xml y genera una grafica comparativa
para el informe / sustentacion.

Uso:
    cd traffic_sumo
    python analysis/run_comparison.py
"""
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _sub in ["", "controller", "analysis", "tools"]:
    _p = os.path.join(ROOT, _sub) if _sub else ROOT
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from controller import adaptive_controller  # type: ignore[import-not-found]
except ImportError:
    import adaptive_controller  # type: ignore[import-not-found, no-redef]


def run_baseline():
    try:
        subprocess.run(
            ["sumo", "-c", os.path.join(ROOT, "scenarios", "baseline.sumocfg"), "--no-step-log", "true"],
            cwd=ROOT,
            check=True,
        )
    except Exception as exc:
        fallback = os.path.join(ROOT, "results", "baseline_tripinfo.xml")
        if not os.path.exists(fallback):
            raise
        print(f"Aviso: usando resultados previos en {fallback} ({exc})")


def run_adaptive():
    prev_cwd = os.getcwd()
    try:
        os.chdir(ROOT)
        adaptive_controller.run(num_retries=2)
    except Exception as exc:
        fallback = os.path.join(ROOT, "results", "adaptive_tripinfo.xml")
        if not os.path.exists(fallback):
            raise
        print(f"Aviso: usando resultados previos en {fallback} ({exc})")
    finally:
        os.chdir(prev_cwd)


def parse_tripinfo(path: str) -> dict[str, float | int]:
    """
    Parsea un archivo tripinfo XML de SUMO y calcula métricas clave:
    n (vehículos completados), avg_wait (espera promedio), avg_timeloss (pérdida de tiempo promedio).
    (Requerimiento CU7, RU009 - Formato PU-03)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo de resultados no encontrado: {path}")

    tree = ET.parse(path)
    trips = tree.getroot().findall("tripinfo")
    if not trips:
        return {"n": 0, "avg_wait": 0.0, "max_wait": 0.0, "avg_timeloss": 0.0}

    waits = [float(t.get("waitingTime") or 0.0) for t in trips]
    timeloss = [float(t.get("timeLoss") or 0.0) for t in trips]
    return {
        "n": len(waits),
        "avg_wait": sum(waits) / len(waits),
        "max_wait": max(waits),
        "avg_timeloss": sum(timeloss) / len(timeloss),
    }


def stats(path: str) -> dict[str, float | int]:
    """Alias compatible hacia atrás para parse_tripinfo."""
    return parse_tripinfo(path)


def calcular_mejora(base: float, adaptativo: float) -> float:
    """
    Calcula el porcentaje de reducción (mejora) respecto a la línea base.
    Fórmula: ((base - adaptativo) / base) * 100
    (Requerimiento CU7, RU010 - Formato PU-03)
    """
    if base == 0:
        return 0.0
    return ((base - adaptativo) / base) * 100.0


def generar_grafica(base: dict[str, float | int], adap: dict[str, float | int], out_path: str) -> str:
    """
    Genera el gráfico de barras comparativo y lo guarda en disco.
    (Requerimiento CU7, RU011 - Formato PU-03)
    """
    labels = ["Espera promedio (s)", "Perdida de tiempo prom. (s)"]
    base_vals = [float(base["avg_wait"]), float(base["avg_timeloss"])]
    adap_vals = [float(adap["avg_wait"]), float(adap["avg_timeloss"])]

    x = list(range(len(labels)))
    width = 0.35
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar([i - width / 2 for i in x], base_vals, width, label="Semaforo fijo", color="#8a8a8a")
    ax.bar([i + width / 2 for i in x], adap_vals, width, label="Adaptativo (IoT + TraCI)", color="#2e7d32")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Segundos")
    ax.set_title("Semaforo fijo vs. adaptativo (interseccion critica, hora pico)")
    ax.legend()
    for i, v in enumerate(base_vals):
        ax.text(i - width / 2, v + 0.3, f"{v:.1f}", ha="center")
    for i, v in enumerate(adap_vals):
        ax.text(i + width / 2, v + 0.3, f"{v:.1f}", ha="center")
    fig.tight_layout()
    out_dir = os.path.dirname(os.path.abspath(out_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def imprimir_resumen(base: dict[str, float | int], adap: dict[str, float | int]) -> dict[str, float]:
    """
    Imprime en salida estándar el resumen comparativo de métricas y los porcentajes de mejora.
    (Requerimiento CU7, RU009, RU010 - Formato PU-03 CP10)
    """
    mejora_espera = calcular_mejora(float(base["avg_wait"]), float(adap["avg_wait"]))
    mejora_timeloss = calcular_mejora(float(base["avg_timeloss"]), float(adap["avg_timeloss"]))
    print("\n=== RESULTADOS ===")
    print(
        f"Base:       espera prom {float(base['avg_wait']):.1f}s | "
        f"timeLoss prom {float(base['avg_timeloss']):.1f}s | vehiculos {base['n']}"
    )
    print(
        f"Adaptativo: espera prom {float(adap['avg_wait']):.1f}s | "
        f"timeLoss prom {float(adap['avg_timeloss']):.1f}s | vehiculos {adap['n']}"
    )
    print(f"Reduccion espera promedio: {mejora_espera:.1f}%")
    print(f"Reduccion perdida de tiempo: {mejora_timeloss:.1f}%")
    return {"mejora_espera": mejora_espera, "mejora_timeloss": mejora_timeloss}


def main():
    print("Corriendo escenario base (semaforo fijo)...")
    run_baseline()
    print("Corriendo escenario adaptativo (TraCI + sensores IoT)...")
    run_adaptive()

    base = parse_tripinfo(os.path.join(ROOT, "results", "baseline_tripinfo.xml"))
    adap = parse_tripinfo(os.path.join(ROOT, "results", "adaptive_tripinfo.xml"))

    imprimir_resumen(base, adap)

    out_path = os.path.join(ROOT, "results", "comparacion.png")
    generar_grafica(base, adap, out_path)
    print(f"\nGrafica guardada en: {out_path}")


if __name__ == "__main__":
    main()
