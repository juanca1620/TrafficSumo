import os
import sys

# Asegurar que el entorno resuelva las carpetas del proyecto
_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _sub in ["controller", "analysis", "tools", "."]:
    _p = os.path.join(_DIR, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest
from unittest.mock import patch, MagicMock
import traci

try:
    from controller.adaptive_controller import (
        leer_detectores_eje,
        DETECTOR_MAP,
        NS_DETECTORS,
        EW_DETECTORS,
    )
except ImportError:
    from adaptive_controller import (  # pyright: ignore[reportMissingImports]
        leer_detectores_eje,
        DETECTOR_MAP,
        NS_DETECTORS,
        EW_DETECTORS,
    )


def test_pu01_cp1_vehiculos_ambos_ejes():
    """
    CP1 - Positivo: vehículos en ambos ejes.
    El mock devuelve 3 y 2 vehículos en NS (suma 5), y 1 y 0 en EW (suma 1).
    Resultado esperado: {'NS': 5, 'EW': 1}.
    """
    mapping = {
        "det_N2C_0": 3,
        "det_N2C_1": 2,
        "det_S2C_0": 0,
        "det_S2C_1": 0,
        "det_E2C_0": 1,
        "det_E2C_1": 0,
        "det_W2C_0": 0,
        "det_W2C_1": 0,
    }

    def fake_get_vehicles(det_id):
        return mapping.get(det_id, 0)

    with patch("traci.inductionloop.getLastStepVehicleNumber", side_effect=fake_get_vehicles):
        resultado = leer_detectores_eje()
        assert resultado == {"NS": 5, "EW": 1}, f"Se esperaba {{'NS': 5, 'EW': 1}}, obtenido {resultado}"


def test_pu01_cp2_sin_vehiculos():
    """
    CP2 - Positivo: sin vehículos en ningún acceso.
    El mock devuelve 0 para todos los detectores.
    Resultado esperado: {'NS': 0, 'EW': 0} sin excepciones.
    """
    with patch("traci.inductionloop.getLastStepVehicleNumber", return_value=0):
        resultado = leer_detectores_eje()
        assert resultado == {"NS": 0, "EW": 0}


def test_pu01_cp3_consulta_todos_detectores():
    """
    CP3 - Positivo: consulta de todos los detectores en cada paso.
    Se invoca la función una vez y se verifica que cada detector configurado
    sea consultado exactamente una vez (call_count == 8).
    """
    total_esperado = len(NS_DETECTORS) + len(EW_DETECTORS)
    with patch("traci.inductionloop.getLastStepVehicleNumber", return_value=0) as mock_loop:
        leer_detectores_eje()
        assert mock_loop.call_count == total_esperado, (
            f"Se esperaba {total_esperado} llamadas a TraCI, pero se realizaron {mock_loop.call_count}"
        )


def test_pu01_cp4_error_traci_detector_inexistente():
    """
    CP4 - Negativo: detector inexistente o error de TraCI.
    Preparación: el mock lanza TraCIException para simular fallo de sensor.
    Resultado esperado: la función debe propagar o lanzar la excepción controlada
    y no devolver conteos parciales silenciosos (assertRaises).
    
    [FALLA DIDÁCTICA ESPERADA]:
    El controlador actual silencia la excepción con un bloque pass, retornando
    un conteo parcial engañoso en lugar de alertar el fallo.
    """
    with patch("traci.inductionloop.getLastStepVehicleNumber", side_effect=traci.TraCIException("Detector inexistente")):
        with pytest.raises(traci.TraCIException):
            leer_detectores_eje()


def test_pu01_cp5_limite_conteo_alto_sin_truncar():
    """
    CP5 - Límite: conteo alto en un detector (50 vehículos).
    Preparación: mock devuelve 50 en un detector de NS y 0 en el resto.
    Resultado esperado: {'NS': 50, 'EW': 0}; el valor no se trunca ni se satura.
    """
    def fake_high(det_id):
        return 50 if det_id == "det_N2C_0" else 0

    with patch("traci.inductionloop.getLastStepVehicleNumber", side_effect=fake_high):
        resultado = leer_detectores_eje()
        assert resultado == {"NS": 50, "EW": 0}
