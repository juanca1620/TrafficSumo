import os
import sys
import xml.etree.ElementTree as ET

_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _sub in ["controller", "analysis", "tools", "."]:
    _p = os.path.join(_DIR, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

try:
    from tools.validar_config import validar_red, validar_demanda
except ImportError:
    from validar_config import validar_red, validar_demanda  # pyright: ignore[reportMissingImports]


def test_pu04_cp1_red_valida_4_accesos_2_carriles(tmp_path):
    """
    CP1 - Positivo: red vial válida.
    Preparación: net.xml con 4 accesos de entrada (N2C, S2C, E2C, W2C),
    cada uno con 2 carriles (numLanes=2).
    Resultado esperado: validar_red() retorna (True, ...).
    """
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <net version="1.20">
        <edge id="N2C" from="N" to="C" numLanes="2">
            <lane id="N2C_0" length="300.0"/>
            <lane id="N2C_1" length="300.0"/>
        </edge>
        <edge id="S2C" from="S" to="C" numLanes="2">
            <lane id="S2C_0" length="300.0"/>
            <lane id="S2C_1" length="300.0"/>
        </edge>
        <edge id="E2C" from="E" to="C" numLanes="2">
            <lane id="E2C_0" length="300.0"/>
            <lane id="E2C_1" length="300.0"/>
        </edge>
        <edge id="W2C" from="W" to="C" numLanes="2">
            <lane id="W2C_0" length="300.0"/>
            <lane id="W2C_1" length="300.0"/>
        </edge>
    </net>
    """
    net_file = tmp_path / "valida.net.xml"
    net_file.write_text(xml_content, encoding="utf-8")

    es_valido, mensaje = validar_red(str(net_file))
    assert es_valido is True
    assert "válida" in mensaje.lower()


def test_pu04_cp2_limite_acceso_con_un_carril(tmp_path):
    """
    CP2 - Límite: un acceso con solo 1 carril.
    Preparación: net.xml donde el acceso E2C tiene numLanes = 1.
    Resultado esperado: validar_red() retorna (False, ...) e identifica el acceso E2C incumplido.
    """
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <net version="1.20">
        <edge id="N2C" from="N" to="C" numLanes="2"/>
        <edge id="S2C" from="S" to="C" numLanes="2"/>
        <edge id="E2C" from="E" to="C" numLanes="1"/>
        <edge id="W2C" from="W" to="C" numLanes="2"/>
    </net>
    """
    net_file = tmp_path / "invalida_carril.net.xml"
    net_file.write_text(xml_content, encoding="utf-8")

    es_valido, mensaje = validar_red(str(net_file))
    assert es_valido is False
    assert "E2C" in mensaje
    assert "al menos 2 carriles" in mensaje


def test_pu04_cp3_negativo_red_con_solo_3_accesos(tmp_path):
    """
    CP3 - Negativo: red con solo 3 accesos (falta W2C).
    Resultado esperado: validar_red() retorna (False, ...) indicando que no tiene 4 accesos.
    """
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <net version="1.20">
        <edge id="N2C" from="N" to="C" numLanes="2"/>
        <edge id="S2C" from="S" to="C" numLanes="2"/>
        <edge id="E2C" from="E" to="C" numLanes="2"/>
    </net>
    """
    net_file = tmp_path / "incompleta.net.xml"
    net_file.write_text(xml_content, encoding="utf-8")

    es_valido, mensaje = validar_red(str(net_file))
    assert es_valido is False
    assert "4 accesos" in mensaje


def test_pu04_cp4_demanda_valida_predominio_ns(tmp_path):
    """
    CP4 - Positivo: demanda vehicular válida.
    Preparación: routes.rou.xml con flujos NS = 1200 veh/h y EW = 600 veh/h.
    Resultado esperado: validar_demanda() retorna (True, ...) y confirma NS > EW.
    """
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <routes>
        <flow id="f_NS" route="r_NS" begin="0" end="3600" vehsPerHour="1200"/>
        <flow id="f_EW" route="r_EW" begin="0" end="3600" vehsPerHour="600"/>
    </routes>
    """
    rou_file = tmp_path / "valida.rou.xml"
    rou_file.write_text(xml_content, encoding="utf-8")

    es_valido, mensaje = validar_demanda(str(rou_file))
    assert es_valido is True
    assert "Demanda válida" in mensaje


def test_pu04_cp5_demanda_ns_menor_o_igual_ew(tmp_path):
    """
    CP5 - Negativo: demanda vehicular con NS menor o igual que EW.
    Preparación: flujos con NS = 500 veh/h y EW = 600 veh/h.
    Resultado esperado: validar_demanda() retorna (False, ...) y reporta incumplimiento del criterio CU3.
    """
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <routes>
        <flow id="f_NS" route="r_NS" begin="0" end="3600" vehsPerHour="500"/>
        <flow id="f_EW" route="r_EW" begin="0" end="3600" vehsPerHour="600"/>
    </routes>
    """
    rou_file = tmp_path / "invalida_flujos.rou.xml"
    rou_file.write_text(xml_content, encoding="utf-8")

    es_valido, mensaje = validar_demanda(str(rou_file))
    assert es_valido is False
    assert "Incumplimiento del criterio CU3" in mensaje


def test_pu04_cp6_negativo_valor_invalido_flujo(tmp_path):
    """
    CP6 - Negativo: flujo con vehsPerHour negativo (-100) o texto no numérico ('abc').
    Resultado esperado: lanza ValueError con mensaje descriptivo.
    """
    neg_file = tmp_path / "negativo.rou.xml"
    neg_file.write_text('<routes><flow id="f_NS" route="r_NS" vehsPerHour="-100"/></routes>', encoding="utf-8")
    with pytest.raises(ValueError, match="negativo"):
        validar_demanda(str(neg_file))

    abc_file = tmp_path / "texto.rou.xml"
    abc_file.write_text('<routes><flow id="f_NS" route="r_NS" vehsPerHour="abc"/></routes>', encoding="utf-8")
    with pytest.raises(ValueError, match="no numérico"):
        validar_demanda(str(abc_file))


def test_pu04_cp7_negativo_archivo_inexistente_o_mal_formado(tmp_path):
    """
    CP7 - Negativo: archivo inexistente o XML mal formado.
    Resultado esperado: lanza FileNotFoundError y ET.ParseError respectivamente.
    """
    with pytest.raises(FileNotFoundError):
        validar_red(str(tmp_path / "no_existe.net.xml"))

    with pytest.raises(FileNotFoundError):
        validar_demanda(str(tmp_path / "no_existe.rou.xml"))

    bad_xml = tmp_path / "corrupto.net.xml"
    bad_xml.write_text("<net><edge id='N2C'>", encoding="utf-8")
    with pytest.raises(ET.ParseError):
        validar_red(str(bad_xml))

    bad_rou = tmp_path / "corrupto.rou.xml"
    bad_rou.write_text("<routes><flow id='f_NS' vehsPerHour='1200'>", encoding="utf-8")
    with pytest.raises(ET.ParseError):
        validar_demanda(str(bad_rou))
