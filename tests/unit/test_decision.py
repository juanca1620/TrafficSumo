import os
import sys

_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _sub in ["controller", "analysis", "tools", "."]:
    _p = os.path.join(_DIR, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

try:
    from controller.adaptive_controller import (
        decidir_accion,
        validar_parametros,
        GapOutTracker,
        PhaseSwitchTracker,
    )
except ImportError:
    from adaptive_controller import (  # pyright: ignore[reportMissingImports]
        decidir_accion,
        validar_parametros,
        GapOutTracker,
        PhaseSwitchTracker,
    )


def test_pu02_cp1_limite_inferior_no_cortar_antes_minimo():
    """
    CP1 - Límite inferior (min - 1): no cortar antes del verde mínimo.
    Entrada: t_verde = 9 s, seg_sin_deteccion = 5, hay_demanda_opuesta = True.
    Resultado esperado: 'EXTENDER'. El verde nunca se corta antes de 10 s (CU6).
    """
    accion = decidir_accion(t_verde=9, seg_sin_deteccion=5, hay_demanda_opuesta=True)
    assert accion == "EXTENDER"


def test_pu02_cp2_limite_inferior_cesion_en_minimo():
    """
    CP2 - Límite inferior (min): cesión permitida en el mínimo exacto.
    Entrada: t_verde = 10 s, seg_sin_deteccion = 3 (gap cumplido), hay_demanda_opuesta = True.
    Resultado esperado: 'CAMBIAR'.
    """
    accion = decidir_accion(t_verde=10, seg_sin_deteccion=3, hay_demanda_opuesta=True)
    assert accion == "CAMBIAR"


def test_pu02_cp3_extender_con_demanda_activa():
    """
    CP3 - Positivo: extender mientras hay demanda activa en el eje verde.
    Entrada: t_verde = 30 s, seg_sin_deteccion = 0, hay_demanda_opuesta = True.
    Resultado esperado: 'EXTENDER'.
    """
    accion = decidir_accion(t_verde=30, seg_sin_deteccion=0, hay_demanda_opuesta=True)
    assert accion == "EXTENDER"


def test_pu02_cp4_limite_superior_max_menos_uno():
    """
    CP4 - Límite superior (max - 1): aún puede extender a los 44 s.
    Entrada: t_verde = 44 s, seg_sin_deteccion = 0, hay_demanda_opuesta = True.
    Resultado esperado: 'EXTENDER'.
    """
    accion = decidir_accion(t_verde=44, seg_sin_deteccion=0, hay_demanda_opuesta=True)
    assert accion == "EXTENDER"


def test_pu02_cp5_limite_superior_corte_por_verde_maximo():
    """
    CP5 - Límite superior (max): corte forzoso por verde máximo.
    Entrada: t_verde = 45 s, seg_sin_deteccion = 0, hay_demanda_opuesta = True.
    Resultado esperado: 'CAMBIAR' (evita la inanición del eje opuesto).
    """
    accion = decidir_accion(t_verde=45, seg_sin_deteccion=0, hay_demanda_opuesta=True)
    assert accion == "CAMBIAR"


def test_pu02_cp6_negativo_nunca_superar_maximo():
    """
    CP6 - Negativo: nunca superar el máximo (46 s).
    Entrada: t_verde = 46 s, seg_sin_deteccion = 0, hay_demanda_opuesta = True.
    Resultado esperado: 'CAMBIAR'.
    """
    accion = decidir_accion(t_verde=46, seg_sin_deteccion=0, hay_demanda_opuesta=True)
    assert accion == "CAMBIAR"


def test_pu02_cp7_gap_out_ceder_al_eje_opuesto():
    """
    CP7 - Gap-out: ceder el paso al eje opuesto tras intervalo sin detección.
    Entrada A: t_verde = 20 s, seg_sin_deteccion = 3, hay_demanda_opuesta = True -> 'CAMBIAR'.
    Entrada B: t_verde = 20 s, seg_sin_deteccion = 2, hay_demanda_opuesta = True -> 'EXTENDER'.
    """
    accion_a = decidir_accion(t_verde=20, seg_sin_deteccion=3, hay_demanda_opuesta=True)
    assert accion_a == "CAMBIAR"

    accion_b = decidir_accion(t_verde=20, seg_sin_deteccion=2, hay_demanda_opuesta=True)
    assert accion_b == "EXTENDER"


def test_pu02_cp8_ambos_ejes_sin_demanda():
    """
    CP8 - Ambos ejes sin demanda.
    Entrada: t_verde = 20 s, seg_sin_deteccion = 5, hay_demanda_opuesta = False.
    Resultado esperado: 'EXTENDER' (no generar un cambio de fase innecesario).
    """
    accion = decidir_accion(t_verde=20, seg_sin_deteccion=5, hay_demanda_opuesta=False)
    assert accion == "EXTENDER"


def test_pu02_cp9_contador_gap_out():
    """
    CP9 - Contador de gap-out.
    Acción: se simulan 4 pasos consecutivos sin detección y luego un paso con detección.
    Resultado esperado: el contador pasa de 0 a 4 y se reinicia a 0 cuando se detecta un vehículo.
    """
    tracker = GapOutTracker()
    assert tracker.seg_sin_deteccion == 0
    for esperado in range(1, 5):
        assert tracker.step(hay_vehiculo=False) == esperado
    assert tracker.step(hay_vehiculo=True) == 0


def test_pu02_cp10_contador_cambios_de_fase():
    """
    CP10 - Contador de cambios de fase (RU008).
    Acción: se registra el contador inicial y se ejecutan 3 cambios de fase.
    Resultado esperado: el contador inicia en 0 y termina en 3.
    """
    sw = PhaseSwitchTracker()
    assert sw.switches == 0
    sw.register_switch()
    sw.register_switch()
    assert sw.register_switch() == 3


def test_pu02_cp11_validacion_parametros():
    """
    CP11 - Validación de parámetros de configuración semafórica.
    Entrada válida: (10, 45, 3) -> True.
    Entradas inválidas: (50, 45, 3) [min > max], (10, 45, 0) [gap <= 0], (-5, 45, 3) [min < 0]
    deben lanzar ValueError con mensaje descriptivo.
    """
    assert validar_parametros(10, 45, 3) is True

    with pytest.raises(ValueError, match="no puede superar al verde máximo"):
        validar_parametros(50, 45, 3)

    with pytest.raises(ValueError, match="mayor a 0"):
        validar_parametros(10, 45, 0)

    with pytest.raises(ValueError, match="no puede ser negativo"):
        validar_parametros(-5, 45, 3)
