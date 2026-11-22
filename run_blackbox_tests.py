"""
Ejecutor de las Pruebas de Caja Negra del Plan de Pruebas.
Ejecuta pytest sobre tests/blackbox/ y presenta un resumen ejecutivo
con el estado de validación externa (netconvert, SUMO, TraCI y gráficas).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    print("=" * 72)
    print(" EJECUCIÓN DE PRUEBAS DE CAJA NEGRA - PLAN DE PRUEBAS (EAM)")
    print("=" * 72)
    print("Formatos evaluados: PCN-01, PCN-02, PCN-03, PCN-04")
    print("Directorio de pruebas: tests/blackbox/\n")

    cmd = [sys.executable, "-m", "pytest", "tests/blackbox/test_caja_negra.py", "-v", "--tb=short"]
    result = subprocess.run(cmd, cwd=ROOT)

    print("\n" + "=" * 72)
    print(" RESUMEN EJECUTIVO DE CAJA NEGRA (BLACK-BOX TESTING)")
    print("=" * 72)
    print("- Módulos validados externamente:")
    print("  1. PCN-01 (CN-01): Compilación de red vial con netconvert (4 accesos, 2 carriles).")
    print("  2. PCN-02 (CN-09): Simulación base en SUMO (3600 s, baseline_tripinfo.xml).")
    print("  3. PCN-02 (CN-12): Manejo controlado de configuración inexistente en SUMO.")
    print("  4. PCN-04 (CN-26): Generación y validación de gráfica comparacion.png.")
    print(f"- Estado global de ejecución: {'EXITOSO (100% PASSED)' if result.returncode == 0 else 'CON FALLOS'}")
    print("=" * 72)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
