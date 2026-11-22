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
    from analysis.run_comparison import parse_tripinfo, calcular_mejora, generar_grafica, imprimir_resumen
except ImportError:
    from run_comparison import (  # pyright: ignore[reportMissingImports]
        parse_tripinfo,
        calcular_mejora,
        generar_grafica,
        imprimir_resumen,
    )


def test_pu03_cp1_promedios_tripinfo_valido(tmp_path):
    """
    CP1 - Positivo: promedios correctos de un tripinfo válido.
    Preparación: archivo XML sintético con 3 viajes (espera: 10, 20, 30; pérdida: 15, 25, 35).
    Resultado esperado: avg_wait = 20.0, avg_timeloss = 25.0, n = 3.
    """
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <tripinfos>
        <tripinfo id="car1" waitingTime="10.0" timeLoss="15.0"/>
        <tripinfo id="car2" waitingTime="20.0" timeLoss="25.0"/>
        <tripinfo id="car3" waitingTime="30.0" timeLoss="35.0"/>
    </tripinfos>
    """
    test_file = tmp_path / "test_tripinfo.xml"
    test_file.write_text(xml_content, encoding="utf-8")

    res = parse_tripinfo(str(test_file))
    assert res["n"] == 3
    assert res["avg_wait"] == pytest.approx(20.0, 0.1)
    assert res["avg_timeloss"] == pytest.approx(25.0, 0.1)


def test_pu03_cp2_limite_tripinfo_sin_viajes(tmp_path):
    """
    CP2 - Límite: tripinfo sin viajes.
    Preparación: XML válido sin elementos <tripinfo>.
    Resultado esperado: retorna 0 vehículos y promedios 0.0 sin ZeroDivisionError.
    """
    xml_content = '<?xml version="1.0" encoding="UTF-8"?><tripinfos></tripinfos>'
    test_file = tmp_path / "empty_tripinfo.xml"
    test_file.write_text(xml_content, encoding="utf-8")

    res = parse_tripinfo(str(test_file))
    assert res["n"] == 0
    assert res["avg_wait"] == 0.0
    assert res["avg_timeloss"] == 0.0


def test_pu03_cp3_archivo_tripinfo_inexistente(tmp_path):
    """
    CP3 - Negativo: archivo de resultados inexistente.
    Acción: parse_tripinfo() con ruta inexistente.
    Resultado esperado: lanza FileNotFoundError con mensaje claro.
    """
    ruta_invalida = str(tmp_path / "archivo_no_existente.xml")
    with pytest.raises(FileNotFoundError):
        parse_tripinfo(ruta_invalida)


def test_pu03_cp4_negativo_xml_mal_formado(tmp_path):
    """
    CP4 - Negativo: XML mal formado.
    Preparación: archivo con etiqueta sin cerrar.
    Resultado esperado: lanza ET.ParseError controlado.
    """
    bad_file = tmp_path / "malformado.xml"
    bad_file.write_text("<tripinfos><tripinfo id='1' waitingTime='10.0'>", encoding="utf-8")
    with pytest.raises(ET.ParseError):
        parse_tripinfo(str(bad_file))


def test_pu03_cp5_porcentaje_mejora_espera():
    """
    CP5 - Positivo: cálculo de mejora en tiempo de espera promedio.
    Entrada: base = 100 s, adaptativo = 49.2 s.
    Resultado esperado: mejora = 50.8%.
    """
    mejora = calcular_mejora(base=100.0, adaptativo=49.2)
    assert mejora == pytest.approx(50.8, 0.1)


def test_pu03_cp6_mejora_perdida_de_tiempo():
    """
    CP6 - Positivo: mejora en pérdida de tiempo.
    Entrada: base = 100 s, adaptativo = 62.9 s.
    Resultado esperado: mejora = 37.1%.
    """
    mejora = calcular_mejora(base=100.0, adaptativo=62.9)
    assert mejora == pytest.approx(37.1, 0.1)


def test_pu03_cp7_negativo_adaptativo_empeora():
    """
    CP7 - Negativo: el adaptativo empeora respecto al base.
    Entrada: base = 50 s, adaptativo = 60 s.
    Resultado esperado: resultado negativo (-20.0%).
    """
    mejora = calcular_mejora(base=50.0, adaptativo=60.0)
    assert mejora == pytest.approx(-20.0, 0.1)


def test_pu03_cp8_limite_base_igual_a_cero():
    """
    CP8 - Límite: escenario base con espera igual a cero.
    Entrada: base = 0 s, adaptativo = 10 s.
    Resultado esperado: se maneja sin ZeroDivisionError retornando 0.0.
    """
    resultado = calcular_mejora(base=0.0, adaptativo=10.0)
    assert isinstance(resultado, float)
    assert resultado == 0.0


def test_pu03_cp9_generacion_de_grafica(tmp_path):
    """
    CP9 - Positivo: generación de la gráfica comparativa.
    Acción: generar_grafica() con valores de ambos escenarios y ruta en carpeta temporal.
    Resultado esperado: el archivo comparacion.png existe y su tamaño es mayor que 0 bytes.
    """
    base_stats = {"n": 1918, "avg_wait": 12.1, "avg_timeloss": 19.1}
    adap_stats = {"n": 1923, "avg_wait": 5.9, "avg_timeloss": 12.0}
    out_img = tmp_path / "comparacion.png"
    generar_grafica(base_stats, adap_stats, str(out_img))
    assert out_img.exists()
    assert out_img.stat().st_size > 0


def test_pu03_cp10_impresion_porcentaje_mejora(capsys):
    """
    CP10 - Positivo: impresión del porcentaje de mejora en salida estándar (CU7).
    Acción: se ejecuta la función que imprime el resumen (imprimir_resumen) con capsys.
    Resultado esperado: la salida estándar contiene el porcentaje de mejora calculado.
    """
    base_stats = {"n": 1918, "avg_wait": 100.0, "avg_timeloss": 100.0}
    adap_stats = {"n": 1923, "avg_wait": 49.2, "avg_timeloss": 62.9}
    imprimir_resumen(base_stats, adap_stats)
    captured = capsys.readouterr()
    assert "50.8%" in captured.out
    assert "37.1%" in captured.out
