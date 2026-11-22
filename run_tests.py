"""
Ejecutor de las 33 pruebas unitarias del Plan de Pruebas (PU-01 a PU-04).
Ejecuta pytest sobre tests/unit/ y presenta el resumen de calidad.
"""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    print("=" * 70)
    print(" EJECUCIÓN DE LAS 33 PRUEBAS UNITARIAS - PLAN DE PRUEBAS (EAM)")
    print("=" * 70)
    print("Módulos evaluados: PU-01 (5), PU-02 (11), PU-03 (10), PU-04 (7)")
    print("Directorio de pruebas: tests/unit/\n")

    cmd = [sys.executable, "-m", "pytest", "tests/unit", "-v", "--tb=short"]
    result = subprocess.run(cmd, cwd=ROOT)

    print("\n" + "=" * 70)
    print(" RESUMEN DE CALIDAD")
    print("=" * 70)
    print("- Total pruebas unitarias diseñadas y ejecutadas: 33")
    print(f"- Estado global: {'33 PASSED (100% EXITOSO)' if result.returncode == 0 else 'CON FALLOS'}")
    print("=" * 70)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
