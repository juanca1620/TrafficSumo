"""
Controlador adaptativo de semaforizacion basado en sensores IoT virtuales.

Logica:
  - Los detectores E1 (uno por carril de entrada) simulan los sensores IoT
    reales que reportarian flujo vehicular en tiempo real.
  - Cada segundo simulado, el controlador revisa cuantos vehiculos hay
    "en cola" (esperando o pasando) en el acceso que tiene luz verde y en
    el acceso opuesto (rojo).
  - Se respeta un verde minimo (evita cortes injustos) y un verde maximo
    (evita inanicion del otro eje).
  - Si el acceso en verde deja de tener demanda ("gap-out") y el acceso en
    rojo SI tiene vehiculos esperando, se corta el verde (una vez cumplido
    el minimo) y se cede el paso.
  - Si el acceso en verde sigue con demanda, se extiende el verde hasta el
    maximo permitido.

Esto emula el objetivo especifico 3 del proyecto: "ajustes en la
sincronizacion semaforica" a partir de datos de sensores IoT en tiempo real.
"""
import os
import sys

if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

import traci  # type: ignore[import-untyped]  # noqa: E402

TLS_ID = "C"

# Indices de fase segun el tlLogic generado por netconvert
PHASE_NS_GREEN = 0
PHASE_NS_YELLOW = 1
PHASE_EW_GREEN = 2
PHASE_EW_YELLOW = 3

MIN_GREEN = 10       # segundos minimos de verde (seguridad / evita cortes injustos)
MAX_GREEN = 45       # segundos maximos de verde (evita inanicion del otro eje)
YELLOW_DURATION = 3  # segundos de amarillo (igual que el programa original)
GAP_OUT = 3          # segundos sin deteccion de vehiculos para considerar "sin demanda"

NS_DETECTORS = ["det_N2C_0", "det_N2C_1", "det_S2C_0", "det_S2C_1"]
EW_DETECTORS = ["det_E2C_0", "det_E2C_1", "det_W2C_0", "det_W2C_1"]

DETECTOR_MAP = {
    "NS": NS_DETECTORS,
    "EW": EW_DETECTORS,
}

SIM_END = 3600


def queued_vehicles(detector_ids):
    """Suma de vehiculos detectados en el ultimo paso en un grupo de sensores."""
    return sum(traci.inductionloop.getLastStepVehicleNumber(d) for d in detector_ids)


def leer_detectores_eje(detector_map=None):
    """
    Lee los detectores E1 simulados agrupados por eje (NS y EW).
    (Requerimiento CU5, RU005 - Formato PU-01)
    """
    if detector_map is None:
        detector_map = DETECTOR_MAP

    conteo = {}
    for eje, det_list in detector_map.items():
        total = 0
        for d in det_list:
            try:
                total += traci.inductionloop.getLastStepVehicleNumber(d)
            except traci.TraCIException:
                raise
        conteo[eje] = total
    return conteo


def decidir_accion(t_verde, seg_sin_deteccion, hay_demanda_opuesta, params=None):
    """
    Determina si la fase en verde actual se extiende o cambia.
    Retorna 'EXTENDER' o 'CAMBIAR'.
    (Requerimiento CU6, RU006, RU007 - Formato PU-02)
    """
    if params is None:
        params = {"min_green": MIN_GREEN, "max_green": MAX_GREEN, "gap_out": GAP_OUT}

    min_g = params.get("min_green", MIN_GREEN)
    max_g = params.get("max_green", MAX_GREEN)
    gap_o = params.get("gap_out", GAP_OUT)

    # Regla 1: Nunca cortar antes del verde minimo
    if t_verde < min_g:
        return "EXTENDER"

    # Regla 4: Corte forzoso al alcanzar o superar el verde maximo
    if t_verde >= max_g:
        return "CAMBIAR"

    # Regla 3 y 5: Ceder por gap-out solo si hay demanda en el eje opuesto
    if seg_sin_deteccion >= gap_o and hay_demanda_opuesta:
        return "CAMBIAR"

    return "EXTENDER"


def validar_parametros(min_green, max_green, gap_out):
    """
    Valida los limites y consistencia de los parametros semaforicos.
    (Requerimiento CU6, RU006 - Formato PU-02)
    """
    if min_green < 0:
        raise ValueError("El verde mínimo no puede ser negativo.")
    if min_green > max_green:
        raise ValueError("El verde mínimo no puede superar al verde máximo.")
    if gap_out <= 0:
        raise ValueError("El tiempo de gap-out debe ser mayor a 0.")
    return True


class GapOutTracker:
    """Rastreador de segundos consecutivos sin deteccion de vehiculos."""
    def __init__(self):
        self.seg_sin_deteccion = 0

    def step(self, hay_vehiculo: bool):
        if hay_vehiculo:
            self.seg_sin_deteccion = 0
        else:
            self.seg_sin_deteccion += 1
        return self.seg_sin_deteccion


class PhaseSwitchTracker:
    """Contador de cambios de fase realizados por el controlador adaptativo."""
    def __init__(self):
        self.switches = 0

    def register_switch(self):
        self.switches += 1
        return self.switches


def run(
    num_retries: int = 10,
    min_green: int = MIN_GREEN,
    max_green: int = MAX_GREEN,
    gap_out: int = GAP_OUT,
    use_gui: bool = False,
    config_path: str = "scenarios/adaptive.sumocfg",
):
    """
    Ejecuta la simulación adaptativa en SUMO conectando vía TraCI y aplicando
    las funciones validadas en el Plan de Pruebas Unitarias (PU-01 y PU-02):
      - validar_parametros()
      - leer_detectores_eje()
      - decidir_accion()
      - GapOutTracker y PhaseSwitchTracker
    """
    validar_parametros(min_green, max_green, gap_out)
    params = {"min_green": min_green, "max_green": max_green, "gap_out": gap_out}

    sumo_binary = "sumo-gui" if use_gui else "sumo"
    traci.start([sumo_binary, "-c", config_path, "--no-step-log", "true"], numRetries=num_retries)

    current_phase = PHASE_NS_GREEN
    traci.trafficlight.setPhase(TLS_ID, current_phase)
    traci.trafficlight.setPhaseDuration(TLS_ID, 9999)

    phase_timer = 0
    gap_tracker = GapOutTracker()
    switch_tracker = PhaseSwitchTracker()

    step = 0
    while step < SIM_END:
        traci.simulationStep()
        step += 1
        phase_timer += 1

        if current_phase in (PHASE_NS_GREEN, PHASE_EW_GREEN):
            conteos = leer_detectores_eje()
            if current_phase == PHASE_NS_GREEN:
                active_count, other_count = conteos["NS"], conteos["EW"]
            else:
                active_count, other_count = conteos["EW"], conteos["NS"]

            seg_sin_det = gap_tracker.step(hay_vehiculo=(active_count > 0))
            accion = decidir_accion(
                t_verde=phase_timer,
                seg_sin_deteccion=seg_sin_det,
                hay_demanda_opuesta=(other_count > 0),
                params=params,
            )

            if accion == "CAMBIAR":
                next_phase = PHASE_NS_YELLOW if current_phase == PHASE_NS_GREEN else PHASE_EW_YELLOW
                traci.trafficlight.setPhase(TLS_ID, next_phase)
                traci.trafficlight.setPhaseDuration(TLS_ID, YELLOW_DURATION)
                current_phase = next_phase
                phase_timer = 0
                switch_tracker.register_switch()
        else:
            # Fase amarilla: duración fija, luego pasa al verde del eje opuesto
            if phase_timer >= YELLOW_DURATION:
                next_phase = PHASE_EW_GREEN if current_phase == PHASE_NS_YELLOW else PHASE_NS_GREEN
                traci.trafficlight.setPhase(TLS_ID, next_phase)
                traci.trafficlight.setPhaseDuration(TLS_ID, 9999)
                current_phase = next_phase
                phase_timer = 0
                gap_tracker = GapOutTracker()

    traci.close()
    print(f"Simulacion adaptativa terminada. Cambios de fase realizados: {switch_tracker.switches}")
    return switch_tracker.switches


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Controlador adaptativo SGT (SUMO + TraCI)")
    parser.add_argument("--min-green", type=int, default=MIN_GREEN, help="Tiempo mínimo de verde (s)")
    parser.add_argument("--max-green", type=int, default=MAX_GREEN, help="Tiempo máximo de verde (s)")
    parser.add_argument("--gap-out", type=int, default=GAP_OUT, help="Umbral de gap-out sin detección (s)")
    parser.add_argument("--gui", action="store_true", help="Ejecutar con interfaz gráfica sumo-gui")
    parser.add_argument("--config", type=str, default="scenarios/adaptive.sumocfg", help="Ruta al archivo .sumocfg")
    args = parser.parse_args()

    run(
        min_green=args.min_green,
        max_green=args.max_green,
        gap_out=args.gap_out,
        use_gui=args.gui,
        config_path=args.config,
    )
